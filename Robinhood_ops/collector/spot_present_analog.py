#!/usr/bin/env python3
import argparse
import json
import math
import sqlite3
import time
import urllib.parse
import urllib.request
from pathlib import Path

REST_URLS = {
    "mainnet": "https://api.arcus.xyz",
    "testnet": "https://api.testnet.arcus.xyz",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS spot_present_analog_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  ticker TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  horizon_minutes INTEGER NOT NULL,
  countback INTEGER NOT NULL,
  best_setting_name TEXT,
  best_hit_rate REAL,
  current_price REAL,
  predicted_return_pct REAL,
  probability_positive REAL,
  probability_target REAL,
  probability_stop REAL,
  started_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spot_present_analog_matches (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  setting_name TEXT NOT NULL,
  match_open_time INTEGER NOT NULL,
  distance REAL NOT NULL,
  similarity_weight REAL NOT NULL,
  entry_price REAL NOT NULL,
  future_return_pct REAL NOT NULL,
  hit_target INTEGER NOT NULL,
  hit_stop INTEGER NOT NULL,
  max_favorable_pct REAL NOT NULL,
  max_adverse_pct REAL NOT NULL,
  features_json TEXT NOT NULL
);
"""


SETTINGS = [
    {
        "name": "momentum_volume",
        "weights": {
            "ret_15": 1.3,
            "ret_30": 1.2,
            "ret_60": 0.9,
            "ret_240": 0.4,
            "volume_ratio": 0.9,
            "pos_60": 0.7,
            "realized_vol_60": 0.4,
            "compression_60_pct": 0.4,
        },
    },
    {
        "name": "breakout_compression",
        "weights": {
            "ret_15": 0.8,
            "ret_30": 0.9,
            "ret_60": 0.7,
            "volume_ratio": 0.8,
            "volume_z": 0.8,
            "pos_60": 1.2,
            "pos_240": 1.0,
            "compression_60_pct": 1.2,
        },
    },
    {
        "name": "mean_reversion_guarded",
        "weights": {
            "ret_15": 0.7,
            "ret_30": 0.6,
            "ret_60": 0.8,
            "ret_240": 1.0,
            "pos_60": 1.1,
            "pos_240": 1.1,
            "realized_vol_60": 0.9,
            "volume_ratio": 0.5,
        },
    },
    {
        "name": "low_noise_trend",
        "weights": {
            "ret_15": 1.0,
            "ret_30": 1.0,
            "ret_60": 1.0,
            "ret_240": 0.5,
            "realized_vol_60": 1.3,
            "compression_60_pct": 1.0,
            "volume_ratio": 0.6,
        },
    },
]


def now_ns():
    return time.time_ns()


def connect_db(path):
    db_path = Path(path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def request_json(base_url, path, params=None):
    url = f"{base_url}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsPresentAnalog/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values):
    return sum(values) / len(values) if values else 0.0


def stdev(values):
    if len(values) < 2:
        return 0.0
    m = mean(values)
    return math.sqrt(sum((x - m) ** 2 for x in values) / (len(values) - 1))


def pct(new, old):
    return (new / old - 1) * 100 if old else 0.0


def load_spot_candles(base_url, ticker, timeframe, countback):
    payload = request_json(
        base_url,
        "/v1/api-meta/candles",
        {"market": ticker, "timeframe": timeframe, "to": int(time.time()), "countback": countback},
    )
    candles = list(reversed(payload.get("candles") or []))
    parsed = []
    for candle in candles:
        parsed.append({
            "open_time": int(candle["openTime"]),
            "open": number(candle["open"]),
            "high": number(candle["high"]),
            "low": number(candle["low"]),
            "close": number(candle["close"]),
            "volume": number(candle.get("volume")) or 0.0,
        })
    return [c for c in parsed if c["close"] is not None]


def features_at(candles, idx):
    w15 = candles[idx - 15:idx]
    w30 = candles[idx - 30:idx]
    w60 = candles[idx - 60:idx]
    w240 = candles[idx - 240:idx]
    close = candles[idx - 1]["close"]
    returns = [math.log(w60[i]["close"] / w60[i - 1]["close"]) for i in range(1, len(w60)) if w60[i - 1]["close"]]
    high60 = max(c["high"] for c in w60)
    low60 = min(c["low"] for c in w60)
    high240 = max(c["high"] for c in w240)
    low240 = min(c["low"] for c in w240)
    volume_recent = mean([c["volume"] for c in candles[idx - 5:idx]])
    volume_base_series = [c["volume"] for c in candles[idx - 65:idx - 5]]
    volume_base = mean(volume_base_series)
    volume_std = stdev(volume_base_series)
    return {
        "ret_15": pct(close, w15[0]["close"]),
        "ret_30": pct(close, w30[0]["close"]),
        "ret_60": pct(close, w60[0]["close"]),
        "ret_240": pct(close, w240[0]["close"]),
        "pos_60": (close - low60) / (high60 - low60) if high60 != low60 else 0.5,
        "pos_240": (close - low240) / (high240 - low240) if high240 != low240 else 0.5,
        "volume_ratio": volume_recent / volume_base if volume_base else 0.0,
        "volume_z": (volume_recent - volume_base) / volume_std if volume_std else 0.0,
        "realized_vol_60": stdev(returns) * math.sqrt(60) * 100,
        "compression_60_pct": (high60 - low60) / close * 100 if close else 0.0,
    }


def outcome_at(candles, idx, horizon, target_pct, stop_pct):
    entry = candles[idx]["open"]
    future = candles[idx:idx + horizon]
    max_fav = 0.0
    max_adv = 0.0
    hit_target = False
    hit_stop = False
    exit_price = future[-1]["close"]
    for candle in future:
        high_ret = pct(candle["high"], entry)
        low_ret = pct(candle["low"], entry)
        max_fav = max(max_fav, high_ret)
        max_adv = min(max_adv, low_ret)
        if high_ret >= target_pct:
            hit_target = True
            exit_price = entry * (1 + target_pct / 100)
            break
        if low_ret <= -abs(stop_pct):
            hit_stop = True
            exit_price = entry * (1 - abs(stop_pct) / 100)
            break
    return {
        "entry": entry,
        "exit": exit_price,
        "future_return_pct": pct(exit_price, entry),
        "hit_target": hit_target,
        "hit_stop": hit_stop,
        "max_favorable_pct": max_fav,
        "max_adverse_pct": max_adv,
    }


def normalize_feature_map(feature_maps):
    keys = sorted(feature_maps[0].keys())
    stats = {}
    for key in keys:
        values = [f[key] for f in feature_maps]
        sd = stdev(values)
        stats[key] = {"mean": mean(values), "stdev": sd if sd else 1.0}
    return stats


def distance(a, b, stats, weights):
    total = 0.0
    used = 0.0
    for key, weight in weights.items():
        if key not in a or key not in b:
            continue
        za = (a[key] - stats[key]["mean"]) / stats[key]["stdev"]
        zb = (b[key] - stats[key]["mean"]) / stats[key]["stdev"]
        total += weight * (za - zb) ** 2
        used += weight
    return math.sqrt(total / used) if used else 999.0


def top_analogs(candles, current_idx, horizon, setting, k, target_pct, stop_pct):
    rows = []
    all_features = [features_at(candles, idx) for idx in range(240, current_idx - horizon)]
    current_features = features_at(candles, current_idx)
    stats = normalize_feature_map(all_features + [current_features])
    for offset, idx in enumerate(range(240, current_idx - horizon)):
        f = all_features[offset]
        d = distance(current_features, f, stats, setting["weights"])
        outcome = outcome_at(candles, idx, horizon, target_pct, stop_pct)
        rows.append({"idx": idx, "distance": d, "features": f, "outcome": outcome})
    rows.sort(key=lambda r: r["distance"])
    return current_features, rows[:k]


def backtest_setting(candles, horizon, setting, k, target_pct, stop_pct, step):
    hits = 0
    tests = 0
    returns = []
    start = 480
    end = len(candles) - horizon - 1
    for current_idx in range(start, end, step):
        _, matches = top_analogs(candles[:current_idx + horizon + 1], current_idx, horizon, setting, k, target_pct, stop_pct)
        if len(matches) < k:
            continue
        weights = [1 / (m["distance"] + 0.0001) for m in matches]
        pred = sum(w * m["outcome"]["future_return_pct"] for w, m in zip(weights, matches)) / sum(weights)
        actual = outcome_at(candles, current_idx, horizon, target_pct, stop_pct)["future_return_pct"]
        if (pred > 0 and actual > 0) or (pred <= 0 and actual <= 0):
            hits += 1
        returns.append(actual if pred > 0 else 0.0)
        tests += 1
    return {
        "tests": tests,
        "hit_rate": hits / tests if tests else 0.0,
        "avg_return_when_positive": mean(returns) if returns else 0.0,
    }


def run(args):
    base_url = REST_URLS[args.env]
    candles = load_spot_candles(base_url, args.ticker, args.timeframe, args.countback)
    if len(candles) < 540 + args.horizon:
        raise SystemExit(f"Need more candles. Got {len(candles)}.")
    current_idx = len(candles) - 1
    conn = connect_db(args.db)
    scored_settings = []
    for setting in SETTINGS:
        result = backtest_setting(candles, args.horizon, setting, args.k, args.target_pct, args.stop_pct, args.step)
        scored_settings.append({"setting": setting, **result})
    scored_settings.sort(key=lambda r: (r["hit_rate"], r["avg_return_when_positive"]), reverse=True)
    best = scored_settings[0]
    current_features, matches = top_analogs(candles, current_idx, args.horizon, best["setting"], args.k, args.target_pct, args.stop_pct)
    weights = [1 / (m["distance"] + 0.0001) for m in matches]
    weighted_return = sum(w * m["outcome"]["future_return_pct"] for w, m in zip(weights, matches)) / sum(weights)
    probability_positive = sum(w for w, m in zip(weights, matches) if m["outcome"]["future_return_pct"] > 0) / sum(weights)
    probability_target = sum(w for w, m in zip(weights, matches) if m["outcome"]["hit_target"]) / sum(weights)
    probability_stop = sum(w for w, m in zip(weights, matches) if m["outcome"]["hit_stop"]) / sum(weights)
    current_price = candles[-1]["close"]

    raw = {
        "settings": [{k: v for k, v in s.items() if k != "setting"} | {"name": s["setting"]["name"]} for s in scored_settings],
        "current_features": current_features,
    }
    run_id = conn.execute(
        """
        INSERT INTO spot_present_analog_runs(
          environment, ticker, timeframe, horizon_minutes, countback, best_setting_name,
          best_hit_rate, current_price, predicted_return_pct, probability_positive,
          probability_target, probability_stop, started_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.env,
            args.ticker.upper(),
            args.timeframe,
            args.horizon,
            args.countback,
            best["setting"]["name"],
            best["hit_rate"],
            current_price,
            weighted_return,
            probability_positive,
            probability_target,
            probability_stop,
            now_ns(),
            json.dumps(raw, separators=(",", ":")),
        ),
    ).lastrowid

    for m in matches:
        o = m["outcome"]
        conn.execute(
            """
            INSERT INTO spot_present_analog_matches(
              run_id, ticker, setting_name, match_open_time, distance, similarity_weight,
              entry_price, future_return_pct, hit_target, hit_stop,
              max_favorable_pct, max_adverse_pct, features_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                args.ticker.upper(),
                best["setting"]["name"],
                candles[m["idx"]]["open_time"],
                m["distance"],
                1 / (m["distance"] + 0.0001),
                o["entry"],
                o["future_return_pct"],
                1 if o["hit_target"] else 0,
                1 if o["hit_stop"] else 0,
                o["max_favorable_pct"],
                o["max_adverse_pct"],
                json.dumps(m["features"], separators=(",", ":")),
            ),
        )
    conn.commit()
    conn.close()

    print(json.dumps({
        "run_id": run_id,
        "ticker": args.ticker.upper(),
        "current_price": current_price,
        "horizon_minutes": args.horizon,
        "best_setting": best["setting"]["name"],
        "best_setting_hit_rate": best["hit_rate"],
        "predicted_return_pct": weighted_return,
        "probability_positive": probability_positive,
        "probability_target": probability_target,
        "probability_stop": probability_stop,
        "top_matches": [
            {
                "at": candles[m["idx"]]["open_time"],
                "distance": m["distance"],
                "future_return_pct": m["outcome"]["future_return_pct"],
                "hit_target": m["outcome"]["hit_target"],
                "hit_stop": m["outcome"]["hit_stop"],
                "max_favorable_pct": m["outcome"]["max_favorable_pct"],
                "max_adverse_pct": m["outcome"]["max_adverse_pct"],
            }
            for m in matches
        ],
        "settings_backtest": [
            {"name": s["setting"]["name"], "tests": s["tests"], "hit_rate": s["hit_rate"], "avg_return_when_positive": s["avg_return_when_positive"]}
            for s in scored_settings
        ],
    }, indent=2))


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Find past spot states closest to the present and compare their future outcomes.")
    parser.add_argument("--env", choices=sorted(REST_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--ticker", default="COIN")
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--countback", type=int, default=1440)
    parser.add_argument("--horizon", type=int, default=60)
    parser.add_argument("--target-pct", type=float, default=0.5)
    parser.add_argument("--stop-pct", type=float, default=0.35)
    parser.add_argument("--k", type=int, default=12)
    parser.add_argument("--step", type=int, default=20)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

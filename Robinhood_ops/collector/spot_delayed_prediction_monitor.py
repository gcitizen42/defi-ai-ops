#!/usr/bin/env python3
import argparse
import json
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
CREATE TABLE IF NOT EXISTS delayed_prediction_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  ticker TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  base_horizon_minutes INTEGER NOT NULL,
  grace_minutes INTEGER NOT NULL,
  target_pct REAL NOT NULL,
  stop_pct REAL NOT NULL,
  tested_predictions INTEGER NOT NULL,
  on_time_hits INTEGER NOT NULL,
  delayed_hits INTEGER NOT NULL,
  stops_before_hit INTEGER NOT NULL,
  misses INTEGER NOT NULL,
  avg_delay_minutes REAL,
  started_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS delayed_prediction_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  prediction_open_time INTEGER NOT NULL,
  entry_price REAL NOT NULL,
  target_price REAL NOT NULL,
  stop_price REAL NOT NULL,
  result TEXT NOT NULL,
  hit_minutes INTEGER,
  delay_minutes INTEGER,
  max_favorable_pct REAL NOT NULL,
  max_adverse_pct REAL NOT NULL,
  features_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS active_prediction_monitors (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  ticker TEXT NOT NULL,
  direction TEXT NOT NULL,
  entry_price REAL NOT NULL,
  target_price REAL NOT NULL,
  stop_price REAL NOT NULL,
  base_deadline_ns INTEGER NOT NULL,
  grace_deadline_ns INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at_ns INTEGER NOT NULL,
  updated_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);
"""


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
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsDelayedPrediction/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def mean(values):
    return sum(values) / len(values) if values else None


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


def simple_features(candles, idx):
    close = candles[idx - 1]["close"]
    w60 = candles[idx - 60:idx]
    w240 = candles[idx - 240:idx]
    high60 = max(c["high"] for c in w60)
    low60 = min(c["low"] for c in w60)
    high240 = max(c["high"] for c in w240)
    low240 = min(c["low"] for c in w240)
    vol5 = sum(c["volume"] for c in candles[idx - 5:idx]) / 5
    vol60 = sum(c["volume"] for c in candles[idx - 65:idx - 5]) / 60
    return {
        "ret_15": pct(close, candles[idx - 15]["close"]),
        "ret_60": pct(close, candles[idx - 60]["close"]),
        "ret_240": pct(close, candles[idx - 240]["close"]),
        "pos_60": (close - low60) / (high60 - low60) if high60 != low60 else 0.5,
        "pos_240": (close - low240) / (high240 - low240) if high240 != low240 else 0.5,
        "volume_ratio": vol5 / vol60 if vol60 else 0.0,
    }


def signal_score(features):
    return (
        0.8 * features["ret_15"]
        + 0.6 * features["ret_60"]
        + 0.2 * features["ret_240"]
        + 0.8 * max(0.0, features["pos_60"] - 0.65)
        + 0.35 * max(0.0, features["volume_ratio"] - 1.0)
    )


def delayed_outcome(candles, idx, base_horizon, grace, target_pct, stop_pct):
    entry = candles[idx]["open"]
    target_price = entry * (1 + target_pct / 100)
    stop_price = entry * (1 - abs(stop_pct) / 100)
    max_fav = 0.0
    max_adv = 0.0
    hit_minutes = None
    stop_minutes = None
    total = base_horizon + grace
    for minute, candle in enumerate(candles[idx:idx + total], start=1):
        max_fav = max(max_fav, pct(candle["high"], entry))
        max_adv = min(max_adv, pct(candle["low"], entry))
        if stop_minutes is None and candle["low"] <= stop_price:
            stop_minutes = minute
        if hit_minutes is None and candle["high"] >= target_price:
            hit_minutes = minute
        if hit_minutes is not None or stop_minutes is not None:
            break

    if hit_minutes is not None and (stop_minutes is None or hit_minutes <= stop_minutes):
        result = "on_time_hit" if hit_minutes <= base_horizon else "delayed_hit"
        delay = max(0, hit_minutes - base_horizon)
    elif stop_minutes is not None:
        result = "stopped_before_hit"
        delay = None
    else:
        result = "miss"
        delay = None
    return {
        "entry": entry,
        "target_price": target_price,
        "stop_price": stop_price,
        "result": result,
        "hit_minutes": hit_minutes,
        "delay_minutes": delay,
        "max_favorable_pct": max_fav,
        "max_adverse_pct": max_adv,
    }


def run_backtest(args):
    base_url = REST_URLS[args.env]
    candles = load_spot_candles(base_url, args.ticker, args.timeframe, args.countback)
    if len(candles) < 240 + args.base_horizon + args.grace:
        raise SystemExit(f"Need more candles. Got {len(candles)}.")
    conn = connect_db(args.db)
    events = []
    skipped = 0
    for idx in range(240, len(candles) - args.base_horizon - args.grace, args.step):
        features = simple_features(candles, idx)
        score = signal_score(features)
        if score < args.score_threshold:
            skipped += 1
            continue
        outcome = delayed_outcome(candles, idx, args.base_horizon, args.grace, args.target_pct, args.stop_pct)
        events.append({"idx": idx, "features": features | {"score": score}, "outcome": outcome})

    counts = {
        "on_time_hit": sum(1 for e in events if e["outcome"]["result"] == "on_time_hit"),
        "delayed_hit": sum(1 for e in events if e["outcome"]["result"] == "delayed_hit"),
        "stopped_before_hit": sum(1 for e in events if e["outcome"]["result"] == "stopped_before_hit"),
        "miss": sum(1 for e in events if e["outcome"]["result"] == "miss"),
    }
    delays = [e["outcome"]["delay_minutes"] for e in events if e["outcome"]["delay_minutes"] is not None]
    run_id = conn.execute(
        """
        INSERT INTO delayed_prediction_runs(
          environment, ticker, timeframe, base_horizon_minutes, grace_minutes,
          target_pct, stop_pct, tested_predictions, on_time_hits, delayed_hits,
          stops_before_hit, misses, avg_delay_minutes, started_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.env,
            args.ticker.upper(),
            args.timeframe,
            args.base_horizon,
            args.grace,
            args.target_pct,
            args.stop_pct,
            len(events),
            counts["on_time_hit"],
            counts["delayed_hit"],
            counts["stopped_before_hit"],
            counts["miss"],
            mean(delays),
            now_ns(),
            json.dumps({"skipped": skipped, "args": vars(args)}, separators=(",", ":")),
        ),
    ).lastrowid
    for e in events:
        o = e["outcome"]
        conn.execute(
            """
            INSERT INTO delayed_prediction_events(
              run_id, ticker, prediction_open_time, entry_price, target_price,
              stop_price, result, hit_minutes, delay_minutes,
              max_favorable_pct, max_adverse_pct, features_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                args.ticker.upper(),
                candles[e["idx"]]["open_time"],
                o["entry"],
                o["target_price"],
                o["stop_price"],
                o["result"],
                o["hit_minutes"],
                o["delay_minutes"],
                o["max_favorable_pct"],
                o["max_adverse_pct"],
                json.dumps(e["features"], separators=(",", ":")),
            ),
        )
    conn.commit()
    conn.close()
    print(json.dumps({"run_id": run_id, "ticker": args.ticker.upper(), "predictions": len(events), **counts, "avg_delay_minutes": mean(delays), "skipped": skipped}, indent=2))


def create_monitor(args):
    base_url = REST_URLS[args.env]
    candles = load_spot_candles(base_url, args.ticker, args.timeframe, 5)
    price = candles[-1]["close"]
    target_price = price * (1 + args.target_pct / 100)
    stop_price = price * (1 - abs(args.stop_pct) / 100)
    now = now_ns()
    conn = connect_db(args.db)
    monitor_id = conn.execute(
        """
        INSERT INTO active_prediction_monitors(
          environment, ticker, direction, entry_price, target_price, stop_price,
          base_deadline_ns, grace_deadline_ns, status, created_at_ns, updated_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.env,
            args.ticker.upper(),
            "long",
            price,
            target_price,
            stop_price,
            now + args.base_horizon * 60 * 1_000_000_000,
            now + (args.base_horizon + args.grace) * 60 * 1_000_000_000,
            "watching",
            now,
            now,
            json.dumps(vars(args), separators=(",", ":")),
        ),
    ).lastrowid
    conn.commit()
    conn.close()
    print(json.dumps({"monitor_id": monitor_id, "ticker": args.ticker.upper(), "entry": price, "target": target_price, "stop": stop_price, "base_horizon_minutes": args.base_horizon, "grace_minutes": args.grace}, indent=2))


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Analyze delayed target hits and create active prediction monitors.")
    parser.add_argument("--mode", choices=["backtest", "create-monitor"], default="backtest")
    parser.add_argument("--env", choices=sorted(REST_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--ticker", default="COIN")
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--countback", type=int, default=1440)
    parser.add_argument("--base-horizon", type=int, default=60)
    parser.add_argument("--grace", type=int, default=30)
    parser.add_argument("--target-pct", type=float, default=0.5)
    parser.add_argument("--stop-pct", type=float, default=0.35)
    parser.add_argument("--score-threshold", type=float, default=1.25)
    parser.add_argument("--step", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    if parsed.mode == "backtest":
        run_backtest(parsed)
    else:
        create_monitor(parsed)

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
CREATE TABLE IF NOT EXISTS spot_field_backtests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  ticker TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  horizon_minutes INTEGER NOT NULL,
  target_pct REAL NOT NULL,
  stop_pct REAL NOT NULL,
  tests INTEGER NOT NULL,
  predictions INTEGER NOT NULL,
  wins INTEGER NOT NULL,
  losses INTEGER NOT NULL,
  timeouts INTEGER NOT NULL,
  skipped INTEGER NOT NULL,
  win_rate REAL,
  avg_return_pct REAL,
  avg_max_favorable_pct REAL,
  avg_max_adverse_pct REAL,
  started_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spot_field_backtest_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  backtest_id INTEGER NOT NULL,
  ticker TEXT NOT NULL,
  prediction_open_time INTEGER NOT NULL,
  entry_price REAL NOT NULL,
  exit_price REAL NOT NULL,
  predicted_direction TEXT NOT NULL,
  result TEXT NOT NULL,
  return_pct REAL NOT NULL,
  max_favorable_pct REAL NOT NULL,
  max_adverse_pct REAL NOT NULL,
  score REAL NOT NULL,
  features_json TEXT NOT NULL
);
"""


def now_ns():
    return time.time_ns()


def request_json(base_url, path, params=None):
    url = f"{base_url}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsSpotFieldBacktest/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def connect_db(path):
    db_path = Path(path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


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
    to = int(time.time())
    payload = request_json(
        base_url,
        "/v1/api-meta/candles",
        {"market": ticker, "timeframe": timeframe, "to": to, "countback": countback},
    )
    candles = payload.get("candles") or []
    candles = list(reversed(candles))
    parsed = []
    for candle in candles:
        parsed.append({
            "open_time": int(candle["openTime"]),
            "open": number(candle["open"]),
            "high": number(candle["high"]),
            "low": number(candle["low"]),
            "close": number(candle["close"]),
            "volume": number(candle.get("volume")) or 0.0,
            "raw": candle,
        })
    return [c for c in parsed if c["close"] is not None]


def market_field_features(candles, idx):
    window_15 = candles[idx - 15:idx]
    window_30 = candles[idx - 30:idx]
    window_60 = candles[idx - 60:idx]
    window_240 = candles[idx - 240:idx]
    current = candles[idx - 1]
    close = current["close"]

    returns = [math.log(window_60[i]["close"] / window_60[i - 1]["close"]) for i in range(1, len(window_60)) if window_60[i - 1]["close"]]
    high_60 = max(c["high"] for c in window_60)
    low_60 = min(c["low"] for c in window_60)
    high_240 = max(c["high"] for c in window_240)
    low_240 = min(c["low"] for c in window_240)
    pos_60 = (close - low_60) / (high_60 - low_60) if high_60 != low_60 else 0.5
    pos_240 = (close - low_240) / (high_240 - low_240) if high_240 != low_240 else 0.5
    volume_recent = mean([c["volume"] for c in candles[idx - 5:idx]])
    volume_base = mean([c["volume"] for c in candles[idx - 65:idx - 5]])
    volume_ratio = volume_recent / volume_base if volume_base else 0.0
    volume_series = [c["volume"] for c in candles[idx - 65:idx - 5]]
    volume_z = (volume_recent - mean(volume_series)) / stdev(volume_series) if stdev(volume_series) else 0.0

    ret_15 = pct(close, window_15[0]["close"])
    ret_30 = pct(close, window_30[0]["close"])
    ret_60 = pct(close, window_60[0]["close"])
    ret_240 = pct(close, window_240[0]["close"])
    realized_vol_60 = stdev(returns) * math.sqrt(60) * 100

    # Candle-only proxy for "liquidity field" until true spot order book data is available.
    compression = (high_60 - low_60) / close * 100
    breakout_pressure = max(0.0, pos_60 - 0.75) * 4
    pullback_pressure = max(0.0, 0.25 - pos_60) * -3
    momentum = 0.55 * ret_15 + 0.35 * ret_30 + 0.20 * ret_60
    volume_push = math.log(max(volume_ratio, 0.2))
    noise_penalty = max(0.0, realized_vol_60 - 1.25) * 0.6
    extension_penalty = max(0.0, ret_240 - 8.0) * 0.25
    compression_bonus = 0.35 if compression < 1.0 and volume_ratio > 1.1 else 0.0
    score = momentum + 0.65 * volume_push + breakout_pressure + pullback_pressure + compression_bonus - noise_penalty - extension_penalty

    return {
        "close": close,
        "ret_15": ret_15,
        "ret_30": ret_30,
        "ret_60": ret_60,
        "ret_240": ret_240,
        "pos_60": pos_60,
        "pos_240": pos_240,
        "volume_ratio": volume_ratio,
        "volume_z": volume_z,
        "realized_vol_60": realized_vol_60,
        "compression_60_pct": compression,
        "score": score,
    }


def evaluate_outcome(candles, idx, horizon, target_pct, stop_pct):
    entry = candles[idx]["open"]
    future = candles[idx:idx + horizon]
    max_fav = 0.0
    max_adv = 0.0
    result = "timeout"
    exit_price = future[-1]["close"]

    for candle in future:
        high_ret = pct(candle["high"], entry)
        low_ret = pct(candle["low"], entry)
        max_fav = max(max_fav, high_ret)
        max_adv = min(max_adv, low_ret)
        if high_ret >= target_pct:
            result = "win"
            exit_price = entry * (1 + target_pct / 100)
            break
        if low_ret <= -abs(stop_pct):
            result = "loss"
            exit_price = entry * (1 - abs(stop_pct) / 100)
            break

    return {
        "entry": entry,
        "exit": exit_price,
        "return_pct": pct(exit_price, entry),
        "max_favorable_pct": max_fav,
        "max_adverse_pct": max_adv,
        "result": result,
    }


def run_backtest(conn, args, ticker):
    base_url = REST_URLS[args.env]
    candles = load_spot_candles(base_url, ticker, args.timeframe, args.countback)
    if len(candles) < 240 + args.horizon:
        print(f"{ticker}: skipped, only {len(candles)} candles")
        return None

    events = []
    skipped = 0
    for idx in range(240, len(candles) - args.horizon, args.step):
        features = market_field_features(candles, idx)
        if features["score"] < args.score_threshold:
            skipped += 1
            continue
        outcome = evaluate_outcome(candles, idx, args.horizon, args.target_pct, args.stop_pct)
        events.append({
            "ticker": ticker,
            "prediction_open_time": candles[idx]["open_time"],
            "direction": "long",
            "features": features,
            "outcome": outcome,
        })

    wins = sum(1 for e in events if e["outcome"]["result"] == "win")
    losses = sum(1 for e in events if e["outcome"]["result"] == "loss")
    timeouts = sum(1 for e in events if e["outcome"]["result"] == "timeout")
    predictions = len(events)
    win_rate = wins / predictions if predictions else None
    avg_return = mean([e["outcome"]["return_pct"] for e in events]) if events else None
    avg_fav = mean([e["outcome"]["max_favorable_pct"] for e in events]) if events else None
    avg_adv = mean([e["outcome"]["max_adverse_pct"] for e in events]) if events else None
    raw = {
        "ticker": ticker,
        "candles": len(candles),
        "args": vars(args),
        "events": events[:20],
    }

    backtest_id = conn.execute(
        """
        INSERT INTO spot_field_backtests(
          environment, ticker, timeframe, horizon_minutes, target_pct, stop_pct,
          tests, predictions, wins, losses, timeouts, skipped, win_rate,
          avg_return_pct, avg_max_favorable_pct, avg_max_adverse_pct, started_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.env,
            ticker,
            args.timeframe,
            args.horizon,
            args.target_pct,
            args.stop_pct,
            max(0, (len(candles) - args.horizon - 240) // args.step),
            predictions,
            wins,
            losses,
            timeouts,
            skipped,
            win_rate,
            avg_return,
            avg_fav,
            avg_adv,
            now_ns(),
            json.dumps(raw, separators=(",", ":")),
        ),
    ).lastrowid

    for event in events:
        outcome = event["outcome"]
        features = event["features"]
        conn.execute(
            """
            INSERT INTO spot_field_backtest_events(
              backtest_id, ticker, prediction_open_time, entry_price, exit_price,
              predicted_direction, result, return_pct, max_favorable_pct,
              max_adverse_pct, score, features_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                backtest_id,
                ticker,
                event["prediction_open_time"],
                outcome["entry"],
                outcome["exit"],
                event["direction"],
                outcome["result"],
                outcome["return_pct"],
                outcome["max_favorable_pct"],
                outcome["max_adverse_pct"],
                features["score"],
                json.dumps(features, separators=(",", ":")),
            ),
        )

    return {
        "ticker": ticker,
        "candles": len(candles),
        "predictions": predictions,
        "wins": wins,
        "losses": losses,
        "timeouts": timeouts,
        "skipped": skipped,
        "win_rate": win_rate,
        "avg_return_pct": avg_return,
        "avg_max_favorable_pct": avg_fav,
        "avg_max_adverse_pct": avg_adv,
    }


def main():
    args = parse_args()
    conn = connect_db(args.db)
    tickers = [ticker.strip().upper() for ticker in args.tickers.split(",") if ticker.strip()]
    summaries = []
    for ticker in tickers:
        print(f"Testing {ticker}...")
        try:
            summary = run_backtest(conn, args, ticker)
            if summary:
                summaries.append(summary)
                wr = summary["win_rate"]
                wr_text = f"{wr:.1%}" if wr is not None else "n/a"
                print(
                    f"{ticker}: predictions={summary['predictions']} wins={summary['wins']} "
                    f"losses={summary['losses']} timeouts={summary['timeouts']} "
                    f"win_rate={wr_text} avg_return={summary['avg_return_pct']}"
                )
        except Exception as exc:
            print(f"{ticker}: error: {exc}")
    conn.commit()
    conn.close()
    print(json.dumps(summaries, indent=2))


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Walk-forward test a candle-proxy Market Field signal on Arcus spot data.")
    parser.add_argument("--env", choices=sorted(REST_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--tickers", default="COIN,MSTR,RKLB,AMD,NVDA,AAPL,SPY,QQQ")
    parser.add_argument("--timeframe", default="1m")
    parser.add_argument("--countback", type=int, default=1440)
    parser.add_argument("--horizon", type=int, default=60)
    parser.add_argument("--target-pct", type=float, default=0.5)
    parser.add_argument("--stop-pct", type=float, default=0.35)
    parser.add_argument("--score-threshold", type=float, default=1.25)
    parser.add_argument("--step", type=int, default=5)
    return parser.parse_args()


if __name__ == "__main__":
    main()

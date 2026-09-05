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
CREATE TABLE IF NOT EXISTS spot_paper_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  ticker TEXT NOT NULL,
  notional_usd REAL NOT NULL,
  target_pct REAL NOT NULL,
  stop_pct REAL NOT NULL,
  trailing_pct REAL,
  timeout_seconds INTEGER NOT NULL,
  entry_price REAL,
  exit_price REAL,
  quantity REAL,
  gross_pnl_usd REAL,
  gross_pnl_pct REAL,
  exit_reason TEXT,
  started_at_ns INTEGER NOT NULL,
  exited_at_ns INTEGER,
  raw_json TEXT
);

CREATE TABLE IF NOT EXISTS spot_paper_ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  received_at_ns INTEGER NOT NULL,
  price REAL NOT NULL,
  change_pct_24h REAL,
  volume_24h REAL,
  unrealized_pnl_usd REAL,
  unrealized_pnl_pct REAL,
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
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsSpotPaperWatch/0.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_spot_entry(base_url, ticker):
    overview = request_json(base_url, "/v1/api-meta/spot/overview")
    for entry in overview:
        if entry.get("ticker", "").upper() == ticker.upper():
            quote = entry.get("quote") or {}
            price = quote.get("price")
            if price is None:
                raise SystemExit(f"{ticker} has no current quote price.")
            return entry
    raise SystemExit(f"{ticker} not found in spot overview.")


def pct_change(entry_price, current_price):
    return (current_price - entry_price) / entry_price * 100


def print_notification(reason, ticker, price, pnl_usd, pnl_pct):
    print("")
    print("SELL NOTIFICATION")
    print(f"reason: {reason}")
    print(f"ticker: {ticker}")
    print(f"price: {price:.8f}")
    print(f"paper pnl: ${pnl_usd:.5f} ({pnl_pct:.4f}%)")
    print("")


def main():
    args = parse_args()
    validate_args(args)
    base_url = REST_URLS[args.env]
    conn = connect_db(args.db)
    started_at = now_ns()

    entry = get_spot_entry(base_url, args.ticker)
    quote = entry.get("quote") or {}
    entry_price = float(quote["price"])
    quantity = args.notional / entry_price
    high_price = entry_price

    run_id = conn.execute(
        """
        INSERT INTO spot_paper_runs(
          environment, ticker, notional_usd, target_pct, stop_pct, trailing_pct,
          timeout_seconds, entry_price, quantity, started_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            args.env,
            args.ticker.upper(),
            args.notional,
            args.target_pct,
            args.stop_pct,
            args.trailing_pct,
            args.timeout,
            entry_price,
            quantity,
            started_at,
            json.dumps(entry, separators=(",", ":")),
        ),
    ).lastrowid
    conn.commit()

    print(f"spot paper run #{run_id}: bought {args.ticker.upper()} paper ${args.notional:.2f}")
    print(f"entry={entry_price:.8f} qty={quantity:.10f}")
    print(f"target=+{args.target_pct}% stop=-{args.stop_pct}% trailing={args.trailing_pct}% timeout={args.timeout}s")

    exit_reason = None
    exit_price = entry_price
    pnl_usd = 0.0
    pnl_pct = 0.0

    while True:
        tick = get_spot_entry(base_url, args.ticker)
        quote = tick.get("quote") or {}
        price = float(quote["price"])
        high_price = max(high_price, price)
        pnl_pct = pct_change(entry_price, price)
        pnl_usd = (price - entry_price) * quantity
        drawdown_from_high_pct = (high_price - price) / high_price * 100 if high_price else 0
        elapsed = (now_ns() - started_at) / 1_000_000_000

        conn.execute(
            """
            INSERT INTO spot_paper_ticks(
              run_id, received_at_ns, price, change_pct_24h, volume_24h,
              unrealized_pnl_usd, unrealized_pnl_pct, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                now_ns(),
                price,
                quote.get("changePercent24h"),
                quote.get("volume24h"),
                pnl_usd,
                pnl_pct,
                json.dumps(tick, separators=(",", ":")),
            ),
        )
        conn.commit()

        print(
            f"{elapsed:6.1f}s {args.ticker.upper()} price={price:.8f} "
            f"pnl=${pnl_usd:.5f} ({pnl_pct:.4f}%) "
            f"high={high_price:.8f} trail_dd={drawdown_from_high_pct:.4f}%"
        )

        if pnl_pct >= args.target_pct:
            exit_reason = "target"
        elif pnl_pct <= -abs(args.stop_pct):
            exit_reason = "stop"
        elif args.trailing_pct is not None and drawdown_from_high_pct >= args.trailing_pct:
            exit_reason = "trailing_sell"
        elif elapsed >= args.timeout:
            exit_reason = "timeout_reminder"

        if exit_reason:
            exit_price = price
            break
        time.sleep(args.interval)

    conn.execute(
        """
        UPDATE spot_paper_runs
        SET exit_price = ?, gross_pnl_usd = ?, gross_pnl_pct = ?,
            exit_reason = ?, exited_at_ns = ?
        WHERE id = ?
        """,
        (exit_price, pnl_usd, pnl_pct, exit_reason, now_ns(), run_id),
    )
    conn.commit()
    conn.close()
    print_notification(exit_reason, args.ticker.upper(), exit_price, pnl_usd, pnl_pct)


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Simulate a spot buy and notify when sell conditions trigger.")
    parser.add_argument("--env", choices=sorted(REST_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--ticker", default="AAPL")
    parser.add_argument("--notional", type=float, default=10.0)
    parser.add_argument("--target-pct", type=float, default=0.05)
    parser.add_argument("--stop-pct", type=float, default=0.05)
    parser.add_argument("--trailing-pct", type=float, default=0.03)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--interval", type=float, default=5.0)
    return parser.parse_args()


def validate_args(args):
    if args.notional <= 0:
        raise SystemExit("--notional must be greater than zero.")
    if args.target_pct <= 0:
        raise SystemExit("--target-pct must be greater than zero.")
    if args.stop_pct <= 0:
        raise SystemExit("--stop-pct must be greater than zero.")
    if args.trailing_pct is not None and args.trailing_pct <= 0:
        raise SystemExit("--trailing-pct must be greater than zero when provided.")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero.")
    if args.interval <= 0:
        raise SystemExit("--interval must be greater than zero.")


if __name__ == "__main__":
    main()

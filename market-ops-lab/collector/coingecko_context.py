#!/usr/bin/env python3
import argparse
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://api.coingecko.com/api/v3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS coingecko_assets (
  coin_id TEXT PRIMARY KEY,
  symbol TEXT,
  name TEXT,
  market_cap_rank INTEGER,
  raw_json TEXT NOT NULL,
  updated_at_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS coingecko_prices (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  coin_id TEXT NOT NULL,
  vs_currency TEXT NOT NULL,
  price REAL,
  market_cap REAL,
  volume_24h REAL,
  change_24h_pct REAL,
  received_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_coingecko_prices_coin_time
ON coingecko_prices(coin_id, received_at_ns);

CREATE TABLE IF NOT EXISTS coingecko_market_chart (
  coin_id TEXT NOT NULL,
  vs_currency TEXT NOT NULL,
  sample_ts_ms INTEGER NOT NULL,
  price REAL,
  market_cap REAL,
  volume REAL,
  fetched_at_ns INTEGER NOT NULL,
  PRIMARY KEY (coin_id, vs_currency, sample_ts_ms)
);

CREATE TABLE IF NOT EXISTS external_context_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  started_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);
"""


def now_ns():
    return time.time_ns()


def load_env_file(path):
    values = {}
    env_path = Path(path)
    if not env_path.exists():
        return values
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def connect_db(path):
    db_path = Path(path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


def request_json(path, params=None, api_key=None):
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {"accept": "application/json", "user-agent": "RobinhoodOpsCoinGeckoContext/0.1"}
    if api_key:
        headers["x-cg-demo-api-key"] = api_key
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def request_json_with_retries(path, params=None, api_key=None, retries=3, backoff=8):
    for attempt in range(retries + 1):
        try:
            return request_json(path, params=params, api_key=api_key)
        except urllib.error.HTTPError as exc:
            if exc.code != 429 or attempt >= retries:
                raise
            wait = backoff * (attempt + 1)
            print(f"rate limited; waiting {wait}s")
            time.sleep(wait)


def store_assets(conn, assets):
    received_at = now_ns()
    for asset in assets:
        conn.execute(
            """
            INSERT INTO coingecko_assets(coin_id, symbol, name, market_cap_rank, raw_json, updated_at_ns)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin_id) DO UPDATE SET
              symbol=excluded.symbol,
              name=excluded.name,
              market_cap_rank=excluded.market_cap_rank,
              raw_json=excluded.raw_json,
              updated_at_ns=excluded.updated_at_ns
            """,
            (
                asset.get("id"),
                asset.get("symbol"),
                asset.get("name"),
                asset.get("market_cap_rank"),
                json.dumps(asset, separators=(",", ":")),
                received_at,
            ),
        )


def store_prices(conn, payload, vs_currency):
    received_at = now_ns()
    for coin_id, data in payload.items():
        conn.execute(
            """
            INSERT INTO coingecko_prices(
              coin_id, vs_currency, price, market_cap, volume_24h,
              change_24h_pct, received_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                coin_id,
                vs_currency,
                data.get(vs_currency),
                data.get(f"{vs_currency}_market_cap"),
                data.get(f"{vs_currency}_24h_vol"),
                data.get(f"{vs_currency}_24h_change"),
                received_at,
                json.dumps(data, separators=(",", ":")),
            ),
        )


def store_market_chart(conn, coin_id, vs_currency, payload):
    fetched_at = now_ns()
    prices = {int(ts): value for ts, value in payload.get("prices", [])}
    market_caps = {int(ts): value for ts, value in payload.get("market_caps", [])}
    volumes = {int(ts): value for ts, value in payload.get("total_volumes", [])}
    for ts, price in prices.items():
        conn.execute(
            """
            INSERT INTO coingecko_market_chart(
              coin_id, vs_currency, sample_ts_ms, price, market_cap, volume, fetched_at_ns
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin_id, vs_currency, sample_ts_ms) DO UPDATE SET
              price=excluded.price,
              market_cap=excluded.market_cap,
              volume=excluded.volume,
              fetched_at_ns=excluded.fetched_at_ns
            """,
            (coin_id, vs_currency, ts, price, market_caps.get(ts), volumes.get(ts), fetched_at),
        )


def main():
    args = parse_args()
    secrets = load_env_file(args.env_file)
    api_key = args.api_key or os.environ.get("COINGECKO_API_KEY") or secrets.get("COINGECKO_API_KEY")
    conn = connect_db(args.db)
    coin_ids = [coin.strip() for coin in args.coins.split(",") if coin.strip()]

    if not args.skip_ping:
        print("CoinGecko ping:", request_json_with_retries("/ping", api_key=api_key).get("gecko_says"))

    prices = request_json_with_retries(
        "/simple/price",
        {
            "ids": ",".join(coin_ids),
            "vs_currencies": args.vs_currency,
            "include_market_cap": "true",
            "include_24hr_vol": "true",
            "include_24hr_change": "true",
        },
        api_key=api_key,
    )
    store_prices(conn, prices, args.vs_currency)
    print(f"stored prices for {len(prices)} coins")

    if args.store_assets:
        markets = request_json_with_retries(
            "/coins/markets",
            {
                "vs_currency": args.vs_currency,
                "ids": ",".join(coin_ids),
                "order": "market_cap_desc",
                "per_page": len(coin_ids),
                "page": 1,
                "sparkline": "false",
                "price_change_percentage": "1h,24h,7d",
            },
            api_key=api_key,
        )
        store_assets(conn, markets)
        print(f"stored asset metadata for {len(markets)} coins")

    if args.history_days > 0:
        for coin_id in coin_ids:
            try:
                chart = request_json_with_retries(
                    f"/coins/{coin_id}/market_chart",
                    {"vs_currency": args.vs_currency, "days": args.history_days},
                    api_key=api_key,
                )
                store_market_chart(conn, coin_id, args.vs_currency, chart)
                print(f"stored {coin_id} market chart")
                time.sleep(args.sleep)
            except Exception as exc:
                print(f"{coin_id}: market chart failed: {exc}")

    conn.execute(
        "INSERT INTO external_context_runs(source, started_at_ns, raw_json) VALUES (?, ?, ?)",
        ("coingecko", now_ns(), json.dumps({"coins": coin_ids, "vs_currency": args.vs_currency}, separators=(",", ":"))),
    )
    conn.commit()
    conn.close()


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    default_env_file = Path(__file__).resolve().parent.parent / "secrets" / "coingecko.env"
    parser = argparse.ArgumentParser(description="Collect public CoinGecko context into SQLite.")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--env-file", default=str(default_env_file))
    parser.add_argument("--api-key")
    parser.add_argument("--coins", default="bitcoin,ethereum,solana,chainlink,hyperliquid,dydx")
    parser.add_argument("--vs-currency", default="usd")
    parser.add_argument("--history-days", type=int, default=1)
    parser.add_argument("--sleep", type=float, default=8.0)
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--skip-ping", action="store_true")
    parser.add_argument("--store-assets", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    main()

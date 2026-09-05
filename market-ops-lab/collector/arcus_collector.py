#!/usr/bin/env python3
import argparse
import asyncio
import json
import os
import signal
import sqlite3
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ENVIRONMENTS = {
    "mainnet": {
        "rest": "https://api.arcus.xyz",
        "ws": "wss://api.arcus.xyz/v1/ws",
    },
    "testnet": {
        "rest": "https://api.testnet.arcus.xyz",
        "ws": "wss://api.testnet.arcus.xyz/v1/ws",
    },
}

DEFAULT_CONFIG = {
    "environment": "mainnet",
    "database": "../data/arcus.sqlite",
    "markets": ["BTC-USD", "ETH-USD", "SOL-USD"],
    "timeframes": ["1m"],
    "orderbook_levels": 12,
    "rest_sync_interval_seconds": 60,
    "websocket_reconnect_seconds": 5,
    "collect_websocket": True,
    "collect_trades": True,
    "collect_bbo": True,
    "collect_l2_orderbook": True,
    "collect_candles": True,
}

SCHEMA = """
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS raw_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  environment TEXT NOT NULL,
  channel TEXT NOT NULL,
  market TEXT,
  event_ts_ns INTEGER,
  received_at_ns INTEGER NOT NULL,
  payload_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_raw_events_channel_market
ON raw_events(channel, market, received_at_ns);

CREATE TABLE IF NOT EXISTS markets (
  market TEXT PRIMARY KEY,
  market_id INTEGER,
  full_asset_name TEXT,
  base_asset TEXT,
  quote_asset TEXT,
  category TEXT,
  type TEXT,
  status TEXT,
  tick_size TEXT,
  step_size TEXT,
  min_order_notional TEXT,
  raw_json TEXT NOT NULL,
  updated_at_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS market_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market TEXT NOT NULL,
  market_id INTEGER,
  status TEXT,
  oracle_price REAL,
  mark_price REAL,
  last_trade_price REAL,
  funding_rate REAL,
  next_funding_rate REAL,
  next_funding_at INTEGER,
  price_change_24h REAL,
  volume_24h REAL,
  volume_24h_notional REAL,
  trades_24h INTEGER,
  open_interest REAL,
  received_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_market_time
ON market_snapshots(market, received_at_ns);

CREATE TABLE IF NOT EXISTS mids (
  market TEXT NOT NULL,
  mid_price REAL,
  global_sequence_id INTEGER,
  received_at_ns INTEGER NOT NULL,
  PRIMARY KEY (market, received_at_ns)
);

CREATE TABLE IF NOT EXISTS candles (
  market TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  open_time INTEGER NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  notional_volume REAL,
  trade_count INTEGER,
  is_final INTEGER,
  received_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL,
  PRIMARY KEY (market, timeframe, open_time)
);

CREATE TABLE IF NOT EXISTS orderbook_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  market TEXT NOT NULL,
  last_sequence_id INTEGER,
  global_sequence_id INTEGER,
  exchange_ts INTEGER,
  received_at_ns INTEGER NOT NULL,
  best_bid_price REAL,
  best_bid_size REAL,
  best_ask_price REAL,
  best_ask_size REAL,
  bid_depth_notional REAL,
  ask_depth_notional REAL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_orderbook_snapshots_market_time
ON orderbook_snapshots(market, received_at_ns);

CREATE TABLE IF NOT EXISTS bbo (
  market TEXT NOT NULL,
  exchange_ts INTEGER,
  received_at_ns INTEGER NOT NULL,
  best_bid_price REAL,
  best_bid_size REAL,
  best_ask_price REAL,
  best_ask_size REAL,
  last_sequence_id INTEGER,
  global_sequence_id INTEGER,
  raw_json TEXT NOT NULL,
  PRIMARY KEY (market, received_at_ns)
);

CREATE TABLE IF NOT EXISTS trades (
  id TEXT,
  market TEXT NOT NULL,
  exchange_ts INTEGER,
  received_at_ns INTEGER NOT NULL,
  price REAL,
  size REAL,
  side TEXT,
  raw_json TEXT NOT NULL,
  PRIMARY KEY (market, received_at_ns, raw_json)
);

CREATE TABLE IF NOT EXISTS collector_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  started_at_ns INTEGER NOT NULL,
  stopped_at_ns INTEGER,
  config_json TEXT NOT NULL
);
"""


def now_ns():
    return time.time_ns()


def as_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value):
    try:
        if value in (None, ""):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def load_config(path):
    config = dict(DEFAULT_CONFIG)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            config.update(json.load(f))
    return config


def resolve_database(config_path, database):
    db_path = Path(database)
    if not db_path.is_absolute():
        base = Path(config_path).resolve().parent if config_path else Path(__file__).resolve().parent
        db_path = (base / db_path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def connect_db(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def request_json(base_url, path, params=None):
    url = f"{base_url}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsArcusCollector/0.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def insert_raw(conn, source, environment, channel, market, payload, received_at, event_ts=None):
    conn.execute(
        """
        INSERT INTO raw_events(source, environment, channel, market, event_ts_ns, received_at_ns, payload_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (source, environment, channel, market, event_ts, received_at, json.dumps(payload, separators=(",", ":"))),
    )


def upsert_market(conn, market, received_at):
    conn.execute(
        """
        INSERT INTO markets(
          market, market_id, full_asset_name, base_asset, quote_asset, category, type, status,
          tick_size, step_size, min_order_notional, raw_json, updated_at_ns
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(market) DO UPDATE SET
          market_id=excluded.market_id,
          full_asset_name=excluded.full_asset_name,
          base_asset=excluded.base_asset,
          quote_asset=excluded.quote_asset,
          category=excluded.category,
          type=excluded.type,
          status=excluded.status,
          tick_size=excluded.tick_size,
          step_size=excluded.step_size,
          min_order_notional=excluded.min_order_notional,
          raw_json=excluded.raw_json,
          updated_at_ns=excluded.updated_at_ns
        """,
        (
            market.get("marketDisplayName"),
            market.get("marketId"),
            market.get("fullAssetName"),
            market.get("baseAsset"),
            market.get("quoteAsset"),
            market.get("category"),
            market.get("type"),
            market.get("status"),
            market.get("tickSize"),
            market.get("stepSize"),
            market.get("minOrderNotional"),
            json.dumps(market, separators=(",", ":")),
            received_at,
        ),
    )

    conn.execute(
        """
        INSERT INTO market_snapshots(
          market, market_id, status, oracle_price, mark_price, last_trade_price,
          funding_rate, next_funding_rate, next_funding_at, price_change_24h,
          volume_24h, volume_24h_notional, trades_24h, open_interest, received_at_ns, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            market.get("marketDisplayName"),
            market.get("marketId"),
            market.get("status"),
            as_float(market.get("oraclePrice")),
            as_float(market.get("markPrice")),
            as_float(market.get("lastTradePrice")),
            as_float(market.get("fundingRate")),
            as_float(market.get("nextFundingRate")),
            as_int(market.get("nextFundingAt")),
            as_float(market.get("priceChange24h")),
            as_float(market.get("volume24h")),
            as_float(market.get("volume24hNotional")),
            as_int(market.get("trades24h")),
            as_float(market.get("openInterest")),
            received_at,
            json.dumps(market, separators=(",", ":")),
        ),
    )


def store_markets(conn, environment, payload, received_at):
    insert_raw(conn, "rest", environment, "markets", None, payload, received_at)
    for market in payload.get("markets", []):
        upsert_market(conn, market, received_at)


def store_mids(conn, environment, payload, received_at):
    insert_raw(conn, "rest", environment, "mids", None, payload, received_at)
    sequence = as_int(payload.get("globalSequenceId"))
    for market, mid in payload.get("mids", {}).items():
        conn.execute(
            "INSERT INTO mids(market, mid_price, global_sequence_id, received_at_ns) VALUES (?, ?, ?, ?)",
            (market, as_float(mid), sequence, received_at),
        )


def store_candles(conn, environment, market, timeframe, payload, received_at, source="rest"):
    insert_raw(conn, source, environment, "candles", market, payload, received_at)
    for candle in payload.get("candles", []):
        conn.execute(
            """
            INSERT INTO candles(
              market, timeframe, open_time, open, high, low, close, volume,
              notional_volume, trade_count, is_final, received_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(market, timeframe, open_time) DO UPDATE SET
              open=excluded.open,
              high=excluded.high,
              low=excluded.low,
              close=excluded.close,
              volume=excluded.volume,
              notional_volume=excluded.notional_volume,
              trade_count=excluded.trade_count,
              is_final=excluded.is_final,
              received_at_ns=excluded.received_at_ns,
              raw_json=excluded.raw_json
            """,
            (
                candle.get("marketDisplayName") or market,
                candle.get("timeframe") or timeframe,
                as_int(candle.get("openTime")),
                as_float(candle.get("open")),
                as_float(candle.get("high")),
                as_float(candle.get("low")),
                as_float(candle.get("close")),
                as_float(candle.get("volume")),
                as_float(candle.get("notionalVolume")),
                as_int(candle.get("tradeCount")),
                1 if candle.get("isFinal") else 0,
                received_at,
                json.dumps(candle, separators=(",", ":")),
            ),
        )


def level_depth(levels):
    total = 0.0
    for price, size in levels or []:
        p = as_float(price) or 0
        s = as_float(size) or 0
        total += p * s
    return total


def store_orderbook(conn, environment, market, contents, received_at):
    bids = contents.get("bids") or []
    asks = contents.get("asks") or []
    best_bid = bids[0] if bids else [None, None]
    best_ask = asks[0] if asks else [None, None]
    insert_raw(conn, "websocket", environment, "l2Orderbook", market, contents, received_at, contents.get("timestamp"))
    conn.execute(
        """
        INSERT INTO orderbook_snapshots(
          market, last_sequence_id, global_sequence_id, exchange_ts, received_at_ns,
          best_bid_price, best_bid_size, best_ask_price, best_ask_size,
          bid_depth_notional, ask_depth_notional, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            market,
            as_int(contents.get("lastSequenceId")),
            as_int(contents.get("globalSequenceId")),
            as_int(contents.get("timestamp")),
            received_at,
            as_float(best_bid[0]),
            as_float(best_bid[1]),
            as_float(best_ask[0]),
            as_float(best_ask[1]),
            level_depth(bids),
            level_depth(asks),
            json.dumps(contents, separators=(",", ":")),
        ),
    )


def store_bbo(conn, environment, market, contents, received_at):
    bid = contents.get("bestBid") or {}
    ask = contents.get("bestAsk") or {}
    insert_raw(conn, "websocket", environment, "bbo", market, contents, received_at, contents.get("timestamp"))
    conn.execute(
        """
        INSERT INTO bbo(
          market, exchange_ts, received_at_ns, best_bid_price, best_bid_size,
          best_ask_price, best_ask_size, last_sequence_id, global_sequence_id, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            market,
            as_int(contents.get("timestamp")),
            received_at,
            as_float(bid.get("price")),
            as_float(bid.get("size")),
            as_float(ask.get("price")),
            as_float(ask.get("size")),
            as_int(contents.get("lastSequenceId")),
            as_int(contents.get("globalSequenceId")),
            json.dumps(contents, separators=(",", ":")),
        ),
    )


def store_trade(conn, environment, market, contents, received_at):
    trades = contents if isinstance(contents, list) else [contents]
    insert_raw(conn, "websocket", environment, "trades", market, contents, received_at)
    for trade in trades:
        if not isinstance(trade, dict):
            continue
        trade_id = trade.get("id") or trade.get("tradeId")
        conn.execute(
            """
            INSERT OR IGNORE INTO trades(id, market, exchange_ts, received_at_ns, price, size, side, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(trade_id) if trade_id is not None else None,
                trade.get("marketDisplayName") or market,
                as_int(trade.get("timestamp")),
                received_at,
                as_float(trade.get("price")),
                as_float(trade.get("size")),
                trade.get("side") or trade.get("takerSide"),
                json.dumps(trade, separators=(",", ":")),
            ),
        )


def sync_rest_once(conn, config, base_url):
    received_at = now_ns()
    markets_payload = request_json(base_url, "/v1/markets")
    store_markets(conn, config["environment"], markets_payload, received_at)

    mids_payload = request_json(base_url, "/v1/mids")
    store_mids(conn, config["environment"], mids_payload, now_ns())

    to_us = int(time.time() * 1_000_000)
    for market in config["markets"]:
        for timeframe in config["timeframes"]:
            try:
                payload = request_json(
                    base_url,
                    "/v1/candles",
                    {"market": market, "timeframe": timeframe, "to": to_us, "countback": 200},
                )
                store_candles(conn, config["environment"], market, timeframe, payload, now_ns())
            except Exception as exc:
                print(f"REST candle sync failed for {market}/{timeframe}: {exc}", file=sys.stderr)
    conn.commit()


async def rest_loop(conn, config, base_url, stop_event):
    interval = int(config["rest_sync_interval_seconds"])
    while not stop_event.is_set():
        try:
            sync_rest_once(conn, config, base_url)
            print(f"REST sync complete at {time.strftime('%H:%M:%S')}")
        except Exception as exc:
            print(f"REST sync failed: {exc}", file=sys.stderr)
        await asyncio.sleep(interval)


async def websocket_loop(conn, config, ws_url, stop_event):
    try:
        import websockets
    except ImportError:
        print("Missing dependency: run `python3 -m pip install -r collector/requirements.txt`", file=sys.stderr)
        return

    reconnect_seconds = int(config["websocket_reconnect_seconds"])
    environment = config["environment"]
    while not stop_event.is_set():
        try:
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                print(f"WebSocket connected: {ws_url}")
                for market in config["markets"]:
                    if config.get("collect_l2_orderbook", True):
                        await ws.send(json.dumps({
                            "type": "subscribe",
                            "channel": "l2Orderbook",
                            "id": market,
                            "nLevels": int(config["orderbook_levels"]),
                        }))
                    if config.get("collect_bbo", True):
                        await ws.send(json.dumps({"type": "subscribe", "channel": "bbo", "id": market}))
                    if config.get("collect_trades", True):
                        await ws.send(json.dumps({"type": "subscribe", "channel": "trades", "id": market}))
                    if config.get("collect_candles", True):
                        for timeframe in config["timeframes"]:
                            await ws.send(json.dumps({"type": "subscribe", "channel": "candles", "id": f"{market}/{timeframe}"}))

                while not stop_event.is_set():
                    message = await asyncio.wait_for(ws.recv(), timeout=30)
                    received_at = now_ns()
                    payload = json.loads(message)
                    channel = payload.get("channel") or payload.get("type") or "unknown"
                    market_id = payload.get("id")
                    contents = payload.get("contents", payload)

                    if channel == "l2Orderbook":
                        store_orderbook(conn, environment, market_id, contents, received_at)
                    elif channel == "bbo":
                        store_bbo(conn, environment, market_id, contents, received_at)
                    elif channel == "trades":
                        store_trade(conn, environment, market_id, contents, received_at)
                    elif channel == "candles":
                        if "/" in str(market_id):
                            market, timeframe = market_id.split("/", 1)
                        else:
                            market, timeframe = market_id, config["timeframes"][0]
                        if isinstance(contents, dict) and contents.get("isSnapshot"):
                            store_candles(conn, environment, market, timeframe, contents, received_at, source="websocket")
                        elif isinstance(contents, dict):
                            store_candles(conn, environment, market, timeframe, {"candles": [contents]}, received_at, source="websocket")
                    else:
                        insert_raw(conn, "websocket", environment, channel, market_id, payload, received_at)

                    if received_at % 50 < 5:
                        conn.commit()
                conn.commit()
        except asyncio.TimeoutError:
            print("WebSocket timeout; reconnecting", file=sys.stderr)
        except Exception as exc:
            print(f"WebSocket error: {exc}; reconnecting in {reconnect_seconds}s", file=sys.stderr)
            await asyncio.sleep(reconnect_seconds)


async def main_async(args):
    config = load_config(args.config)
    if args.env:
        config["environment"] = args.env
    if args.markets:
        config["markets"] = args.markets.split(",")
    if args.rest_only:
        config["collect_websocket"] = False
    if args.duration:
        config["duration_seconds"] = args.duration

    environment = config["environment"]
    if environment not in ENVIRONMENTS:
        raise SystemExit(f"Unknown environment: {environment}")

    db_path = resolve_database(args.config, config["database"])
    conn = connect_db(db_path)
    run_started = now_ns()
    run_id = conn.execute(
        "INSERT INTO collector_runs(environment, started_at_ns, config_json) VALUES (?, ?, ?)",
        (environment, run_started, json.dumps(config, indent=2)),
    ).lastrowid
    conn.commit()

    print(f"Database: {db_path}")
    print(f"Environment: {environment}")
    print(f"Markets: {', '.join(config['markets'])}")

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    if args.once:
        sync_rest_once(conn, config, ENVIRONMENTS[environment]["rest"])
    else:
        tasks = [asyncio.create_task(rest_loop(conn, config, ENVIRONMENTS[environment]["rest"], stop_event))]
        if config.get("collect_websocket", True):
            tasks.append(asyncio.create_task(websocket_loop(conn, config, ENVIRONMENTS[environment]["ws"], stop_event)))
        if args.duration:
            async def stop_later():
                await asyncio.sleep(args.duration)
                stop_event.set()
            tasks.append(asyncio.create_task(stop_later()))
        await stop_event.wait()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    conn.execute("UPDATE collector_runs SET stopped_at_ns = ? WHERE id = ?", (now_ns(), run_id))
    conn.commit()
    conn.close()
    print("Collector stopped")


def parse_args():
    parser = argparse.ArgumentParser(description="Collect Arcus market data into SQLite.")
    default_config = str(Path(__file__).resolve().parent / "config.example.json")
    parser.add_argument("--config", default=default_config, help="Path to collector JSON config.")
    parser.add_argument("--env", choices=sorted(ENVIRONMENTS.keys()), help="Override environment.")
    parser.add_argument("--markets", help="Comma-separated market list, e.g. BTC-USD,ETH-USD.")
    parser.add_argument("--once", action="store_true", help="Run one REST sync and exit.")
    parser.add_argument("--rest-only", action="store_true", help="Disable WebSocket collection.")
    parser.add_argument("--duration", type=int, help="Run duration in seconds.")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))

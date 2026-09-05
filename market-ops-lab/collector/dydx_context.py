#!/usr/bin/env python3
import argparse
import json
import sqlite3
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_URLS = {
    "mainnet": "https://indexer.dydx.trade/v4",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS dydx_markets (
  ticker TEXT PRIMARY KEY,
  status TEXT,
  oracle_price REAL,
  price_change_24h REAL,
  volume_24h REAL,
  trades_24h INTEGER,
  next_funding_rate REAL,
  open_interest REAL,
  tick_size REAL,
  step_size REAL,
  raw_json TEXT NOT NULL,
  updated_at_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS dydx_orderbook_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  best_bid REAL,
  best_bid_size REAL,
  best_ask REAL,
  best_ask_size REAL,
  mid REAL,
  spread_bps REAL,
  microprice REAL,
  microprice_edge_bps REAL,
  bid_depth_notional REAL,
  ask_depth_notional REAL,
  depth_imbalance REAL,
  slippage_buy_100_bps REAL,
  slippage_sell_100_bps REAL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dydx_orderbook_features_ticker_time
ON dydx_orderbook_features(ticker, received_at_ns);

CREATE TABLE IF NOT EXISTS dydx_trades (
  id TEXT PRIMARY KEY,
  ticker TEXT NOT NULL,
  side TEXT,
  price REAL,
  size REAL,
  notional REAL,
  trade_type TEXT,
  created_at TEXT,
  created_at_ns INTEGER,
  fetched_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_dydx_trades_ticker_time
ON dydx_trades(ticker, created_at_ns);

CREATE TABLE IF NOT EXISTS dydx_trade_flow_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ticker TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  trade_count INTEGER NOT NULL,
  buy_notional REAL NOT NULL,
  sell_notional REAL NOT NULL,
  flow_imbalance REAL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dydx_candles (
  ticker TEXT NOT NULL,
  resolution TEXT NOT NULL,
  started_at TEXT NOT NULL,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  base_volume REAL,
  usd_volume REAL,
  trades INTEGER,
  starting_open_interest REAL,
  orderbook_mid_open REAL,
  orderbook_mid_close REAL,
  fetched_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL,
  PRIMARY KEY (ticker, resolution, started_at)
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
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsDydxContext/0.1"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def as_ns(iso_value):
    if not iso_value:
        return None
    try:
        dt = datetime.fromisoformat(iso_value.replace("Z", "+00:00"))
        return int(dt.timestamp() * 1_000_000_000)
    except ValueError:
        return None


def depth_notional(levels):
    total = 0.0
    for level in levels or []:
        price = num(level.get("price")) or 0.0
        size = num(level.get("size")) or 0.0
        total += price * size
    return total


def slippage_bps(levels, notional, mid):
    remaining = notional
    qty = 0.0
    spent = 0.0
    for level in levels or []:
        price = num(level.get("price"))
        size = num(level.get("size"))
        if not price or not size:
            continue
        level_notional = price * size
        take = min(remaining, level_notional)
        qty += take / price
        spent += take
        remaining -= take
        if remaining <= 1e-9:
            break
    if remaining > 1e-9 or qty <= 0 or not mid:
        return None
    avg_fill = spent / qty
    return abs(avg_fill - mid) / mid * 10_000


def store_markets(conn, payload):
    ts = now_ns()
    for ticker, market in (payload.get("markets") or {}).items():
        conn.execute(
            """
            INSERT INTO dydx_markets(
              ticker, status, oracle_price, price_change_24h, volume_24h,
              trades_24h, next_funding_rate, open_interest, tick_size, step_size,
              raw_json, updated_at_ns
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
              status=excluded.status,
              oracle_price=excluded.oracle_price,
              price_change_24h=excluded.price_change_24h,
              volume_24h=excluded.volume_24h,
              trades_24h=excluded.trades_24h,
              next_funding_rate=excluded.next_funding_rate,
              open_interest=excluded.open_interest,
              tick_size=excluded.tick_size,
              step_size=excluded.step_size,
              raw_json=excluded.raw_json,
              updated_at_ns=excluded.updated_at_ns
            """,
            (
                ticker,
                market.get("status"),
                num(market.get("oraclePrice")),
                num(market.get("priceChange24H")),
                num(market.get("volume24H")),
                int(market.get("trades24H") or 0),
                num(market.get("nextFundingRate")),
                num(market.get("openInterest")),
                num(market.get("tickSize")),
                num(market.get("stepSize")),
                json.dumps(market, separators=(",", ":")),
                ts,
            ),
        )


def store_orderbook(conn, ticker, book):
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    best_bid = bids[0] if bids else {}
    best_ask = asks[0] if asks else {}
    bid = num(best_bid.get("price"))
    ask = num(best_ask.get("price"))
    bid_size = num(best_bid.get("size"))
    ask_size = num(best_ask.get("size"))
    mid = (bid + ask) / 2 if bid and ask else None
    spread = (ask - bid) / mid * 10_000 if mid else None
    micro = None
    micro_edge = None
    if bid and ask and bid_size and ask_size:
        micro = (ask * bid_size + bid * ask_size) / (bid_size + ask_size)
        micro_edge = (micro - mid) / mid * 10_000
    bid_depth = depth_notional(bids)
    ask_depth = depth_notional(asks)
    imb = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) else None
    conn.execute(
        """
        INSERT INTO dydx_orderbook_features(
          ticker, received_at_ns, best_bid, best_bid_size, best_ask, best_ask_size,
          mid, spread_bps, microprice, microprice_edge_bps, bid_depth_notional,
          ask_depth_notional, depth_imbalance, slippage_buy_100_bps,
          slippage_sell_100_bps, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            now_ns(),
            bid,
            bid_size,
            ask,
            ask_size,
            mid,
            spread,
            micro,
            micro_edge,
            bid_depth,
            ask_depth,
            imb,
            slippage_bps(asks, 100.0, mid),
            slippage_bps(bids, 100.0, mid),
            json.dumps(book, separators=(",", ":")),
        ),
    )


def store_trades(conn, ticker, payload):
    fetched = now_ns()
    buy = 0.0
    sell = 0.0
    trades = payload.get("trades") or []
    for trade in trades:
        price = num(trade.get("price")) or 0.0
        size = num(trade.get("size")) or 0.0
        notional = price * size
        side = (trade.get("side") or "").upper()
        if side == "BUY":
            buy += notional
        elif side == "SELL":
            sell += notional
        conn.execute(
            """
            INSERT OR IGNORE INTO dydx_trades(
              id, ticker, side, price, size, notional, trade_type,
              created_at, created_at_ns, fetched_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                trade.get("id"),
                ticker,
                side,
                price,
                size,
                notional,
                trade.get("type"),
                trade.get("createdAt"),
                as_ns(trade.get("createdAt")),
                fetched,
                json.dumps(trade, separators=(",", ":")),
            ),
        )
    denom = buy + sell
    flow = (buy - sell) / denom if denom else None
    conn.execute(
        """
        INSERT INTO dydx_trade_flow_features(
          ticker, received_at_ns, trade_count, buy_notional, sell_notional, flow_imbalance, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (ticker, fetched, len(trades), buy, sell, flow, json.dumps(payload, separators=(",", ":"))),
    )


def store_candles(conn, ticker, resolution, payload):
    fetched = now_ns()
    for candle in payload.get("candles") or []:
        conn.execute(
            """
            INSERT INTO dydx_candles(
              ticker, resolution, started_at, open, high, low, close,
              base_volume, usd_volume, trades, starting_open_interest,
              orderbook_mid_open, orderbook_mid_close, fetched_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(ticker, resolution, started_at) DO UPDATE SET
              open=excluded.open,
              high=excluded.high,
              low=excluded.low,
              close=excluded.close,
              base_volume=excluded.base_volume,
              usd_volume=excluded.usd_volume,
              trades=excluded.trades,
              starting_open_interest=excluded.starting_open_interest,
              orderbook_mid_open=excluded.orderbook_mid_open,
              orderbook_mid_close=excluded.orderbook_mid_close,
              fetched_at_ns=excluded.fetched_at_ns,
              raw_json=excluded.raw_json
            """,
            (
                ticker,
                resolution,
                candle.get("startedAt"),
                num(candle.get("open")),
                num(candle.get("high")),
                num(candle.get("low")),
                num(candle.get("close")),
                num(candle.get("baseTokenVolume")),
                num(candle.get("usdVolume")),
                int(candle.get("trades") or 0),
                num(candle.get("startingOpenInterest")),
                num(candle.get("orderbookMidPriceOpen")),
                num(candle.get("orderbookMidPriceClose")),
                fetched,
                json.dumps(candle, separators=(",", ":")),
            ),
        )


def main():
    args = parse_args()
    base = BASE_URLS[args.env]
    tickers = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    conn = connect_db(args.db)

    if args.markets:
        store_markets(conn, request_json(base, "/perpetualMarkets"))
        print("stored dydx markets")

    for ticker in tickers:
        try:
            if args.orderbook:
                book = request_json(base, f"/orderbooks/perpetualMarket/{ticker}")
                store_orderbook(conn, ticker, book)
            if args.trades:
                trades = request_json(base, f"/trades/perpetualMarket/{ticker}", {"limit": args.trade_limit})
                store_trades(conn, ticker, trades)
            if args.candles:
                candles = request_json(base, f"/candles/perpetualMarkets/{ticker}", {"resolution": args.resolution, "limit": args.candle_limit})
                store_candles(conn, ticker, args.resolution, candles)
            print(f"stored {ticker}")
        except Exception as exc:
            print(f"{ticker}: failed: {exc}")
        time.sleep(args.sleep)

    conn.commit()
    conn.close()


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Collect public dYdX v4 market context into SQLite.")
    parser.add_argument("--env", choices=sorted(BASE_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--tickers", default="BTC-USD,ETH-USD,SOL-USD")
    parser.add_argument("--markets", action="store_true", default=True)
    parser.add_argument("--orderbook", action="store_true", default=True)
    parser.add_argument("--trades", action="store_true", default=True)
    parser.add_argument("--candles", action="store_true", default=True)
    parser.add_argument("--trade-limit", type=int, default=50)
    parser.add_argument("--resolution", default="1MIN")
    parser.add_argument("--candle-limit", type=int, default=120)
    parser.add_argument("--sleep", type=float, default=0.2)
    return parser.parse_args()


if __name__ == "__main__":
    main()

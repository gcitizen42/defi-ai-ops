#!/usr/bin/env python3
import argparse
import json
import math
import sqlite3
import statistics
import time
import urllib.request
from pathlib import Path

BASE_URLS = {
    "mainnet": "https://api.hyperliquid.xyz",
    "testnet": "https://api.hyperliquid-testnet.xyz",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS hyperliquid_markets (
  coin TEXT PRIMARY KEY,
  asset_index INTEGER NOT NULL,
  sz_decimals INTEGER,
  max_leverage INTEGER,
  only_isolated INTEGER,
  mark_price REAL,
  prev_day_price REAL,
  price_change_24h_pct REAL,
  volume_24h_usd REAL,
  open_interest REAL,
  open_interest_usd REAL,
  funding REAL,
  premium REAL,
  raw_meta_json TEXT NOT NULL,
  raw_context_json TEXT NOT NULL,
  updated_at_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS hyperliquid_orderbook_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  coin TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  exchange_time_ms INTEGER,
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
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hl_orderbook_coin_time
ON hyperliquid_orderbook_features(coin, received_at_ns);

CREATE TABLE IF NOT EXISTS hyperliquid_trades (
  tid TEXT PRIMARY KEY,
  coin TEXT NOT NULL,
  side TEXT,
  price REAL,
  size REAL,
  notional REAL,
  trade_time_ms INTEGER,
  fetched_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hl_trades_coin_time
ON hyperliquid_trades(coin, trade_time_ms);

CREATE TABLE IF NOT EXISTS hyperliquid_trade_flow_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  coin TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  trade_count INTEGER NOT NULL,
  buy_notional REAL NOT NULL,
  sell_notional REAL NOT NULL,
  flow_imbalance REAL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS hyperliquid_candles (
  coin TEXT NOT NULL,
  interval TEXT NOT NULL,
  open_time_ms INTEGER NOT NULL,
  close_time_ms INTEGER,
  open REAL,
  high REAL,
  low REAL,
  close REAL,
  volume REAL,
  trade_count INTEGER,
  fetched_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL,
  PRIMARY KEY (coin, interval, open_time_ms)
);

CREATE TABLE IF NOT EXISTS hyperliquid_scan_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  scanned_at_ns INTEGER NOT NULL,
  coin TEXT NOT NULL,
  side TEXT NOT NULL,
  verdict TEXT NOT NULL,
  entry REAL,
  take_profit REAL,
  stop_loss REAL,
  target_pct REAL,
  stop_pct REAL,
  reward_risk REAL,
  confidence REAL,
  score REAL,
  price_change_24h_pct REAL,
  volume_24h_usd REAL,
  open_interest_usd REAL,
  spread_bps REAL,
  depth_imbalance REAL,
  flow_imbalance REAL,
  reject_reasons TEXT NOT NULL,
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


def num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def post_json(base_url, payload):
    req = urllib.request.Request(
        f"{base_url}/info",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "accept": "application/json",
            "user-agent": "RobinhoodOpsHyperliquidContext/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_meta_and_context(base_url):
    payload = post_json(base_url, {"type": "metaAndAssetCtxs"})
    if not isinstance(payload, list) or len(payload) != 2:
        raise RuntimeError("Unexpected metaAndAssetCtxs response")
    return payload[0], payload[1]


def store_markets(conn, meta, contexts):
    ts = now_ns()
    rows = []
    for idx, (market, ctx) in enumerate(zip(meta.get("universe") or [], contexts or [])):
        coin = market.get("name")
        mark = num(ctx.get("markPx"))
        prev = num(ctx.get("prevDayPx"))
        change = ((mark / prev) - 1) * 100 if mark and prev else None
        oi = num(ctx.get("openInterest"))
        oi_usd = oi * mark if oi is not None and mark is not None else None
        row = (
            coin,
            idx,
            int(market.get("szDecimals") or 0),
            int(market.get("maxLeverage") or 0),
            1 if market.get("onlyIsolated") else 0,
            mark,
            prev,
            change,
            num(ctx.get("dayNtlVlm")),
            oi,
            oi_usd,
            num(ctx.get("funding")),
            num(ctx.get("premium")),
            json.dumps(market, separators=(",", ":")),
            json.dumps(ctx, separators=(",", ":")),
            ts,
        )
        rows.append(row)
        conn.execute(
            """
            INSERT INTO hyperliquid_markets(
              coin, asset_index, sz_decimals, max_leverage, only_isolated,
              mark_price, prev_day_price, price_change_24h_pct, volume_24h_usd,
              open_interest, open_interest_usd, funding, premium,
              raw_meta_json, raw_context_json, updated_at_ns
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin) DO UPDATE SET
              asset_index=excluded.asset_index,
              sz_decimals=excluded.sz_decimals,
              max_leverage=excluded.max_leverage,
              only_isolated=excluded.only_isolated,
              mark_price=excluded.mark_price,
              prev_day_price=excluded.prev_day_price,
              price_change_24h_pct=excluded.price_change_24h_pct,
              volume_24h_usd=excluded.volume_24h_usd,
              open_interest=excluded.open_interest,
              open_interest_usd=excluded.open_interest_usd,
              funding=excluded.funding,
              premium=excluded.premium,
              raw_meta_json=excluded.raw_meta_json,
              raw_context_json=excluded.raw_context_json,
              updated_at_ns=excluded.updated_at_ns
            """,
            row,
        )
    return rows


def depth_notional(levels):
    return sum((num(level.get("px")) or 0.0) * (num(level.get("sz")) or 0.0) for level in levels)


def store_orderbook(conn, base_url, coin, levels):
    payload = post_json(base_url, {"type": "l2Book", "coin": coin})
    bids, asks = (payload.get("levels") or [[], []])[:2]
    best_bid = bids[0] if bids else {}
    best_ask = asks[0] if asks else {}
    bid = num(best_bid.get("px"))
    ask = num(best_ask.get("px"))
    bid_size = num(best_bid.get("sz"))
    ask_size = num(best_ask.get("sz"))
    mid = (bid + ask) / 2 if bid and ask else None
    spread = (ask - bid) / mid * 10_000 if mid else None
    bid_depth = depth_notional(bids[:levels])
    ask_depth = depth_notional(asks[:levels])
    imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if bid_depth + ask_depth else None
    micro = (ask * bid_size + bid * ask_size) / (bid_size + ask_size) if bid and ask and bid_size and ask_size else None
    micro_edge = (micro - mid) / mid * 10_000 if micro and mid else None
    row = {
        "coin": coin,
        "received_at_ns": now_ns(),
        "exchange_time_ms": int(payload.get("time") or 0),
        "best_bid": bid,
        "best_bid_size": bid_size,
        "best_ask": ask,
        "best_ask_size": ask_size,
        "mid": mid,
        "spread_bps": spread,
        "microprice": micro,
        "microprice_edge_bps": micro_edge,
        "bid_depth_notional": bid_depth,
        "ask_depth_notional": ask_depth,
        "depth_imbalance": imbalance,
        "raw_json": json.dumps(payload, separators=(",", ":")),
    }
    conn.execute(
        """
        INSERT INTO hyperliquid_orderbook_features(
          coin, received_at_ns, exchange_time_ms, best_bid, best_bid_size,
          best_ask, best_ask_size, mid, spread_bps, microprice,
          microprice_edge_bps, bid_depth_notional, ask_depth_notional,
          depth_imbalance, raw_json
        )
        VALUES (:coin, :received_at_ns, :exchange_time_ms, :best_bid, :best_bid_size,
          :best_ask, :best_ask_size, :mid, :spread_bps, :microprice,
          :microprice_edge_bps, :bid_depth_notional, :ask_depth_notional,
          :depth_imbalance, :raw_json)
        """,
        row,
    )
    return row


def store_trades(conn, base_url, coin, limit):
    payload = post_json(base_url, {"type": "recentTrades", "coin": coin})
    ts = now_ns()
    buy_notional = 0.0
    sell_notional = 0.0
    count = 0
    used = payload[:limit] if isinstance(payload, list) else []
    for trade in used:
        price = num(trade.get("px"))
        size = num(trade.get("sz"))
        notional = (price or 0.0) * (size or 0.0)
        side = trade.get("side")
        if side == "B":
            buy_notional += notional
        elif side in ("A", "S"):
            sell_notional += notional
        tid = str(trade.get("tid") or trade.get("hash") or f"{coin}:{trade.get('time')}:{count}")
        conn.execute(
            """
            INSERT OR IGNORE INTO hyperliquid_trades(
              tid, coin, side, price, size, notional, trade_time_ms, fetched_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                tid,
                coin,
                side,
                price,
                size,
                notional,
                int(trade.get("time") or 0),
                ts,
                json.dumps(trade, separators=(",", ":")),
            ),
        )
        count += 1
    flow = (buy_notional - sell_notional) / (buy_notional + sell_notional) if buy_notional + sell_notional else None
    row = {
        "coin": coin,
        "received_at_ns": ts,
        "trade_count": count,
        "buy_notional": buy_notional,
        "sell_notional": sell_notional,
        "flow_imbalance": flow,
        "raw_json": json.dumps(used, separators=(",", ":")),
    }
    conn.execute(
        """
        INSERT INTO hyperliquid_trade_flow_features(
          coin, received_at_ns, trade_count, buy_notional, sell_notional, flow_imbalance, raw_json
        )
        VALUES (:coin, :received_at_ns, :trade_count, :buy_notional, :sell_notional, :flow_imbalance, :raw_json)
        """,
        row,
    )
    return row


def store_candles(conn, base_url, coin, interval, lookback_minutes):
    end_ms = int(time.time() * 1000)
    start_ms = end_ms - lookback_minutes * 60_000
    payload = post_json(
        base_url,
        {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval": interval,
                "startTime": start_ms,
                "endTime": end_ms,
            },
        },
    )
    ts = now_ns()
    rows = []
    for candle in payload if isinstance(payload, list) else []:
        row = (
            coin,
            interval,
            int(candle.get("t") or 0),
            int(candle.get("T") or 0),
            num(candle.get("o")),
            num(candle.get("h")),
            num(candle.get("l")),
            num(candle.get("c")),
            num(candle.get("v")),
            int(candle.get("n") or 0),
            ts,
            json.dumps(candle, separators=(",", ":")),
        )
        conn.execute(
            """
            INSERT INTO hyperliquid_candles(
              coin, interval, open_time_ms, close_time_ms, open, high, low, close,
              volume, trade_count, fetched_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(coin, interval, open_time_ms) DO UPDATE SET
              close_time_ms=excluded.close_time_ms,
              open=excluded.open,
              high=excluded.high,
              low=excluded.low,
              close=excluded.close,
              volume=excluded.volume,
              trade_count=excluded.trade_count,
              fetched_at_ns=excluded.fetched_at_ns,
              raw_json=excluded.raw_json
            """,
            row,
        )
        rows.append(row)
    return rows


def pct(a, b):
    return ((b / a) - 1) * 100 if a else 0.0


def evaluate_candidate(market, book, flow, candles):
    closes = [row[7] for row in candles if row[7]]
    highs = [row[5] for row in candles if row[5]]
    lows = [row[6] for row in candles if row[6]]
    if len(closes) < 30:
        return None
    last = closes[-1]
    r1 = pct(closes[-2], last)
    r5 = pct(closes[-6], last) if len(closes) > 6 else 0.0
    r15 = pct(closes[-16], last) if len(closes) > 16 else 0.0
    r60 = pct(closes[-61], last) if len(closes) > 61 else 0.0
    tr = [
        (highs[i] - lows[i]) / closes[i] * 100
        for i in range(max(0, len(closes) - min(60, len(closes))), len(closes))
        if closes[i]
    ]
    atr_pct = sum(tr) / len(tr) if tr else 0.0
    trend = 0.48 * r15 + 0.30 * r60 + 0.17 * r5 + 0.05 * r1
    micro = 0.0
    if book.get("depth_imbalance") is not None:
        micro += 0.35 * book["depth_imbalance"]
    if book.get("microprice_edge_bps") is not None:
        micro += 0.05 * book["microprice_edge_bps"]
    if flow.get("flow_imbalance") is not None:
        micro += 0.45 * flow["flow_imbalance"]
    score = trend + micro
    side = "long" if score >= 0 else "short"
    spread_cost_pct = (book.get("spread_bps") or 999.0) / 100
    target_pct = max(0.55, min(3.5, atr_pct * 10 + abs(r15) * 0.45 + abs(r60) * 0.10))
    stop_pct = max(0.35, min(1.6, atr_pct * 6 + spread_cost_pct * 1.5))
    reward_risk = target_pct / stop_pct if stop_pct else 0.0
    confidence = (
        0.48
        + min(0.22, abs(score) * 0.06)
        + min(0.08, abs(flow.get("flow_imbalance") or 0.0) * 0.12)
        + min(0.05, abs(book.get("depth_imbalance") or 0.0) * 0.08)
        - min(0.18, spread_cost_pct / max(target_pct, 0.01) * 0.9)
    )
    rejects = []
    if (book.get("spread_bps") or 999.0) > 12:
        rejects.append(f"wide spread {book.get('spread_bps'):.2f}bps")
    if spread_cost_pct > target_pct * 0.18:
        rejects.append("spread too large vs target")
    if reward_risk < 1.45:
        rejects.append(f"low reward/risk {reward_risk:.2f}")
    if abs(score) < 1.0:
        rejects.append("weak combined signal")
    if side == "long" and r15 < 0 and (flow.get("flow_imbalance") or 0.0) < 0:
        rejects.append("falling with sell flow")
    if side == "short" and r15 > 0 and (flow.get("flow_imbalance") or 0.0) > 0:
        rejects.append("rising with buy flow")
    entry = book["best_ask"] if side == "long" else book["best_bid"]
    take_profit = entry * (1 + target_pct / 100) if side == "long" else entry * (1 - target_pct / 100)
    stop_loss = entry * (1 - stop_pct / 100) if side == "long" else entry * (1 + stop_pct / 100)
    verdict = "candidate" if not rejects and confidence >= 0.58 else "watch" if len(rejects) <= 1 and confidence >= 0.54 else "reject"
    return {
        "coin": market[0],
        "side": side,
        "verdict": verdict,
        "entry": entry,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        "target_pct": target_pct,
        "stop_pct": stop_pct,
        "reward_risk": reward_risk,
        "confidence": confidence,
        "score": score,
        "r1_pct": r1,
        "r5_pct": r5,
        "r15_pct": r15,
        "r60_pct": r60,
        "atr_1m_pct": atr_pct,
        "price_change_24h_pct": market[7],
        "volume_24h_usd": market[8],
        "open_interest_usd": market[10],
        "funding": market[11],
        "spread_bps": book.get("spread_bps"),
        "depth_imbalance": book.get("depth_imbalance"),
        "flow_imbalance": flow.get("flow_imbalance"),
        "reject_reasons": rejects,
    }


def store_scan(conn, result):
    row = dict(result)
    row["scanned_at_ns"] = now_ns()
    row["reject_reasons"] = json.dumps(row["reject_reasons"], separators=(",", ":"))
    row["raw_json"] = json.dumps(result, separators=(",", ":"))
    conn.execute(
        """
        INSERT INTO hyperliquid_scan_results(
          scanned_at_ns, coin, side, verdict, entry, take_profit, stop_loss,
          target_pct, stop_pct, reward_risk, confidence, score,
          price_change_24h_pct, volume_24h_usd, open_interest_usd,
          spread_bps, depth_imbalance, flow_imbalance, reject_reasons, raw_json
        )
        VALUES (
          :scanned_at_ns, :coin, :side, :verdict, :entry, :take_profit, :stop_loss,
          :target_pct, :stop_pct, :reward_risk, :confidence, :score,
          :price_change_24h_pct, :volume_24h_usd, :open_interest_usd,
          :spread_bps, :depth_imbalance, :flow_imbalance, :reject_reasons, :raw_json
        )
        """,
        row,
    )


def market_rank(row):
    change = abs(row[7] or 0.0)
    volume = row[8] or 0.0
    oi_usd = row[10] or 0.0
    return change * 0.5 + math.log10(max(volume, 1.0)) * 0.6 + math.log10(max(oi_usd, 1.0)) * 0.2


def run(args):
    base_url = BASE_URLS[args.env]
    conn = connect_db(args.db)
    meta, contexts = get_meta_and_context(base_url)
    markets = store_markets(conn, meta, contexts)
    conn.commit()
    if args.markets:
        selected = [m for m in markets if m[0] in {coin.strip() for coin in args.markets.split(",") if coin.strip()}]
    else:
        selected = [
            m for m in sorted(markets, key=market_rank, reverse=True)
            if (m[8] or 0.0) >= args.min_volume_usd and (m[5] or 0.0) > 0
        ][: args.limit]
    results = []
    for market in selected:
        coin = market[0]
        book = store_orderbook(conn, base_url, coin, args.levels)
        flow = store_trades(conn, base_url, coin, args.trade_limit)
        candles = store_candles(conn, base_url, coin, args.interval, args.lookback_minutes)
        candidate = evaluate_candidate(market, book, flow, candles)
        if candidate:
            store_scan(conn, candidate)
            results.append(candidate)
        conn.commit()
        if args.sleep:
            time.sleep(args.sleep)
    conn.close()
    results.sort(key=lambda item: ({"candidate": 0, "watch": 1, "reject": 2}[item["verdict"]], -item["confidence"], -abs(item["score"])))
    print(json.dumps(results, indent=2))


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Collect and scan Hyperliquid public perp context.")
    parser.add_argument("--env", choices=BASE_URLS.keys(), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--markets", help="Comma-separated Hyperliquid coins, e.g. BTC,ETH,SOL.")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--min-volume-usd", type=float, default=3_000_000)
    parser.add_argument("--levels", type=int, default=20)
    parser.add_argument("--trade-limit", type=int, default=100)
    parser.add_argument("--interval", default="1m")
    parser.add_argument("--lookback-minutes", type=int, default=240)
    parser.add_argument("--sleep", type=float, default=0.15)
    return parser.parse_args()


if __name__ == "__main__":
    run(parse_args())

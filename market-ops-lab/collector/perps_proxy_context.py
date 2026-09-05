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
CREATE TABLE IF NOT EXISTS related_market_clusters (
  cluster_name TEXT PRIMARY KEY,
  leaders_json TEXT NOT NULL,
  members_json TEXT NOT NULL,
  updated_at_ns INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS perps_proxy_features (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  market TEXT NOT NULL,
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
  trade_buy_notional REAL,
  trade_sell_notional REAL,
  trade_flow_imbalance REAL,
  trade_count INTEGER,
  last_sequence_id INTEGER,
  global_sequence_id INTEGER,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_perps_proxy_features_market_time
ON perps_proxy_features(market, received_at_ns);
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
    req = urllib.request.Request(url, headers={"accept": "application/json", "user-agent": "RobinhoodOpsPerpsProxy/0.1"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def number(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def depth_notional(levels):
    total = 0.0
    for price_raw, size_raw in levels or []:
        price = number(price_raw) or 0.0
        size = number(size_raw) or 0.0
        total += price * size
    return total


def slippage_bps(levels, notional, mid):
    remaining = notional
    filled_qty = 0.0
    spent = 0.0
    for price_raw, size_raw in levels or []:
        price = number(price_raw)
        size = number(size_raw)
        if not price or not size:
            continue
        level_notional = price * size
        take = min(remaining, level_notional)
        spent += take
        filled_qty += take / price
        remaining -= take
        if remaining <= 1e-9:
            break
    if remaining > 1e-9 or filled_qty <= 0 or not mid:
        return None
    avg_fill = spent / filled_qty
    return abs(avg_fill - mid) / mid * 10_000


def trade_flow(trades):
    buy = 0.0
    sell = 0.0
    for trade in trades:
        price = number(trade.get("price")) or 0.0
        size = number(trade.get("size")) or 0.0
        notional = price * size
        side = (trade.get("side") or "").upper()
        if side == "BUY":
            buy += notional
        elif side == "SELL":
            sell += notional
    denom = buy + sell
    imbalance = (buy - sell) / denom if denom else None
    return buy, sell, imbalance


def compute_market_features(base_url, market, levels, trade_limit):
    book = request_json(base_url, f"/v1/l2OrderBook/{market}", {"nLevels": levels})
    bbo = request_json(base_url, f"/v1/bbo/{market}")
    trades_payload = request_json(base_url, "/v1/trades", {"market": market, "limit": trade_limit})
    trades = trades_payload.get("trades") or []

    bids = book.get("bids") or []
    asks = book.get("asks") or []
    best_bid = number((bids[0] if bids else [None, None])[0])
    best_bid_size = number((bids[0] if bids else [None, None])[1])
    best_ask = number((asks[0] if asks else [None, None])[0])
    best_ask_size = number((asks[0] if asks else [None, None])[1])
    mid = (best_bid + best_ask) / 2 if best_bid and best_ask else None
    spread_bps = (best_ask - best_bid) / mid * 10_000 if mid else None
    microprice = None
    microprice_edge_bps = None
    if best_bid and best_ask and best_bid_size and best_ask_size:
        microprice = (best_ask * best_bid_size + best_bid * best_ask_size) / (best_bid_size + best_ask_size)
        microprice_edge_bps = (microprice - mid) / mid * 10_000 if mid else None

    bid_depth = depth_notional(bids)
    ask_depth = depth_notional(asks)
    depth_imbalance = (bid_depth - ask_depth) / (bid_depth + ask_depth) if (bid_depth + ask_depth) else None
    buy_notional, sell_notional, flow_imbalance = trade_flow(trades)

    return {
        "book": book,
        "bbo": bbo,
        "trades": trades,
        "features": {
            "best_bid": best_bid,
            "best_bid_size": best_bid_size,
            "best_ask": best_ask,
            "best_ask_size": best_ask_size,
            "mid": mid,
            "spread_bps": spread_bps,
            "microprice": microprice,
            "microprice_edge_bps": microprice_edge_bps,
            "bid_depth_notional": bid_depth,
            "ask_depth_notional": ask_depth,
            "depth_imbalance": depth_imbalance,
            "slippage_buy_100_bps": slippage_bps(asks, 100.0, mid),
            "slippage_sell_100_bps": slippage_bps(bids, 100.0, mid),
            "trade_buy_notional": buy_notional,
            "trade_sell_notional": sell_notional,
            "trade_flow_imbalance": flow_imbalance,
            "trade_count": len(trades),
            "last_sequence_id": book.get("lastSequenceId"),
            "global_sequence_id": book.get("globalSequenceId"),
        },
    }


def store_clusters(conn, config):
    updated_at = now_ns()
    for name, cluster in (config.get("clusters") or {}).items():
        conn.execute(
            """
            INSERT INTO related_market_clusters(cluster_name, leaders_json, members_json, updated_at_ns)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(cluster_name) DO UPDATE SET
              leaders_json=excluded.leaders_json,
              members_json=excluded.members_json,
              updated_at_ns=excluded.updated_at_ns
            """,
            (
                name,
                json.dumps(cluster.get("leaders") or [], separators=(",", ":")),
                json.dumps(cluster.get("members") or [], separators=(",", ":")),
                updated_at,
            ),
        )


def store_features(conn, environment, market, payload):
    f = payload["features"]
    conn.execute(
        """
        INSERT INTO perps_proxy_features(
          environment, market, received_at_ns, best_bid, best_bid_size, best_ask,
          best_ask_size, mid, spread_bps, microprice, microprice_edge_bps,
          bid_depth_notional, ask_depth_notional, depth_imbalance,
          slippage_buy_100_bps, slippage_sell_100_bps, trade_buy_notional,
          trade_sell_notional, trade_flow_imbalance, trade_count,
          last_sequence_id, global_sequence_id, raw_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            environment,
            market,
            now_ns(),
            f["best_bid"],
            f["best_bid_size"],
            f["best_ask"],
            f["best_ask_size"],
            f["mid"],
            f["spread_bps"],
            f["microprice"],
            f["microprice_edge_bps"],
            f["bid_depth_notional"],
            f["ask_depth_notional"],
            f["depth_imbalance"],
            f["slippage_buy_100_bps"],
            f["slippage_sell_100_bps"],
            f["trade_buy_notional"],
            f["trade_sell_notional"],
            f["trade_flow_imbalance"],
            f["trade_count"],
            f["last_sequence_id"],
            f["global_sequence_id"],
            json.dumps(payload, separators=(",", ":")),
        ),
    )


def main():
    args = parse_args()
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    markets = [m.strip() for m in (args.markets.split(",") if args.markets else config.get("perps_proxy_markets", [])) if m.strip()]
    conn = connect_db(args.db)
    store_clusters(conn, config)
    base_url = REST_URLS[args.env]
    rows = []
    for market in markets:
        try:
            payload = compute_market_features(base_url, market, args.levels, args.trade_limit)
            store_features(conn, args.env, market, payload)
            f = payload["features"]
            rows.append((market, f["spread_bps"], f["depth_imbalance"], f["microprice_edge_bps"], f["trade_flow_imbalance"]))
            print(
                f"{market}: spread={fmt(f['spread_bps'])}bps depth_imb={fmt(f['depth_imbalance'])} "
                f"micro_edge={fmt(f['microprice_edge_bps'])}bps flow={fmt(f['trade_flow_imbalance'])}"
            )
        except Exception as exc:
            print(f"{market}: failed: {exc}")
        time.sleep(args.sleep)
    conn.commit()
    conn.close()
    print(f"stored {len(rows)} perps proxy feature rows")


def fmt(value):
    return "n/a" if value is None else f"{value:.4f}"


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    default_config = Path(__file__).resolve().parent / "market_context_config.json"
    parser = argparse.ArgumentParser(description="Collect perps L2/trade pressure features as spot proxy context.")
    parser.add_argument("--env", choices=sorted(REST_URLS.keys()), default="mainnet")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--config", default=str(default_config))
    parser.add_argument("--markets", help="Comma-separated perps markets. Defaults to config.")
    parser.add_argument("--levels", type=int, default=20)
    parser.add_argument("--trade-limit", type=int, default=50)
    parser.add_argument("--sleep", type=float, default=0.25)
    return parser.parse_args()


if __name__ == "__main__":
    main()

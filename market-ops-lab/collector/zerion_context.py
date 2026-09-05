#!/usr/bin/env python3
import argparse
import base64
import json
import os
import sqlite3
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

BASE_URL = "https://api.zerion.io/v1"

SCHEMA = """
CREATE TABLE IF NOT EXISTS zerion_wallet_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wallet_address TEXT NOT NULL,
  endpoint TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  raw_json TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_zerion_wallet_snapshots_wallet_time
ON zerion_wallet_snapshots(wallet_address, received_at_ns);

CREATE TABLE IF NOT EXISTS zerion_portfolio (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wallet_address TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  total_value REAL,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS zerion_positions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  wallet_address TEXT NOT NULL,
  received_at_ns INTEGER NOT NULL,
  position_id TEXT,
  position_type TEXT,
  name TEXT,
  symbol TEXT,
  quantity REAL,
  value REAL,
  chain TEXT,
  raw_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS zerion_transactions (
  id TEXT PRIMARY KEY,
  wallet_address TEXT NOT NULL,
  mined_at TEXT,
  operation_type TEXT,
  status TEXT,
  chain TEXT,
  received_at_ns INTEGER NOT NULL,
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


def auth_header(api_key):
    token = base64.b64encode(f"{api_key}:".encode("utf-8")).decode("ascii")
    return f"Basic {token}"


def request_json(path, api_key, params=None):
    url = f"{BASE_URL}{path}"
    if params:
        url = f"{url}?{urllib.parse.urlencode(params, doseq=True)}"
    req = urllib.request.Request(
        url,
        headers={
            "accept": "application/json",
            "authorization": auth_header(api_key),
            "user-agent": "RobinhoodOpsZerionContext/0.1",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def num(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def attr(item, *names):
    attrs = item.get("attributes") or {}
    for name in names:
        if name in attrs:
            return attrs[name]
    return None


def rel_chain(item):
    rel = item.get("relationships") or {}
    chain = rel.get("chain") or {}
    data = chain.get("data") or {}
    return data.get("id")


def store_snapshot(conn, address, endpoint, payload, received_at):
    conn.execute(
        "INSERT INTO zerion_wallet_snapshots(wallet_address, endpoint, received_at_ns, raw_json) VALUES (?, ?, ?, ?)",
        (address, endpoint, received_at, json.dumps(payload, separators=(",", ":"))),
    )


def store_portfolio(conn, address, payload, received_at):
    store_snapshot(conn, address, "portfolio", payload, received_at)
    data = payload.get("data") or {}
    total_value = attr(data, "total", "total_value", "value")
    if isinstance(total_value, dict):
        total_value = total_value.get("positions") or total_value.get("value") or total_value.get("total")
    conn.execute(
        "INSERT INTO zerion_portfolio(wallet_address, received_at_ns, total_value, raw_json) VALUES (?, ?, ?, ?)",
        (address, received_at, num(total_value), json.dumps(payload, separators=(",", ":"))),
    )


def store_positions(conn, address, payload, received_at):
    store_snapshot(conn, address, "positions", payload, received_at)
    for item in payload.get("data") or []:
        attrs = item.get("attributes") or {}
        fungible_info = attrs.get("fungible_info") or {}
        quantity = attrs.get("quantity") or {}
        value = attrs.get("value")
        if isinstance(value, dict):
            value = value.get("value")
        conn.execute(
            """
            INSERT INTO zerion_positions(
              wallet_address, received_at_ns, position_id, position_type, name,
              symbol, quantity, value, chain, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                address,
                received_at,
                item.get("id"),
                item.get("type"),
                fungible_info.get("name") or attrs.get("name"),
                fungible_info.get("symbol") or attrs.get("symbol"),
                num(quantity.get("float") if isinstance(quantity, dict) else quantity),
                num(value),
                rel_chain(item),
                json.dumps(item, separators=(",", ":")),
            ),
        )


def store_transactions(conn, address, payload, received_at):
    store_snapshot(conn, address, "transactions", payload, received_at)
    for item in payload.get("data") or []:
        attrs = item.get("attributes") or {}
        conn.execute(
            """
            INSERT OR REPLACE INTO zerion_transactions(
              id, wallet_address, mined_at, operation_type, status, chain, received_at_ns, raw_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.get("id"),
                address,
                attrs.get("mined_at"),
                attrs.get("operation_type"),
                attrs.get("status"),
                rel_chain(item),
                received_at,
                json.dumps(item, separators=(",", ":")),
            ),
        )


def main():
    args = parse_args()
    secrets = load_env_file(args.env_file)
    api_key = args.api_key or os.environ.get("ZERION_API_KEY") or secrets.get("ZERION_API_KEY")
    address = args.address or os.environ.get("ZERION_WALLET_ADDRESS") or secrets.get("ZERION_WALLET_ADDRESS")
    if not api_key:
        raise SystemExit(f"Missing ZERION_API_KEY. Add it to {args.env_file}")
    if not address:
        raise SystemExit("Missing wallet address.")

    conn = connect_db(args.db)
    received_at = now_ns()

    try:
        if args.portfolio:
            payload = request_json(f"/wallets/{address}/portfolio", api_key, {"filter[positions]": args.positions_filter})
            store_portfolio(conn, address, payload, received_at)
            print("stored zerion portfolio")
        if args.positions:
            payload = request_json(f"/wallets/{address}/positions", api_key, {"filter[positions]": args.positions_filter})
            store_positions(conn, address, payload, received_at)
            print(f"stored zerion positions: {len(payload.get('data') or [])}")
        if args.transactions:
            payload = request_json(f"/wallets/{address}/transactions", api_key, {"page[size]": args.transaction_limit})
            store_transactions(conn, address, payload, received_at)
            print(f"stored zerion transactions: {len(payload.get('data') or [])}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Zerion HTTP {exc.code}: {body[:500]}")
    finally:
        conn.commit()
        conn.close()


def parse_args():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Collect Zerion wallet context into SQLite.")
    parser.add_argument("--db", default=str(root / "data" / "arcus.sqlite"))
    parser.add_argument("--env-file", default=str(root / "secrets" / "zerion.env"))
    parser.add_argument("--api-key")
    parser.add_argument("--address")
    parser.add_argument("--positions-filter", default="only_simple")
    parser.add_argument("--transaction-limit", type=int, default=25)
    parser.add_argument("--portfolio", action="store_true", default=True)
    parser.add_argument("--positions", action="store_true", default=True)
    parser.add_argument("--transactions", action="store_true", default=True)
    return parser.parse_args()


if __name__ == "__main__":
    main()

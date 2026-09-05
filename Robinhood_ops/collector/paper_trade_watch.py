#!/usr/bin/env python3
import argparse
import asyncio
import json
import re
import signal
import sqlite3
import time
from pathlib import Path

ENVIRONMENTS = {
    "mainnet": "wss://api.arcus.xyz/v1/ws",
    "testnet": "wss://api.testnet.arcus.xyz/v1/ws",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS paper_trade_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  environment TEXT NOT NULL,
  market TEXT NOT NULL,
  side TEXT NOT NULL,
  notional_usd REAL NOT NULL,
  target_bps REAL NOT NULL,
  stop_bps REAL NOT NULL,
  timeout_seconds INTEGER NOT NULL,
  entry_price REAL,
  exit_price REAL,
  quantity REAL,
  gross_pnl_usd REAL,
  gross_pnl_bps REAL,
  exit_reason TEXT,
  started_at_ns INTEGER NOT NULL,
  entered_at_ns INTEGER,
  exited_at_ns INTEGER,
  raw_json TEXT
);

CREATE TABLE IF NOT EXISTS paper_trade_ticks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id INTEGER NOT NULL,
  received_at_ns INTEGER NOT NULL,
  best_bid REAL,
  best_bid_size REAL,
  best_ask REAL,
  best_ask_size REAL,
  mid REAL,
  unrealized_pnl_usd REAL,
  unrealized_pnl_bps REAL,
  raw_json TEXT NOT NULL
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


def connect_db(path):
    db_path = Path(path).resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.executescript(SCHEMA)
    return conn


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


def validate_preflight(args):
    checks = []
    secrets = load_env_file(args.env_file)
    api_key = secrets.get("ARCUS_API_KEY") or ""
    private_key = secrets.get("ARCUS_ED25519_PRIVATE_KEY") or ""
    address = secrets.get("ARCUS_ADDRESS") or ""

    checks.append(("api_key_file", Path(args.env_file).exists()))
    checks.append(("api_key_present", bool(api_key)))
    checks.append(("api_key_64_hex_public_key", bool(re.fullmatch(r"[0-9a-fA-F]{64}", api_key))))
    checks.append(("address_present_for_account_reads", bool(address)))
    checks.append(("address_format_if_present", (not address) or bool(re.fullmatch(r"(0x|0X)?[0-9a-fA-F]{40}", address))))
    checks.append(("private_key_present_for_signed_orders", bool(private_key)))

    print("preflight:")
    for name, ok in checks:
        print(f"  {'ok' if ok else 'missing'} {name}")

    if args.require_auth and not all(ok for _, ok in checks):
        raise SystemExit("Authenticated order preflight failed. This runner will not place orders.")


def simulate_market_fill(levels, notional_usd):
    remaining = float(notional_usd)
    filled_qty = 0.0
    spent = 0.0
    for price_raw, size_raw in levels:
        price = as_float(price_raw)
        size = as_float(size_raw)
        if not price or not size:
            continue
        level_notional = price * size
        take_notional = min(remaining, level_notional)
        take_qty = take_notional / price
        filled_qty += take_qty
        spent += take_notional
        remaining -= take_notional
        if remaining <= 0.00000001:
            break
    if remaining > 0.00000001 or filled_qty <= 0:
        return None
    return {
        "avg_price": spent / filled_qty,
        "quantity": filled_qty,
        "notional": spent,
    }


def top_of_book(book):
    bids = book.get("bids") or []
    asks = book.get("asks") or []
    if not bids or not asks:
        return None
    best_bid = [as_float(bids[0][0]), as_float(bids[0][1])]
    best_ask = [as_float(asks[0][0]), as_float(asks[0][1])]
    if not best_bid[0] or not best_ask[0]:
        return None
    return {
        "best_bid": best_bid[0],
        "best_bid_size": best_bid[1],
        "best_ask": best_ask[0],
        "best_ask_size": best_ask[1],
        "mid": (best_bid[0] + best_ask[0]) / 2,
    }


def pnl(side, entry_price, exit_price, quantity):
    if side == "long":
        return (exit_price - entry_price) * quantity
    return (entry_price - exit_price) * quantity


def exit_price_from_book(side, book, quantity):
    levels = book.get("bids") if side == "long" else book.get("asks")
    if not levels:
        return None
    remaining_qty = quantity
    notional = 0.0
    for price_raw, size_raw in levels:
        price = as_float(price_raw)
        size = as_float(size_raw)
        if not price or not size:
            continue
        take_qty = min(remaining_qty, size)
        notional += take_qty * price
        remaining_qty -= take_qty
        if remaining_qty <= 0.00000001:
            break
    if remaining_qty > 0.00000001:
        return None
    return notional / quantity


async def main_async(args):
    try:
        import websockets
    except ImportError:
        raise SystemExit("Missing dependency. Run: python3 -m pip install -r collector/requirements.txt")

    validate_args(args)
    validate_preflight(args)

    ws_url = ENVIRONMENTS[args.env]
    conn = connect_db(args.db)
    started_at = now_ns()
    run_id = conn.execute(
        """
        INSERT INTO paper_trade_runs(
          environment, market, side, notional_usd, target_bps, stop_bps,
          timeout_seconds, started_at_ns
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (args.env, args.market, args.side, args.notional, args.target_bps, args.stop_bps, args.timeout, started_at),
    ).lastrowid
    conn.commit()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass

    entry = None
    quantity = None
    entry_time = None
    exit_reason = None
    exit_price = None
    gross_pnl = None
    gross_pnl_bps = None
    last_book = None

    print(f"paper trade run #{run_id}: {args.side} {args.market} ${args.notional:.2f}")
    print(f"target={args.target_bps} bps stop={args.stop_bps} bps timeout={args.timeout}s")

    async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
        await ws.send(json.dumps({
            "type": "subscribe",
            "channel": "l2Orderbook",
            "id": args.market,
            "nLevels": args.levels,
        }))

        while not stop_event.is_set():
            message = await asyncio.wait_for(ws.recv(), timeout=30)
            received_at = now_ns()
            payload = json.loads(message)
            if payload.get("channel") != "l2Orderbook" or payload.get("id") != args.market:
                continue

            book = payload.get("contents") or {}
            tob = top_of_book(book)
            if not tob:
                continue
            last_book = book

            if entry is None:
                levels = book.get("asks") if args.side == "long" else book.get("bids")
                fill = simulate_market_fill(levels or [], args.notional)
                if not fill:
                    raise SystemExit("Not enough displayed book depth to simulate entry.")
                spread_bps = (tob["best_ask"] - tob["best_bid"]) / tob["mid"] * 10_000
                immediate_exit = exit_price_from_book(args.side, book, fill["quantity"])
                immediate_pnl = pnl(args.side, fill["avg_price"], immediate_exit, fill["quantity"]) if immediate_exit else None
                immediate_pnl_bps = immediate_pnl / args.notional * 10_000 if immediate_pnl is not None else None
                immediate_label = f"{immediate_pnl_bps:.3f} bps" if immediate_pnl_bps is not None else "unavailable"
                print(f"feasibility spread={spread_bps:.3f} bps immediate_exit={immediate_label}")
                if spread_bps > args.max_spread_bps:
                    raise SystemExit(f"Rejected: spread {spread_bps:.3f} bps > max {args.max_spread_bps:.3f} bps")
                if immediate_pnl_bps is not None and immediate_pnl_bps <= -abs(args.max_entry_exit_loss_bps):
                    raise SystemExit(
                        f"Rejected: immediate entry/exit cost {immediate_pnl_bps:.3f} bps "
                        f"<= -{args.max_entry_exit_loss_bps:.3f} bps"
                    )
                entry = fill["avg_price"]
                quantity = fill["quantity"]
                entry_time = received_at
                conn.execute(
                    """
                    UPDATE paper_trade_runs
                    SET entry_price = ?, quantity = ?, entered_at_ns = ?
                    WHERE id = ?
                    """,
                    (entry, quantity, entry_time, run_id),
                )
                conn.commit()
                print(f"ENTRY simulated at {entry:.8f}, qty={quantity:.10f}")

            mark_exit = exit_price_from_book(args.side, book, quantity)
            if mark_exit is None:
                continue

            current_pnl = pnl(args.side, entry, mark_exit, quantity)
            current_pnl_bps = current_pnl / args.notional * 10_000
            conn.execute(
                """
                INSERT INTO paper_trade_ticks(
                  run_id, received_at_ns, best_bid, best_bid_size, best_ask, best_ask_size,
                  mid, unrealized_pnl_usd, unrealized_pnl_bps, raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    received_at,
                    tob["best_bid"],
                    tob["best_bid_size"],
                    tob["best_ask"],
                    tob["best_ask_size"],
                    tob["mid"],
                    current_pnl,
                    current_pnl_bps,
                    json.dumps(book, separators=(",", ":")),
                ),
            )
            conn.commit()

            elapsed = (received_at - entry_time) / 1_000_000_000
            print(
                f"{elapsed:6.1f}s bid={tob['best_bid']:.8f} ask={tob['best_ask']:.8f} "
                f"exit={mark_exit:.8f} pnl=${current_pnl:.5f} ({current_pnl_bps:.3f} bps)"
            )

            if current_pnl_bps >= args.target_bps:
                exit_reason = "target"
            elif current_pnl_bps <= -abs(args.stop_bps):
                exit_reason = "stop"
            elif elapsed >= args.timeout:
                exit_reason = "timeout"

            if exit_reason:
                exit_price = mark_exit
                gross_pnl = current_pnl
                gross_pnl_bps = current_pnl_bps
                break

    exited_at = now_ns()
    conn.execute(
        """
        UPDATE paper_trade_runs
        SET exit_price = ?, gross_pnl_usd = ?, gross_pnl_bps = ?, exit_reason = ?,
            exited_at_ns = ?, raw_json = ?
        WHERE id = ?
        """,
        (
            exit_price,
            gross_pnl,
            gross_pnl_bps,
            exit_reason or "interrupted",
            exited_at,
            json.dumps({"last_book": last_book}, separators=(",", ":")),
            run_id,
        ),
    )
    conn.commit()
    conn.close()

    if exit_price is None or gross_pnl is None or gross_pnl_bps is None:
        print(f"CLOSE {exit_reason or 'interrupted'} before a markable exit price was available")
    else:
        print(
            f"CLOSE {exit_reason or 'interrupted'} at {exit_price:.8f}; "
            f"gross pnl=${gross_pnl:.5f} ({gross_pnl_bps:.3f} bps)"
        )


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    default_env_file = Path(__file__).resolve().parent.parent / "secrets" / "arcus.env"
    parser = argparse.ArgumentParser(description="Run a live-data paper trade and close on target/stop/timeout.")
    parser.add_argument("--env", choices=sorted(ENVIRONMENTS.keys()), default="mainnet")
    parser.add_argument("--env-file", default=str(default_env_file))
    parser.add_argument("--require-auth", action="store_true", help="Fail unless API key, address, and private key are present.")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--market", default="BTC-USD")
    parser.add_argument("--side", choices=["long", "short"], default="long")
    parser.add_argument("--notional", type=float, default=10.0)
    parser.add_argument("--target-bps", type=float, default=0.5)
    parser.add_argument("--stop-bps", type=float, default=1.0)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--levels", type=int, default=20)
    parser.add_argument("--max-spread-bps", type=float, default=5.0)
    parser.add_argument("--max-entry-exit-loss-bps", type=float, default=5.0)
    return parser.parse_args()


def validate_args(args):
    if args.notional <= 0:
        raise SystemExit("--notional must be greater than zero.")
    if args.target_bps <= 0:
        raise SystemExit("--target-bps must be greater than zero.")
    if args.stop_bps <= 0:
        raise SystemExit("--stop-bps must be greater than zero.")
    if args.timeout <= 0:
        raise SystemExit("--timeout must be greater than zero.")
    if args.levels <= 0:
        raise SystemExit("--levels must be greater than zero.")
    if args.max_spread_bps <= 0:
        raise SystemExit("--max-spread-bps must be greater than zero.")
    if args.max_entry_exit_loss_bps <= 0:
        raise SystemExit("--max-entry-exit-loss-bps must be greater than zero.")


if __name__ == "__main__":
    asyncio.run(main_async(parse_args()))

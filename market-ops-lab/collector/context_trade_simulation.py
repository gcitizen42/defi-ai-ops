#!/usr/bin/env python3
import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

RELATED_PERP = {
    "COIN": "BTC-USD",
    "MSTR": "BTC-USD",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "SOL": "SOL-USD",
}


def connect(path):
    return sqlite3.connect(Path(path).resolve())


def latest_row(conn, table, market_col, market, order_col="received_at_ns"):
    conn.row_factory = sqlite3.Row
    cur = conn.execute(f"SELECT * FROM {table} WHERE {market_col} = ? ORDER BY {order_col} DESC LIMIT 1", (market,))
    return cur.fetchone()


def run_analog(args):
    script = Path(__file__).resolve().parent / "spot_present_analog.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--ticker",
            args.ticker,
            "--horizon",
            str(args.horizon),
            "--target-pct",
            str(args.target_pct),
            "--stop-pct",
            str(args.stop_pct),
            "--k",
            str(args.k),
            "--step",
            str(args.step),
        ],
        cwd=str(Path(__file__).resolve().parent.parent),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout)


def context_adjustment(arcus_proxy, dydx_book, dydx_flow):
    score = 0.0
    reasons = []

    for label, row in [("arcus", arcus_proxy), ("dydx", dydx_book)]:
        if not row:
            reasons.append(f"{label}: missing")
            continue
        spread = row["spread_bps"]
        depth = row["depth_imbalance"]
        micro = row["microprice_edge_bps"]
        if spread is not None and spread > 25:
            score -= 0.12
            reasons.append(f"{label}: wide spread {spread:.2f}bps")
        if depth is not None:
            score += max(-0.08, min(0.08, depth * 0.12))
        if micro is not None:
            score += max(-0.08, min(0.08, micro / 100))

    if arcus_proxy and arcus_proxy["trade_flow_imbalance"] is not None:
        flow = arcus_proxy["trade_flow_imbalance"]
        score += max(-0.10, min(0.10, flow * 0.12))
        reasons.append(f"arcus flow {flow:.3f}")

    if dydx_flow and dydx_flow["flow_imbalance"] is not None:
        flow = dydx_flow["flow_imbalance"]
        score += max(-0.10, min(0.10, flow * 0.12))
        reasons.append(f"dydx flow {flow:.3f}")

    return score, reasons


def main():
    args = parse_args()
    analog = run_analog(args)
    conn = connect(args.db)
    related = args.related_perp or RELATED_PERP.get(args.ticker.upper())
    arcus = latest_row(conn, "perps_proxy_features", "market", related) if related else None
    dydx_book = latest_row(conn, "dydx_orderbook_features", "ticker", related) if related else None
    dydx_flow = latest_row(conn, "dydx_trade_flow_features", "ticker", related) if related else None
    adj, reasons = context_adjustment(arcus, dydx_book, dydx_flow)
    base_prob = analog["probability_positive"]
    adjusted_prob = max(0.0, min(1.0, base_prob + adj))
    verdict = "watch"
    if adjusted_prob >= args.accept_threshold and analog["probability_stop"] <= args.max_stop_probability:
        verdict = "candidate"
    if adjusted_prob < args.watch_threshold:
        verdict = "reject"
    result = {
        "ticker": args.ticker.upper(),
        "related_perp": related,
        "analog_probability_positive": base_prob,
        "context_adjustment": adj,
        "adjusted_probability_positive": adjusted_prob,
        "probability_target": analog["probability_target"],
        "probability_stop": analog["probability_stop"],
        "predicted_return_pct": analog["predicted_return_pct"],
        "verdict": verdict,
        "reasons": reasons,
    }
    print(json.dumps(result, indent=2))
    conn.close()


def parse_args():
    default_db = Path(__file__).resolve().parent.parent / "data" / "arcus.sqlite"
    parser = argparse.ArgumentParser(description="Run spot analog simulation and adjust with Arcus/dYdX related perps pressure.")
    parser.add_argument("--db", default=str(default_db))
    parser.add_argument("--ticker", default="COIN")
    parser.add_argument("--related-perp")
    parser.add_argument("--horizon", type=int, default=60)
    parser.add_argument("--target-pct", type=float, default=0.5)
    parser.add_argument("--stop-pct", type=float, default=0.35)
    parser.add_argument("--k", type=int, default=12)
    parser.add_argument("--step", type=int, default=20)
    parser.add_argument("--accept-threshold", type=float, default=0.72)
    parser.add_argument("--watch-threshold", type=float, default=0.58)
    parser.add_argument("--max-stop-probability", type=float, default=0.35)
    return parser.parse_args()


if __name__ == "__main__":
    main()

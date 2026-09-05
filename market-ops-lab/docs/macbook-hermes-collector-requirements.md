# MacBook / Hermes Collector Requirements

Date: 2026-07-26

## Goal

Prepare the MacBook running Hermes to collect Arcus market information accurately before any trading bot is allowed to make decisions.

The first system should be a market data recorder and research memory, not an execution bot.

## Local Runtime

Confirmed on this MacBook:

- Node.js: v25.2.1
- npm: 11.6.2
- SQLite CLI: 3.43.2
- Python: 3.14.2
- Python SQLite library: 3.51.1

Required Python package:

- `websockets`

Install:

```bash
cd market-ops-lab
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
```

## Arcus API Inputs

Public REST inputs:

- `GET /v1/markets` - market universe and metadata.
- `GET /v1/mids` - midpoint prices across markets.
- `GET /v1/candles` - OHLCV candles.
- `GET /v1/bbo` - current top of book.
- `GET /v1/orderbook` - L2 order book snapshot.
- `GET /v1/trades` - recent public trades.
- `GET /v1/funding` - historical funding rates.
- `GET /v1/live-prices` - latest oracle/mark prices.

Public WebSocket channels:

- `markets`
- `l2Orderbook`
- `l2OrderbookUpdates`
- `bbo`
- `trades`
- `candles`
- `oraclePrices`

Current Arcus docs also recommend at least 2 CPU cores and 4 GB RAM for real-time feeds; deeper books or many markets need more.

Sources:

- https://docs.arcus.xyz/llms.txt
- https://docs.arcus.xyz/api-reference/introduction
- https://docs.arcus.xyz/api-reference/websocket
- https://docs.arcus.xyz/api-reference/rate-limits
- https://docs.arcus.xyz/api-reference/public/get-markets
- https://docs.arcus.xyz/api-reference/public/get-all-mid-prices
- https://docs.arcus.xyz/api-reference/public/get-ohlcv-candles
- https://docs.arcus.xyz/api-reference/market-data/l2orderbook
- https://docs.arcus.xyz/api-reference/market-data/trades

## Storage Recommendation

Use SQLite first:

- local;
- simple;
- inspectable;
- reliable enough for prototype ingestion;
- no server dependency;
- easy for Hermes and local scripts to query.

Move to PostgreSQL + TimescaleDB later when:

- collecting all markets continuously;
- keeping deep order books;
- running multiple bots;
- needing concurrent readers/writers;
- needing retention policies and time-series compression.

## Accuracy Principles

- Store raw JSON first.
- Normalize only the fields needed for querying.
- Timestamp both exchange time and local receive time.
- Keep sequence IDs from Arcus payloads.
- Prefer WebSocket for live order book/trade streams.
- Use REST periodically to repair gaps and refresh metadata.
- Do not derive candles from order book snapshots.
- Keep REST candles as canonical OHLCV unless a later trade-derived candle builder is added.
- Log reconnects and gaps.

## First Collector Command

One REST sync:

```bash
cd market-ops-lab
source .venv/bin/activate
python3 collector/arcus_collector.py --once
```

Short live run:

```bash
python3 collector/arcus_collector.py --duration 300
```

Focused market run:

```bash
python3 collector/arcus_collector.py --markets BTC-USD,ETH-USD,SOL-USD,SPY-USD,QQQ-USD,NVDA-USD --duration 900
```

Inspect:

```bash
sqlite3 data/arcus.sqlite '.tables'
sqlite3 data/arcus.sqlite 'select market, status, category, updated_at_ns from markets order by market;'
sqlite3 data/arcus.sqlite 'select market, count(*) from candles group by market order by count(*) desc;'
```

## Obsidian Role

Use Obsidian for human-facing research notes, not primary bot storage.

Suggested flow:

```text
SQLite
  raw and normalized machine data
  bot decision logs
  simulation results

Obsidian
  daily market briefs
  strategy notes
  post-trade reviews
  hypotheses worth revisiting
```

The bot should query SQLite. Hermes can generate Markdown summaries from SQLite into an Obsidian vault.

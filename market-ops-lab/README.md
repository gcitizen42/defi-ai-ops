# Market Ops Lab

Research and planning workspace for AI-assisted market operations across Arcus, Robinhood Chain, and adjacent crypto-market data sources.

Status: research and monitoring infrastructure, not an executable trading system.
Date: 2026-07-26

## Project Areas

- `collector/` - Python public-market and context collectors that write to local SQLite databases.
- `app/` - local Node UI for Arcus market discovery.
- `docs/` - planning, architecture, strategy, and data-source notes.
- `secrets/` - local credential files only. This folder is ignored by git.

## Key Docs

- `engine-asymmetry-context.md` - original Engine Asymmetry framing.
- `arcus-research.md` - public Arcus / Robinhood Chain research with source links.
- `project-concept.md` - proposed product direction, architecture, risks, and discussion questions.
- `market-universe-2026-07-26.md` - Arcus market snapshot captured on 2026-07-26.
- `docs/data-collection-strategy.md` - storage and data strategy.
- `docs/investment-thesis.md` - volatility-first trading thesis.
- `docs/trading-control-center.md` - multi-avenue control center architecture and agent roles.
- `docs/external-data-roadmap.md` - external data-source expansion plan.

## Current Take

The strongest version of the idea is not "AI places trades directly." It is an AI-assisted market operations engine that collects market/context data, builds structured memory, detects asymmetries, explains why they may exist, and only later graduates into controlled execution on testnet.

That keeps the project close to the original Engine Asymmetry framing: AI-assisted research, blockchain analytics, workflow automation, structured data collection, SQLite, and graph-style knowledge representation.

## Requirements

- Python 3.11+
- Node.js 18+
- SQLite, included with Python
- Optional: Arcus, CoinGecko, Zerion, or Hyperliquid credentials for private or rate-limited APIs

## Collector Quick Start

```bash
cd /Users/Citizen42/Documents/DeFi-dApps/market-ops-lab
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
python3 collector/arcus_collector.py --once --rest-only
python3 collector/arcus_collector.py --markets BTC-USD,ETH-USD --duration 300
```

The collector stores data in `data/arcus.sqlite`, which is ignored by git because it can grow quickly.

Credential examples live in `collector/*.env.example`. Copy only the examples you need into `secrets/` and fill them locally:

```bash
mkdir -p secrets
cp collector/arcus.env.example secrets/arcus.env
```

Never commit real API keys, wallet keys, or private account data.

## Local Market UI

```bash
cd /Users/Citizen42/Documents/DeFi-dApps/market-ops-lab/app
npm install
npm start
```

Then open `http://localhost:4173`.

The UI proxies public Arcus endpoints only. It does not load local secrets or place trades.

## Collector Examples

Paper-trade example:

```bash
source .venv/bin/activate
python3 collector/paper_trade_watch.py --market BTC-USD --side long --notional 10 --target-bps 0.5 --stop-bps 1 --timeout 60
```

This uses live Arcus order book data but does not send any order to Arcus.

Spot sell-notification paper example:

```bash
source .venv/bin/activate
python3 collector/spot_paper_watch.py --ticker AAPL --notional 10 --target-pct 0.05 --stop-pct 0.05 --trailing-pct 0.03 --timeout 120
```

This simulates buying a spot ticker and prints a sell notification when target, stop, trailing drop, or timeout is reached.

Market Field walk-forward test:

```bash
source .venv/bin/activate
python3 collector/spot_market_field_backtest.py --tickers COIN,MSTR,RKLB,AMD,NVDA,AAPL,SPY,QQQ --horizon 60 --target-pct 0.5 --stop-pct 0.35
```

This tests a candle-based proxy for the Market Field signal against actual future spot candles and stores the autopsy in SQLite.

CoinGecko external context:

```bash
source .venv/bin/activate
python3 collector/coingecko_context.py --history-days 1 --store-assets
```

This stores public crypto reference prices and short history in SQLite for cross-market context.

Perps proxy pressure context:

```bash
source .venv/bin/activate
python3 collector/perps_proxy_context.py --markets BTC-USD,COIN-USD,NVDA-USD,AMD-USD,QQQ-USD
```

This stores perps order book, spread, slippage and trade-flow features that can be used as proxy liquidity pressure for related spot markets.

Present analog model:

```bash
source .venv/bin/activate
python3 collector/spot_present_analog.py --ticker COIN --horizon 60 --target-pct 0.5 --stop-pct 0.35
```

This finds historical spot states closest to the current state and compares what happened afterward.

Delayed prediction monitor:

```bash
source .venv/bin/activate
python3 collector/spot_delayed_prediction_monitor.py --ticker COIN --base-horizon 60 --grace 30 --target-pct 0.5 --stop-pct 0.35
```

This measures whether predictions hit on time, hit late, stopped first, or missed.

dYdX external perps context:

```bash
source .venv/bin/activate
python3 collector/dydx_context.py --tickers BTC-USD,ETH-USD,SOL-USD
python3 collector/context_trade_simulation.py --ticker COIN --related-perp BTC-USD
```

This collects dYdX order book/trade/candle context and uses it as external pressure confirmation for Arcus spot analog simulations.

Hyperliquid perps context:

```bash
source .venv/bin/activate
python3 collector/hyperliquid_context.py --limit 12 --min-volume-usd 3000000
python3 collector/hyperliquid_context.py --markets BTC,ETH,SOL,HYPE --lookback-minutes 240
```

This stores Hyperliquid market metadata, L2 book features, recent trade flow, candles, and candidate scan results in SQLite.

Zerion wallet context:

```bash
source .venv/bin/activate
python3 collector/zerion_context.py
```

This stores wallet portfolio, positions and transactions for the configured address in `secrets/zerion.env`.

## Safety Boundaries

- This is research and monitoring infrastructure, not a production trading bot.
- Keep execution disabled until explicit policy limits, testnet coverage, logging, and human approval flow are implemented.
- Treat all live market and wallet data as sensitive local data.

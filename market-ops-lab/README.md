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

## Safety Boundaries

- This is research and monitoring infrastructure, not a production trading bot.
- Keep execution disabled until explicit policy limits, testnet coverage, logging, and human approval flow are implemented.
- Treat all live market and wallet data as sensitive local data.

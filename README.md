# DeFi AI Ops

A consolidated DeFi and AI-operations workspace for protocol research, market-data collection, simulation tooling, and reusable on-chain analytics references.

## What Is Here

### AI Ops / DeFi Research

- `aiops/challenge/` - 0xFlorent challenge simulation notes, source snapshots, scripts, and renderer proof contract.

### Market Operations

- `Robinhood_ops/` - Arcus / Robinhood Chain market research, collector scripts, and a local market discovery UI.
- `Robinhood_ops/collector/` - Python collectors that write public market/context data to local SQLite databases.
- `Robinhood_ops/app/` - local Node UI for exploring public Arcus market data.
- `Robinhood_ops/docs/` - strategy, data-source, and architecture notes.

### Consolidated References

- `references/alpha-challenge/` - Wintermute Alpha Challenge study prompts and DKG monitor tooling moved from the older `Alpha-Challenge-C42` repo.
- `references/gnosis-safe-stats/` - cleaned Gnosis Safe analytics scripts moved from the older `gnosis-safe-stats` repo.

## Setup

Collector setup:

```bash
cd Robinhood_ops
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
python3 collector/arcus_collector.py --once --rest-only
```

Local market UI:

```bash
cd Robinhood_ops/app
npm install
npm start
```

Then open `http://localhost:4173`.

## Security

Do not commit API keys, wallet keys, seed phrases, `.env` files, SQLite databases, generated build output, or personal documents. Local credential files belong in ignored `secrets/` folders. Copy examples from `*.env.example` files and fill them locally.

## Status

This repository is being used as the main public technical hub for the `gcitizen42` GitHub profile. Older one-off, training, empty, and fork-only repositories are being consolidated here and can then be archived.

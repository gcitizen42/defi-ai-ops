# DeFi AI Ops

A practical workspace for DeFi research, AI-assisted market monitoring, protocol simulations, and small operations tools.

## What’s Inside

### `market-ops-lab/`

Market research and monitoring work around Arcus, Robinhood Chain, and related crypto-market data sources.

Includes:

- Python collectors for public market/context data
- Paper-trade and signal-testing scripts
- Local SQLite storage
- A small local Arcus market UI
- Research notes and planning docs

### `protocol-security-lab/`

Simulation-first protocol security research.

Includes:

- Local fork and Tenderly simulation notes
- Source snapshots used for analysis
- Scripts for contract-state review
- Challenge research notes kept for learning and reference

### `references/`

Useful older material kept as reference, including Safe analytics scripts and challenge-study tooling.

## Quick Start

Install collector dependencies:

```bash
cd market-ops-lab
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
```

Run a public-data collector once:

```bash
python3 collector/arcus_collector.py --once --rest-only
```

Run the local market UI:

```bash
cd market-ops-lab/app
npm install
npm start
```

Then open `http://localhost:4173`.

## Security

This repo is for research and local tooling. Do not commit API keys, wallet keys, seed phrases, `.env` files, SQLite databases, generated build output, or personal documents.

Use the `*.env.example` files as templates and keep real values locally only.

# DeFi AI Ops

A practical toolbox for DeFi market research, on-chain analytics, protocol simulations, and AI-assisted operations.

## Toolbox

| Tool | What it does | Access |
| --- | --- | --- |
| [Arcus collector](market-ops-lab/collector/arcus_collector.py) | Stores market, candle, trade, and order-book data in SQLite. | Public data; optional API access |
| [Hyperliquid context](market-ops-lab/collector/hyperliquid_context.py) | Captures perps liquidity, funding, open interest, and trade-flow context. | Public data |
| [CoinGecko context](market-ops-lab/collector/coingecko_context.py) | Adds crypto prices, volume, market cap, and short history. | Public data; optional API key |
| [Present analog model](market-ops-lab/collector/spot_present_analog.py) | Finds similar historical market states and compares later outcomes. | Research model |
| [Paper-trade monitor](market-ops-lab/collector/paper_trade_watch.py) | Tests entries, targets, stops, spread, and slippage without placing trades. | Simulation only |
| [Safe history exporter](references/gnosis-safe-stats/safe_history_rawdata.py) | Exports Safe multisig history to CSV with optional gas data. | Public data; optional RPC |
| [Tenderly simulator](protocol-security-lab/challenge-simulations/tenderly_simulate.py) | Runs a transaction against a Tenderly simulation project. | Simulation credentials required |

See the [toolbox guide](toolbox/README.md) for commands and requirements.

## Project Areas

- [`market-ops-lab/`](market-ops-lab/) - collectors, analysis models, paper simulations, and a local market UI.
- [`protocol-security-lab/`](protocol-security-lab/) - simulation-first smart-contract security research.
- [`references/`](references/) - older work kept for learning, including Safe analytics and Alpha Challenge material.

## Quick Start

Install the market-tool dependencies:

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
cd app
npm install
npm start
```

Then open `http://localhost:4173`.

## Security

This repository is for research and local tooling. It does not place live trades by default.

Do not commit API keys, wallet keys, seed phrases, `.env` files, SQLite databases, generated build output, or personal documents. Use the `*.env.example` files as templates and keep real values locally only.

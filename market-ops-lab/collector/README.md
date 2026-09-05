# Collector Scripts

Python collectors and analysis helpers for public market data, wallet context, and paper-trade simulations. Outputs are written to ignored local SQLite databases under `../data/`.

## Requirements

- Python 3.11+
- `websockets` from `requirements.txt`

## Setup

```bash
cd /Users/Citizen42/Documents/DeFi-dApps/market-ops-lab
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
```

## Secrets

Copy the relevant example file to `../secrets/` and fill it locally:

```bash
mkdir -p secrets
cp collector/arcus.env.example secrets/arcus.env
```

Never commit real API keys, wallet keys, local databases, or generated outputs.

## Useful Commands

```bash
python3 collector/arcus_collector.py --once --rest-only
python3 collector/coingecko_context.py --history-days 1 --store-assets
python3 collector/hyperliquid_context.py --limit 12 --min-volume-usd 3000000
```

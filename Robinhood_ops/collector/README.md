# Collector Scripts

Python collectors and analysis helpers for public market data, wallet context, and paper-trade simulations. Outputs are written to ignored local SQLite databases under `../data/`.

## Setup

```bash
cd Robinhood_ops
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r collector/requirements.txt
```

## Useful Commands

```bash
python3 collector/arcus_collector.py --once --rest-only
python3 collector/coingecko_context.py --history-days 1 --store-assets
python3 collector/hyperliquid_context.py --limit 12 --min-volume-usd 3000000
```

## Secrets

Copy example env files to `../secrets/` and fill them locally. Never commit real API keys, wallet keys, local databases, or generated outputs.

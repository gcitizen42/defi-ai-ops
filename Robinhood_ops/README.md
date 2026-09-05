# Robinhood Ops

Research and planning folder for a Robinhood Chain / Arcus-focused AI trading operations project.

Status: research packet and local tooling, not an executable trading system.

## Project Areas

- `collector/` - Python public-market and context collectors that write to local SQLite databases.
- `app/` - local Node UI for Arcus market discovery.
- `docs/` - planning, architecture, strategy, and data-source notes.
- `secrets/` - local credential files only. This folder is ignored by git.

## Requirements

- Python 3.11+
- Node.js 18+
- SQLite, included with Python
- Optional Arcus, CoinGecko, Zerion, or Hyperliquid credentials for private or rate-limited APIs

## Safety Boundaries

- This is research and monitoring infrastructure, not a production trading bot.
- Keep execution disabled until explicit policy limits, testnet coverage, logging, and human approval flow are implemented.
- Treat all live market and wallet data as sensitive local data.

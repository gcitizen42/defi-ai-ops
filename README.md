# DeFi dApps and AI Ops Workspace

Organized workspace for DeFi research, market-operations prototypes, and simulation tooling.

## Repository Map

### AI Ops / DeFi Research

- `aiops/challenge/` - 0xFlorent challenge simulation notes, source snapshots, scripts, and renderer proof contract.

### Market Operations

- `Robinhood_ops/` - Arcus / Robinhood Chain market research, collector scripts, and a local market discovery UI.
- `Robinhood_ops/collector/` - Python market/context collectors that write to local SQLite databases.
- `Robinhood_ops/app/` - Node-based local UI for public Arcus market discovery.
- `Robinhood_ops/docs/` - strategy, data-source, and architecture notes.

### Local Archive

- `archive/` - local-only material that should not be synced to GitHub. The archived CV work was moved here because it is personal rather than part of the DeFi/AI-ops project surface.

## Setup

Install collector dependencies:

```bash
cd Robinhood_ops
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
cd Robinhood_ops/app
npm install
npm start
```

Then open `http://localhost:4173`.

## Secrets Policy

Do not commit API keys, wallet keys, seed phrases, `.env` files, SQLite databases, generated build output, or personal documents. Local credential files belong in ignored `secrets/` folders. Copy examples from `*.env.example` files and fill them locally.

## Sync Checklist

Before pushing to GitHub:

1. Run `git status --short`.
2. Confirm only source, docs, examples, and requirements are staged.
3. Run the secret scan command from `SECURITY.md`.
4. Commit with a clear message.
5. Push to the configured GitHub remote.

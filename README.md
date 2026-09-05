# DeFi AI Ops

Public technical hub for DeFi research, AI-assisted market operations, and protocol-security simulation work.

## Repository Map

### Market Operations

- `market-ops-lab/` - Arcus / Robinhood Chain market research, collector scripts, and a local market discovery UI.
- `market-ops-lab/collector/` - Python market/context collectors that write to local SQLite databases.
- `market-ops-lab/app/` - Node-based local UI for public Arcus market discovery.
- `market-ops-lab/docs/` - strategy, data-source, and architecture notes.

### Protocol Security

- `protocol-security-lab/challenge-simulations/` - simulation notes, source snapshots, and local fork tooling for DeFi challenge analysis.

### Consolidated References

- `references/alpha-challenge/` - preserved Wintermute Alpha Challenge prompts and DKG monitor tooling from the older `Alpha-Challenge-C42` repo.
- `references/gnosis-safe-stats/` - cleaned Gnosis Safe analytics scripts and docs from the older `gnosis-safe-stats` repo.

### Local Archive

- `archive/` - local-only material that should not be synced to GitHub. The archived CV work was moved here because it is personal rather than part of the DeFi/AI-ops project surface.

## Naming

The public repo is arranged by purpose:

- `market-ops-lab` for market data, monitoring, research automation, and local dashboards.
- `protocol-security-lab` for defensive simulation, source review, and challenge research.
- `references` for useful material consolidated from older repos.

## Setup

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

## Secrets Policy

Do not commit API keys, wallet keys, seed phrases, `.env` files, SQLite databases, generated build output, or personal documents. Local credential files belong in ignored `secrets/` folders. Copy examples from `*.env.example` files and fill them locally.

## Sync Checklist

Before pushing to GitHub:

1. Run `git status --short`.
2. Confirm only source, docs, examples, and requirements are staged.
3. Run the secret scan command from `SECURITY.md`.
4. Commit with a clear message.
5. Push to the configured GitHub remote.

## GitHub Profile Strategy

This repository is intended to be the main public technical hub for the account. Older one-off, training, empty, or fork-only repositories can be archived once their useful material has been consolidated here.

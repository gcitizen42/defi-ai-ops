# Engine Asymmetry Context

## Local Evidence Found

The repo does not currently contain a standalone `AI ops` folder. A broader scan under `/Users/Citizen42/Documents` did not surface a matching `AI ops` directory before the scan was stopped.

Confirmed local references appear in CV/work-positioning files:

- `cv_work/build_career_platform_2026.py`
- `cv_work/build_master_cv_2026.py`
- `cv_work/optimize_cv.py`
- `cv_work/build_ops_mng_cv.py`
- `cv_work/ops-mng-cv-review.md`

Those references describe Engine Asymmetry / Asymmetry Engine as:

- a personal AI and blockchain research initiative;
- focused on AI applied to blockchain analytics, operational research, and workflow automation;
- using SQLite, LLMs, AI agents, structured data collection, graph-based knowledge representation, and autonomous research workflows;
- not yet verified as a public product, public repository, dashboard, or deployed system.

## Interpretation

Based only on the local repo evidence, Engine Asymmetry was about building an AI-assisted research and operations layer for blockchain data rather than a pure trading bot.

The "asymmetry" part should be treated as the search for informational, structural, liquidity, timing, or operational imbalances that are visible in market/on-chain data but not obvious from a UI.

## What This Means For Market Ops Lab

The new project should start as a research and monitoring system:

- collect Arcus market data and account/order data;
- normalize it into a local database;
- compute asymmetry signals;
- let an AI agent summarize market state, explain anomalies, and propose hypotheses;
- require human approval before any live execution;
- use testnet first for order-routing experiments.

This is more defensible than starting with autonomous trading. The public Arcus docs confirm there is a real REST and WebSocket API surface, but trading tokenized equities/perps is high-risk and jurisdiction-sensitive.

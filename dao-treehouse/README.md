# DAO Treehouse

An evidence-backed map of who can control a DAO's contracts, plus a guarded workspace for preparing governance actions.

Status: product foundation and case-study data. It does not connect wallets, propose transactions, or execute changes yet.

## Core Workflow

1. Add a GitHub repository and choose its supported networks.
2. Scan deployment files without running repository code.
3. Verify every candidate address against current chain state.
4. Build a control graph covering owners, Safes, signers, roles, Timelocks, governors, proxies, implementations, modules, and guards.
5. Select a contract and prepare a human-readable action.
6. Re-check current state, simulate the result, and export an unsigned proposal for review.

The app must keep repository claims separate from live-chain facts. Every node and relationship carries its source, observation block, and confidence.

## First Case Study

[`case-studies/threshold-tbtc-v2/`](case-studies/threshold-tbtc-v2/) seeds a partial control map for Threshold Network tBTC v2 on Ethereum and Arbitrum One. It includes the governance Safes, Timelocks, key contracts, proxy implementations, ownership paths, signer rosters, and two useful examples of stale source data.

## Design Notes

- [Product requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Control graph](docs/control-graph.md)
- [Security model](docs/security-model.md)
- [Technical decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)
- [Project manifest schema](schemas/project-manifest.schema.json)

## Safety Boundary

Read-only discovery comes first. Action preparation remains unsigned and simulation-gated. Private keys and seed phrases never enter the app, repository, server, logs, or generated files.

Timelock scheduling and execution are always separate stages. Admin-role changes are isolated from routine operations and require additional review.

## Proposed Repository Layout

```text
dao-treehouse/
  apps/web/                  dashboard
  apps/worker/               repository and chain scanners
  packages/action-builder/   reviewed action intents and Safe batches
  packages/chain-discovery/  ownership, role, Safe, and proxy adapters
  packages/control-graph/    graph model and authority resolution
  packages/repo-scanner/     deployment artifact parsers
  packages/shared/           schemas and shared types
```

The application folders will be added when the read-only discovery slice is implemented.

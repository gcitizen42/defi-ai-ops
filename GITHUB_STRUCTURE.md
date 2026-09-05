# GitHub Structure

This account should present two top-level repositories:

- `gcitizen42` - profile README and account landing page.
- `defi-ai-ops` - main public technical hub for DeFi research, AI-assisted market operations, and protocol-security simulations.

## Public Categories

### Profile

Use `gcitizen42/gcitizen42` only for the GitHub profile README. It should explain the work, link to the main hub, and stay short.

### Technical Hub

Use `gcitizen42/defi-ai-ops` for active and reference work:

- `market-ops-lab/` - market data collection, monitoring, dashboards, and trading-research infrastructure.
- `protocol-security-lab/` - defensive smart-contract simulation and protocol analysis.
- `references/` - useful material consolidated from older repositories.

## Older Repositories

Recommended treatment:

- `Alpha-Challenge-C42` - archive after confirming `references/alpha-challenge/` has the useful challenge prompts and DKG monitor.
- `gnosis-safe-stats` - archive after confirming `references/gnosis-safe-stats/` has the useful analytics scripts.
- `tbtc-bridge-server` - archive as an old experiment unless it becomes a dedicated bridge service again.
- `DefiLlama-Adapters` - archive unless there is an active adapter contribution plan.
- `governance4thresholders` - archive; currently a placeholder.
- `timelock-controller` - archive; currently a placeholder.
- `github-slideshow` - archive; training repository.

## Naming Rules

- Name folders by what they do, not by the first working title.
- Keep public names broad enough to grow: `market-ops-lab` is better than a single exchange name.
- Keep one-off challenge material under `references/` or `protocol-security-lab/` instead of making many small repos.
- Do not publish secrets, generated databases, large build outputs, personal documents, or credential-bearing config files.

# On-Chain Operations Toolkit

Read-only utilities for inspecting Safe accounts and Threshold Network activity.

## Tools

| Tool | Purpose |
| --- | --- |
| [Safe module inspector](safe-module-inspector/) | Finds Safes owned by an address and inventories enabled modules across supported EVM chains. |
| [Threshold fee monitor](threshold-fee-monitor/) | Totals tBTC Bridge redemption treasury fees by month and year. |
| [tBTC wallet registry](tbtc-wallet-registry/) | Lists registered tBTC wallets, their state, age, and on-chain metadata. |

## Setup

Requirements: Node.js 20+ and npm.

```bash
cd onchain-ops-toolkit
npm install
npm run build
npm test
```

Each tool has its own README and `.env.example`. The tools only read public blockchain data and never require a wallet key.

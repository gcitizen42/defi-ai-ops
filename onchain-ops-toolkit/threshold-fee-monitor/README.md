# Threshold Fee Monitor

Queries tBTC Bridge `RedemptionRequested` events and totals treasury fees by month and year. The date range is inclusive at the start and exclusive at the end.

## Run

From `onchain-ops-toolkit/`:

```bash
cp threshold-fee-monitor/.env.example threshold-fee-monitor/.env
# Add an Ethereum RPC URL to threshold-fee-monitor/.env
npm run start --workspace threshold-fee-monitor -- 2025-01-01 2026-01-01
```

The output is printed in satoshis. The monitor filters every query to the official Ethereum tBTC Bridge proxy address.

## Requirements

- Node.js 20+
- An Ethereum JSON-RPC URL

No signer or wallet key is used.

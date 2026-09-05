# tBTC Wallet Registry

Scans the Ethereum tBTC Bridge for wallet registrations and reports each wallet's current state and on-chain metadata.

The original local script attempted to report BTC balances using an incomplete contract call. This version deliberately reports only values that the Bridge can provide reliably.

## Run

From `onchain-ops-toolkit/`:

```bash
cp tbtc-wallet-registry/.env.example tbtc-wallet-registry/.env
# Add an Ethereum RPC URL to tbtc-wallet-registry/.env
npm run start --workspace tbtc-wallet-registry
```

By default, only live wallets are printed. Include every state or limit the block range:

```bash
npm run start --workspace tbtc-wallet-registry -- \
  --state all \
  --from-block 17392800 \
  --to-block latest
```

## Requirements

- Node.js 20+
- An archive-capable Ethereum JSON-RPC URL for historical block ranges

The command writes JSON to standard output and progress to standard error. It never writes credentials or sends transactions.

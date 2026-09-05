# Safe Module Inspector

Discovers Safe accounts for an owner and inventories their enabled modules. Optional RPC access adds bytecode, selector, and proxy checks.

This is a read-only inspection tool. It does not sign or submit transactions.

## Run

From `onchain-ops-toolkit/`:

```bash
cp safe-module-inspector/.env.example safe-module-inspector/.env
# Add a public owner address to safe-module-inspector/.env
npm run start --workspace safe-module-inspector
```

You can override the owner and chains without changing the file:

```bash
npm run start --workspace safe-module-inspector -- \
  --owner 0xYOUR_OWNER_ADDRESS \
  --chains ethereum,gnosis
```

Reports are written as Markdown and JSON in `safe-module-inspector/reports/`.

## Requirements

- Node.js 20+
- A public EVM address
- Optional RPC URLs for deeper module classification

Public addresses and RPC access are sufficient. Never add wallet keys or seed phrases.

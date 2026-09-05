# Zerion Context

Date: 2026-07-29

## Wallet

Configured wallet:

```text
0x3070f20f86fda706ac380f5060d256028a46ec29
```

Local config:

```text
market-ops-lab/secrets/zerion.env
```

Fill in:

```bash
ZERION_API_KEY=...
ZERION_WALLET_ADDRESS=0x3070f20f86fda706ac380f5060d256028a46ec29
```

## Purpose

Zerion is for wallet state, not order-book prediction:

- portfolio value;
- positions;
- transaction history;
- wallet-level PnL context;
- post-trade reconciliation;
- exposure/risk controls.

## Command

```bash
cd /Users/Citizen42/Documents/DeFi-dApps/market-ops-lab
source .venv/bin/activate
python3 collector/zerion_context.py
```

Tables:

- `zerion_wallet_snapshots`
- `zerion_portfolio`
- `zerion_positions`
- `zerion_transactions`

## Trading Model Role

```text
Arcus/dYdX = market pressure and execution context
Zerion = wallet state, exposure, PnL and reconciliation
```

## Useful Lessons From Zerion AI LP Planning

Source reviewed: `https://zerion.io/blog/how-to-provide-liquidity-on-uniswap-with-ai/`

The article is about planning Uniswap liquidity positions, not perps. The useful architecture is still relevant:

- start every trade plan from the wallet's current portfolio, positions, and PnL;
- check whether the proposed allocation creates concentration risk;
- require the bot to output a concrete position plan before execution;
- keep API keys and agent credentials in local env/config, never in public code;
- keep human review/signing in the loop until the system has proven itself;
- treat automated agent permissions as scoped spending credentials.

For our perps workflow this becomes:

```text
1. Read wallet/account context from Zerion.
2. Read market pressure from Arcus/dYdX.
3. Generate a proposed perp plan:
   market, long/short, entry, stop, take profit, leverage, margin, max loss, liquidation distance, hold window.
4. Reject if wallet exposure, drawdown, liquidity, spread, funding, or model confidence is outside limits.
5. Present the plan for manual execution or later policy-scoped automation.
6. Reconcile open/closed position state back into SQLite.
```

## Zerion Perps Role

Zerion supports perps trading in the wallet app through Hyperliquid. This is separate from the Zerion API wallet-analysis role.

Use Zerion perps as:

- a manual execution venue for early tests;
- a source of portfolio/account context if the API exposes the position data for the wallet;
- a reconciliation layer after trades.

Do not assume Zerion API gives us raw Hyperliquid order book depth or live execution endpoints until verified with the API key and current docs. For prediction data, keep using:

- Arcus perps L2/BBO/trades;
- dYdX public order book and trade flow;
- Hyperliquid market data if we add a direct collector later.

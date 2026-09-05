# Trading Control Center

Date: 2026-08-24

## Goal

Build a trading control center where multiple specialist agents can research, plan, monitor, and audit trades across several avenues.

The control center should coordinate:

- spot trades;
- perps trades;
- yield-agent deposits;
- wallet/account risk;
- data collection;
- simulation and post-trade review.

## Avenues

### Arcus / Robinhood Chain

Role:

- spot and perps market discovery;
- Robinhood-chain specific market data;
- tokenized equity context;
- cross-market asymmetry research.

Use for:

- market universe;
- candles;
- perps order book where available;
- BBO, trades, spreads, slippage;
- stock-token and crypto-beta relationships.

### Hyperliquid

Role:

- direct crypto perps venue and market data source;
- possible execution venue after API-wallet controls are complete.

Use for:

- perps universe;
- L2 book;
- recent trades;
- candles;
- funding;
- open interest;
- account state.

Execution requires a Hyperliquid API wallet / agent wallet and signed exchange actions.

### dYdX

Role:

- independent perps data source;
- confirmation layer against Hyperliquid and Arcus.

Use for:

- BTC/ETH/SOL pressure;
- order book comparison;
- trade-flow divergence;
- funding and candle confirmation.

### Zerion

Role:

- wallet context and manual perps execution surface.

Use for:

- portfolio value;
- existing token/DeFi exposure;
- transaction history;
- post-trade reconciliation;
- manual Hyperliquid-backed perps execution if market is listed.

### GammaFi / Project 0

Role:

- Solana yield-agent avenue.

Use for:

- SOL-denominated yield exposure;
- ML-managed strategy allocation;
- p0SOL monitoring;
- yield-versus-perps comparison;
- capital parking when perps signal quality is poor.

### x402 / Agentic Wallet

Role:

- agent payments and data/tool budgets.

Use for:

- paying for premium APIs;
- budgeted agent-to-agent services;
- future paid research/signal API;
- not for Hyperliquid order signing.

## Agent Roles

### Market Data Agent

Collects:

- candles;
- order books;
- trade prints;
- funding;
- open interest;
- APY/share price for yield agents;
- wallet balances and positions.

### Volatility Agent

Computes:

- realized volatility;
- EWMA volatility;
- GARCH-style conditional variance;
- volatility regime;
- position size from target risk.

### Microstructure Agent

Computes:

- spread;
- slippage;
- order book imbalance;
- microprice edge;
- recent flow imbalance;
- target-before-stop feasibility.

### Yield Agent Analyst

Computes:

- share-price growth;
- realized APY;
- predicted APY drift;
- TVL/capacity change;
- concentration in underlying strategies;
- withdrawal-fee and liquidity impact.

### Risk Agent

Approves or rejects plans based on:

- max loss;
- leverage;
- liquidation distance;
- protocol exposure;
- wallet concentration;
- smart-contract risk;
- data freshness.

### Execution Planner

Produces a human-readable plan:

- venue;
- asset;
- direction or deposit action;
- entry/deposit amount;
- target;
- stop or withdrawal rule;
- hold window;
- invalidation conditions;
- monitoring schedule.

### Auditor

Stores:

- raw inputs;
- model scores;
- rejected alternatives;
- final plan;
- execution status;
- realized result;
- post-mortem.

## Unified Decision Types

```text
reject
watch
paper_trade
manual_trade
manual_deposit
automated_trade_later
automated_rebalance_later
```

## Safety Boundary

Live autonomous execution is out of scope until:

- every venue has read-only collectors;
- paper decisions are logged for a meaningful sample;
- stop-loss behavior is tested;
- agent-wallet keys are isolated and revocable;
- max daily loss is enforced;
- all production execution requires explicit human approval or a pre-approved policy envelope.


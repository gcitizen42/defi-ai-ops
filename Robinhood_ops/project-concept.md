# Project Concept: Robinhood Ops / Trading Control Center

## Working Thesis

Build an AI-assisted trading control center for planning trades and yield allocations across multiple venues.

The first useful version should observe, structure, explain, simulate, and alert. It should not autonomously trade with real funds.

Arcus remains one important avenue, but the broader project should coordinate:

- Arcus / Robinhood Chain for tokenized markets and perps data;
- Hyperliquid for direct crypto perps market data and possible future API-wallet execution;
- dYdX as an independent perps confirmation layer;
- Zerion for wallet context and manual perps execution;
- GammaFi / Project 0 for Solana yield-agent allocation;
- x402 / Agentic Wallet for paid data/tool access and future agent commerce.

## What The System Looks For

"Asymmetry" can mean:

- price differences between stock tokens, perps, and reference markets;
- liquidity gaps across order books and venues;
- unusual volume or flow in Robinhood Chain tokenized assets;
- order book imbalance and spread changes;
- divergence between 24/7 tokenized assets and closed traditional markets;
- funding, margin, or leverage conditions that create directional pressure;
- yield-agent alternatives where idle capital may earn risk-bounded return while trade quality is low;
- user/account-level operational risk, such as stale orders, fills, or missing cancels.

## Proposed MVP

Phase 1 should be a read-only research and planning engine:

1. Arcus connector
   - REST metadata/account reads where available.
   - WebSocket market feeds.
   - Spot indexer stats.

2. Hyperliquid and dYdX connectors
   - Perps market universe.
   - L2 book, recent trades, candles, funding, open interest where available.
   - Independent confirmation of flow and liquidity pressure.

3. Zerion and wallet context
   - Portfolio value.
   - Existing DeFi/token exposure.
   - Transaction history.
   - Manual execution/reconciliation context.

4. Solana yield-agent context
   - GammaFi / Project 0 p0SOL snapshots.
   - Share price, APY, TVL, capacity, strategy allocation, withdrawal fee.
   - Yield-agent alternative when perps trade quality is poor.

5. Local data store
   - SQLite for events, snapshots, trades, candles, account state, and research notes.
   - Append-only raw event table so schemas can be repaired later.

6. Signal layer
   - spread and liquidity monitor;
   - order book imbalance;
   - volume shock detector;
   - volatility regime and target-before-stop model;
   - yield-versus-trade opportunity comparison;
   - stale-order and exposure monitor;
   - cross-market watchlist for stocks, indices, commodities, and crypto.

7. AI research layer
   - summarize market state;
   - explain anomalies with cited data;
   - generate research notes;
   - maintain a hypothesis graph;
   - produce "watch", "investigate", or "do nothing" recommendations.

8. Human approval layer
   - no live order placement in MVP;
   - testnet-only order placement in Phase 2;
   - explicit kill switch before any production trading is considered.

## Suggested Folder Structure For The Future Build

```text
Robinhood_ops/
  docs/
  secrets/
  src/
    arcus/
      rest_client.py
      ws_client.py
      signing.py
      schemas.py
    storage/
      db.py
      migrations/
    signals/
      orderbook.py
      volume.py
      divergence.py
      risk.py
      volatility.py
      yield_agents.py
    ai/
      researcher.py
      prompts/
    app/
      cli.py
      dashboard.py
  tests/
```

## First Technical Milestone

Build a testnet-only data collector:

- load API key from `Robinhood_ops/secrets/arcus.env`;
- connect to Arcus testnet WebSocket;
- subscribe to selected market data channels;
- store raw messages in SQLite;
- compute basic spread/order-book metrics;
- write a daily markdown research brief.

## Decision Points For Discussion

- Do we want this to be a research dashboard, a CLI agent, or both?
- Should the first market focus be stock tokens, crypto perps, or cross-asset divergence?
- Should we integrate non-Arcus reference data for underlying equities and ETFs?
- Should AI output be limited to summaries, or should it generate structured trade hypotheses?
- Should yield agents like p0SOL be treated as capital parking, active strategy allocation, or both?
- What is the risk boundary: read-only, testnet execution, or eventually live execution?

## Non-Negotiables

- Keep secrets outside git.
- Start on testnet.
- Preserve raw data for auditability.
- Separate signal generation from execution.
- Never let an LLM directly place or cancel live orders.
- Add a kill switch before any trading code exists.

# GammaFi / Project 0 Yield Agent Thesis

Date: 2026-08-24

## Thesis

GammaFi's p0SOL agent is relevant to this project because it shows a parallel model to our trading bot idea:

```text
User deposits one asset.
An agent allocates across multiple venues.
The user receives a single liquid receipt token.
The strategy is judged by risk-adjusted return, not isolated APY.
```

This is not a perps trade. It is a Solana yield-agent position that can become one avenue inside the trading control center.

## Verified Public Snapshot

Public page checked:

```text
https://app.gma.fi/agents/p0-sol
```

Observed on the page snapshot:

- Product: `Project 0|SOL`
- Receipt/share token: `p0SOL`
- Position type: risk-optimized automated SOL and LST yield aggregation
- Points: `x2`
- Share price shown: `1.0034 SOL`
- Current APY shown: `24.02%`
- Solver-predicted APY shown: `21.67%`
- TVL shown: `1,436.71 SOL`
- 24h volume shown: `283.09 SOL`
- Total depositors shown: `42`
- Performance fee: `0%`
- Withdrawal fee: `0.1%`

These metrics are time-sensitive and must be refreshed before any decision.

## How It Works

User side:

- deposit SOL;
- receive p0SOL shares;
- share price changes as yield accrues;
- withdraw by burning shares for SOL, subject to the posted withdrawal fee.

Agent side:

- the _gamma Economic Agent runs SOL-denominated yield strategies;
- the page describes leveraged SOL and liquid-staking-token multiply loops;
- it also references SOL lending optimization, funding-rate arbitrage, and cross-protocol leveraged positions;
- allocation is based on risk-adjusted EMAs of realized strategy returns;
- the allocator incorporates leverage costs, liquidation thresholds, and liquidity constraints;
- rebalancing is described as machine-learning-driven.

Infrastructure:

- Project 0 acts as the Solana DeFi-native prime broker;
- Project 0 provides unified margin/credit across venues such as Kamino, Drift, and Jupiter;
- Project 0 documentation describes cross-venue collateral through a unified margin account.

## Why This Matters To Our System

This adds a third capital mode:

```text
1. Cash / stable idle state
2. Directional perps trades
3. Yield-agent allocation while directional edge is weak
```

The control center should compare a perp trade against the yield-agent alternative:

- Is expected perps return worth the additional liquidation and timing risk?
- Is p0SOL APY enough to park SOL while waiting for better trades?
- Is wallet exposure already too SOL-heavy?
- Is Project 0 / GammaFi protocol risk acceptable for the amount?

## How To Model It

Store snapshots:

- share price;
- current APY;
- solver-predicted APY;
- realized APY;
- TVL;
- 24h volume;
- depositor count;
- remaining capacity;
- holdings/strategy allocation;
- withdrawal fee;
- source URL and fetched timestamp.

Compute:

- share-price return in SOL terms;
- APY drift;
- TVL inflow/outflow;
- strategy concentration;
- drawdown from share-price history;
- realized yield versus SOL staking benchmark;
- realized yield versus perps funding/carry alternatives.

## Risk Register

- Product is new and has limited live stress history.
- Multi-protocol smart-contract exposure exists across Project 0 and underlying venues.
- Leveraged loops can introduce liquidation risk.
- Rebalancing can be stressed during fast liquidity exits.
- ML allocator may overweight stale return regimes.
- Share price may update in steps because Solana staking rewards accrue around epoch boundaries.
- UI metrics can change quickly and must be captured with timestamped snapshots.

## Initial Usage Rule

Treat p0SOL as an experimental yield layer, not core collateral.

Prototype rule:

```text
No deposit recommendation until the control center can refresh metrics, record strategy holdings, compare against SOL staking baseline, and produce a protocol-risk score.
```

## Sources

- https://app.gma.fi/agents/p0-sol
- https://www.0.xyz/
- https://docs.0.xyz/
- https://www.0.xyz/ecosystem
- https://www.0.xyz/security


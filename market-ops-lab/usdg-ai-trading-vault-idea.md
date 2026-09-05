# USDG AI Trading Vault Idea

Date captured: 2026-07-26
Status: concept memory, not implementation approval

## Core Idea

Build an app where a user:

1. Deposits USDG.
2. Selects a risk appetite.
3. Submits funds into a strategy run.
4. The backend assigns the funds to a trading bot.
5. The bot uses Hermes-style research loops to inspect Arcus markets, simulate strategy settings, evaluate feasibility, and place trades.
6. The user receives a target timeframe for when to return.
7. At the end of the run, the user can claim remaining funds plus any realized profit.

The project intent is to use AI-assisted execution for broad user benefit, with every trade researched, simulated, and justified before execution.

## Proposed User Risk Modes

- Conservative: low leverage or no leverage, strict drawdown cap, larger liquidity requirements, shorter exposure windows.
- Balanced: moderate trade frequency, wider opportunity set, controlled leverage only after simulation.
- Aggressive: higher volatility tolerance, more strategies, tighter monitoring, still bounded by hard loss limits.

## Bot Loop

The engine should not place random trades. It can explore strategies randomly or semi-randomly, but execution should require confirmation through evidence.

Suggested loop:

1. Discover available Arcus markets.
2. Pull live candles, order book, funding, open interest, and 24h stats.
3. Generate candidate trade hypotheses.
4. Simulate strategy settings before execution.
5. Reject trades that fail liquidity, spread, fee, slippage, funding, or drawdown checks.
6. Rank feasible trades by expected value and risk.
7. Place testnet trades first.
8. Monitor positions continuously.
9. Exit based on target, stop, timeout, or risk breach.
10. Write an audit trail for every decision.

## Hermes Role

Hermes can be treated as the research/execution loop runner:

- repeated market scans;
- AI reasoning cycles;
- strategy parameter search;
- feasibility simulation;
- decision logging;
- trade execution coordination;
- post-trade review.

## MiroFish GitHub Role

MiroFish GitHub should be researched and evaluated before integration.

Possible role if suitable:

- simulation harness;
- strategy setting generator;
- backtesting workflow;
- feasibility checker;
- benchmark environment for bot decisions.

Open question: confirm what MiroFish is, what repo should be used, its license, and whether it is suitable for financial simulation.

## Product Architecture Sketch

```text
User App
  deposit USDG
  choose risk appetite
  view active run
  claim after run

Vault / Escrow Layer
  records deposits
  allocates capital
  enforces claim rules
  blocks unauthorized withdrawals

Risk Engine
  max drawdown
  max exposure
  max leverage
  market whitelist
  kill switch

Research Engine
  Arcus market data
  candles/order book/funding/OI
  AI research loop
  strategy candidates

Simulation Engine
  MiroFish or custom simulator
  fees/slippage/spread checks
  scenario testing

Execution Engine
  Arcus API
  testnet first
  live only after human approval and compliance review

Audit Store
  raw data
  hypotheses
  simulations
  trade decisions
  fills
  profit/loss
```

## Important Boundary

The app should not promise guaranteed profit or a minimum $1 reward. A minimum target can be a goal or strategy threshold, but presenting it as guaranteed creates serious financial, legal, and user-trust risk.

Safer framing:

- "The bot only enters trades whose simulated expected reward exceeds $1 after estimated fees/slippage."
- "Returns are not guaranteed."
- "Users may receive less than deposited."
- "The system can choose not to trade when conditions are poor."

## Non-Negotiables Before Mainstream Use

- Testnet-only proof first.
- No custody or user deposits until legal/compliance review.
- No guaranteed-return language.
- Full audit logs for every trade.
- Hard kill switch.
- Position limits per user and globally.
- Clear loss disclosure.
- Jurisdiction restrictions.
- Independent strategy testing.
- Human approval before any live-funds experiment.

## First Practical Experiment

Before user deposits exist, build a private operator tool:

1. Connect to Arcus public market data.
2. Run research/simulation loops on selected markets.
3. Produce trade proposals with evidence.
4. Execute only on Arcus testnet.
5. Track paper PnL and decision quality.
6. Compare AI-selected trades against simple baseline strategies.

This gives us evidence before touching custody, USDG deposits, or public users.

# Zerion Perps Planning Layer

Date: 2026-07-29

## Summary

Zerion can be useful for this project, but not as the main prediction engine.

Use Zerion for:

- wallet portfolio context;
- existing exposure and PnL;
- account-level risk sizing;
- manual perps execution through the Zerion app;
- future agent-token policy design if Zerion CLI trading permissions fit our needs.

Use Arcus, dYdX, and later Hyperliquid direct market data for:

- order book pressure;
- spreads;
- trade flow;
- candles;
- funding;
- market anomaly detection;
- strategy simulation.

## Adopted From Zerion's AI LP Article

The Uniswap LP article's useful pattern is portfolio-first planning:

```text
Do not ask "is this market attractive?" first.
Ask "does this trade make sense for this wallet, at this size, now?"
```

For perps this means the bot must know:

- current wallet value;
- available stablecoin balance;
- current open DeFi/perps/spot exposure;
- realized and unrealized PnL;
- recent wallet drawdown;
- whether the proposed trade is correlated with existing holdings.

## Required Trade Plan Output

Every candidate trade must produce this structure:

```json
{
  "venue": "zerion_perps_manual",
  "underlying": "BTC",
  "direction": "long",
  "entry_type": "limit",
  "entry_price": 0,
  "take_profit_price": 0,
  "stop_loss_price": 0,
  "max_hold_minutes": 0,
  "notional_usd": 0,
  "margin_usd": 0,
  "leverage": 1,
  "max_loss_usd": 0,
  "liquidation_distance_pct": 0,
  "confidence": 0,
  "reasons": [],
  "reject_reasons": []
}
```

No trade should be suggested unless it has:

- entry;
- stop;
- take profit;
- hold window;
- size;
- leverage;
- expected spread/slippage;
- explicit invalidation reason.

## Initial Risk Rules

Prototype defaults:

- manual execution only;
- no leverage above `2x` until the simulator shows durable edge;
- max margin per test trade: user-specified amount only;
- max loss per trade: `0.25%` to `1.0%` of available trading capital;
- reject if spread consumes more than `20%` of target profit;
- reject if liquidation is too close to the stop;
- reject if target probability is not meaningfully better than stop probability;
- reject if recent analogs show stop-before-target behavior.

## Data Checklist Before Perps Recommendation

Minimum:

- spot/perp candle trend;
- order book imbalance;
- BBO spread;
- recent trade flow;
- funding rate if available;
- related-market confirmation;
- wallet exposure from Zerion.

Better:

- direct Hyperliquid order book;
- direct Hyperliquid funding/open interest;
- liquidation level heatmaps if public/licensed;
- news/event feed;
- cluster correlation regime.

## Execution Boundary

The bot can prepare and monitor the plan. The user executes manually in Zerion until a dedicated, scoped, revocable agent credential is configured and tested.

Required automation controls before any live execution:

- allowlisted venue/chain/contracts;
- max trade size;
- max daily loss;
- max open positions;
- expiry on agent credential;
- dry-run mode;
- full SQLite audit log;
- emergency kill switch.


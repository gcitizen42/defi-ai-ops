# Live Trade Scan

Date: 2026-07-29

## Goal

Find a high-upside perps candidate for manual execution through Zerion or dYdX.

## Data Checked

- dYdX public markets, order book, recent trades, and 1 minute candles.
- Arcus perps proxy context for BTC, ETH, and SOL.
- Hyperliquid public perp market universe, L2 book, recent trades, and 1 minute candles.

## dYdX Result

dYdX live liquidity scan only showed BTC-USD and ETH-USD above the initial $1M 24h volume filter.

Both were rejected:

- BTC-USD: weak directional score.
- ETH-USD: weak directional score.

## Hyperliquid / Zerion Perps Candidate

Candidate:

```text
Market: kPEPE
Side: SHORT
Entry reference: 0.002702
Take profit: 0.0026685757
Stop loss: 0.0027191233
Target move: 1.237%
Stop move: 0.634%
Reward/risk: 1.95
Confidence score: 0.607
```

Reasons:

- 1m, 5m, 15m, 60m, and 24h direction are broadly bearish.
- Recent trade flow was strongly sell-heavy in the sampled trades.
- Spread was acceptable for a high-risk perp attempt.
- Depth imbalance was slightly ask-heavy.

Risks:

- Recent-trade sample was small.
- Meme/perp markets can wick violently.
- Funding is positive, which slightly penalizes shorts.
- This should be treated as a high-risk manual test, not a reliable edge.

Suggested prototype controls:

```text
Manual execution only.
Isolated margin.
No more than 2x leverage for first test.
Cancel idea if price trades above stop before entry.
Do not widen stop after entry.
```

## Rejected / Watch Names

- NEAR short: weak combined signal.
- ADA short: weak combined signal.
- HYPE short: weak combined signal.
- SOL short: weak combined signal.
- BTC long: weak combined signal.
- ETH long: weak combined signal.
- KAITO short: conflicting short-term buy flow despite bearish 15m/60m.

## Missing Before Full Automation

- Zerion API key for wallet balance/exposure check.
- Direct confirmation that Zerion perps lists the selected Hyperliquid market.
- Live monitor for Hyperliquid positions.
- Fee model and liquidation-distance calculation.


# Data Collection Strategy

## Objective

Collect enough accurate market information for a future bot to research opportunities, simulate feasibility, and explain trade candidates before any order is placed.

This is not a profitability guarantee. Profitable trading comes from robust data, risk controls, execution quality, and repeatable strategy evidence.

## What To Collect First

Priority 1:

- market metadata;
- mid prices;
- 1m candles;
- L2 order book snapshots;
- BBO/top-of-book;
- public trades;
- funding rates;
- oracle and mark prices;
- open interest;
- volume and trade counts.

Priority 2:

- account positions;
- open orders;
- fills;
- funding payments;
- portfolio history.

Priority 2 requires an address or account context and should stay separate from public market collection.

## Why This Data Matters

- Candles: trend, volatility, momentum, volume, regime detection.
- Order book: spread, depth, imbalance, slippage estimate.
- Trades: actual flow, aggressor side, realized liquidity.
- Funding: carry cost and crowding pressure.
- Open interest: positioning and leverage pressure.
- Oracle vs mark vs last: dislocation and pricing boundary checks.
- Market status/RTH fields: equity-like markets have trading-hour and bound behavior that affects strategy feasibility.

## Minimum Bot Query Features

The bot should be able to ask:

- Which markets are online?
- Which markets have recent liquidity?
- Which markets have the tightest spreads?
- Which markets have enough depth for a target order size?
- Which markets show rising volume or volatility?
- Which markets are outside regular trading hours?
- Which markets are near upper/lower trading bounds?
- Which markets have funding pressure?
- Which candidate trade would fail after fees/slippage?

## Strategy Research Path

Start with non-executing analytics:

1. Spread monitor.
2. Order-book imbalance monitor.
3. Volume shock monitor.
4. Funding-rate pressure monitor.
5. Oracle/mark/last divergence monitor.
6. Simulated entry/exit with estimated slippage.
7. Paper PnL tracking.

Only after those produce stable evidence should the system move to testnet execution.

## Profitability Research Principles

- Never let the AI decide from narrative alone.
- Every trade candidate needs data citations from the database.
- Every strategy needs a baseline comparison.
- Randomized strategy search is allowed only inside simulation.
- Live execution should use strict allowlists, max loss, max exposure, and kill switches.
- If estimated reward after costs is under the threshold, do not trade.
- If spread/depth is poor, do not trade.
- If the system cannot explain the trade numerically, do not trade.

## Storage Schema Summary

The collector creates:

- `raw_events`
- `markets`
- `market_snapshots`
- `mids`
- `candles`
- `orderbook_snapshots`
- `bbo`
- `trades`
- `collector_runs`

Raw events preserve everything. Normalized tables make bot queries fast.

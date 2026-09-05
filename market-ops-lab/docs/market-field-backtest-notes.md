# Market Field Backtest Notes

Date: 2026-07-27

## Purpose

Test the Market Field idea using past public Arcus spot data:

1. Look back from a historical timestamp.
2. Compute a signal from only data available at that timestamp.
3. Make a long prediction when the signal clears a threshold.
4. Compare against the actual future candle path.
5. Store wins, losses, timeouts, returns, and feature values.

This avoids hindsight bias better than manually looking at today's chart and explaining it after the fact.

## Current Limitation

For spot, the currently used Arcus public data is candle/quote based:

- `GET /v1/api-meta/spot/overview`
- `GET /v1/api-meta/candles`

That means the first test is only a proxy for the liquidity field. It does **not** yet include true spot order book liquidity, hidden/vanishing depth, or trade-by-trade flow.

## Current Proxy Features

- 15m/30m/60m/240m returns.
- Position within recent 60m and 240m range.
- Recent volume ratio.
- Volume z-score.
- 60m realized volatility.
- 60m range compression.
- Breakout pressure.
- Pullback pressure.
- Noise and extension penalties.

## What We Need Next

To get closer to the original liquidity-field idea:

- spot order book depth or quoted route data;
- spot trade prints if available;
- external reference markets, e.g. BTC, SPY, QQQ, NASDAQ futures, gold, oil;
- news/event timestamps from public feeds;
- earnings/calendar/event metadata;
- social/news sentiment from public sources;
- perps BBO/order book as a related pressure feed when spot book is missing.

Do not use illegal inside information. The system should use public or licensed data only.

## First Test Result

Command run on 2026-07-27:

```bash
python3 collector/spot_market_field_backtest.py \
  --tickers COIN,MSTR,RKLB,AMD,NVDA,AAPL,SPY,QQQ \
  --horizon 60 \
  --target-pct 0.5 \
  --stop-pct 0.35 \
  --score-threshold 1.25 \
  --step 5
```

Summary:

| Ticker | Predictions | Wins | Losses | Timeouts | Win Rate | Avg Return |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RKLB | 17 | 9 | 8 | 0 | 52.9% | +0.1000% |
| AMD | 15 | 7 | 7 | 1 | 46.7% | +0.0615% |
| MSTR | 30 | 11 | 16 | 3 | 36.7% | -0.0141% |
| COIN | 20 | 4 | 15 | 1 | 20.0% | -0.1597% |
| AAPL | 10 | 1 | 7 | 2 | 10.0% | -0.1694% |
| NVDA | 7 | 0 | 4 | 3 | 0.0% | -0.1627% |
| QQQ | 8 | 0 | 2 | 6 | 0.0% | -0.0785% |
| SPY | 0 | 0 | 0 | 0 | n/a | n/a |

## Autopsy

The first proxy signal is not reliable enough for trade execution.

What worked:

- RKLB and AMD showed weak positive expectancy under this specific target/stop/horizon.
- The model correctly skipped SPY because the signal threshold did not trigger often enough.

What failed:

- COIN, AAPL, NVDA and QQQ were negative.
- High volume ratio often marked exhaustion rather than continuation.
- COIN losses frequently had strong-looking scores, meaning the score formula overweights volume/momentum and underweights reversal risk.
- The model lacks true spot order book depth, spread, slippage, and trade-flow confirmation.

Immediate improvements:

- Add an exhaustion penalty when volume ratio is extreme after a fast move.
- Require pullback/retest confirmation instead of buying every breakout-pressure signal.
- Add market-specific calibration; one threshold does not fit COIN, AAPL, RKLB and QQQ.
- Add public news/event filters, especially for single stocks.
- Add related-market context, e.g. BTC/MSTR/COIN, QQQ/NVDA/AMD.
- Use perps order book/trade flow as a proxy pressure feed where related spot order book data is unavailable.

## Command

```bash
cd market-ops-lab
source .venv/bin/activate
python3 collector/spot_market_field_backtest.py --tickers COIN,MSTR,RKLB,AMD,NVDA,AAPL,SPY,QQQ --horizon 60 --target-pct 0.5 --stop-pct 0.35
```

Results are stored in:

- `spot_field_backtests`
- `spot_field_backtest_events`

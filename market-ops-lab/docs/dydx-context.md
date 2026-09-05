# dYdX Context Collector

Date: 2026-07-27

## Purpose

dYdX gives public perps order book, trades, candles, market metadata, funding and open interest. This is useful as an external confirmation layer for Arcus signals.

For example:

```text
COIN/MSTR spot signal
  -> check BTC-USD pressure on Arcus perps
  -> check BTC-USD pressure on dYdX perps
  -> accept/watch/reject based on agreement
```

## Commands

Collect dYdX context:

```bash
python3 collector/dydx_context.py --tickers BTC-USD,ETH-USD,SOL-USD
```

Run combined context simulation:

```bash
python3 collector/context_trade_simulation.py --ticker COIN --related-perp BTC-USD
```

## Tables

- `dydx_markets`
- `dydx_orderbook_features`
- `dydx_trades`
- `dydx_trade_flow_features`
- `dydx_candles`

## Notes

TradingView is not used as a data source. TradingView can be used later as a charting library/datafeed target for our own backend data.

# Next Data Sources Status

Date: 2026-07-27

## 1. Spot Order Book Depth

Status: not found as a public Arcus spot endpoint.

Arcus spot is documented as RFQ-based. The RFQ model sources indicative maker liquidity and settles the single winning firm quote atomically. That is different from a visible central limit order book.

Implication:

- We should not claim to detect spot order book walls/depth from Arcus public spot data.
- For spot, we currently use spot quote, spot candles, and 24h volume/change.
- For liquidity pressure, use perps order book as a proxy where a related perps market exists.

Source:

- https://docs.arcus.xyz/concepts/spot-rfq
- https://docs.arcus.xyz/api-reference/marketmetadata/get-spot-market-overview

## 2. Trade Prints / Flow

Status: available for Arcus perps.

REST:

- `GET /v1/trades?market=BTC-USD`

WebSocket:

- `trades` channel

This gives price, size, side, trade id, timestamp and sequence number. It can drive trade-flow imbalance.

Source:

- https://docs.arcus.xyz/api-reference/public/get-recent-public-trades
- https://docs.arcus.xyz/api-reference/market-data/trades

## 3. Spread and Slippage

Status: available for Arcus perps.

REST:

- `GET /v1/bbo/{market}`
- `GET /v1/l2OrderBook/{market}`

WebSocket:

- `bbo`
- `l2Orderbook`
- `l2OrderbookUpdates`

Derived fields:

- spread bps;
- microprice;
- depth imbalance;
- buy/sell slippage for target notional;
- bid/ask depth notional;
- sequence id / gap checks.

Source:

- https://docs.arcus.xyz/api-reference/public/get-best-bid-offer-bbo
- https://docs.arcus.xyz/api-reference/public/get-l2-orderbook-snapshot

## 4. News/Event Feeds

Status: not yet implemented.

Candidate public sources:

- CoinDesk RSS;
- Cointelegraph RSS;
- SEC press releases / filings feeds;
- company investor-relations RSS where available;
- GitHub release/activity feeds for crypto projects;
- earnings-calendar provider later.

Do not use inside information. Use public, licensed, or user-owned sources only.

## 5. Earnings / Calendar Data

Status: not yet implemented.

Needed for stock tokens because large moves often align with:

- earnings;
- guidance;
- product events;
- regulatory filings;
- macro data releases;
- Fed/CPI/NFP events.

This likely needs a dedicated public or paid API. Until then, the model should treat unknown event risk as an uncertainty penalty.

## 6. Related-Market Context

Status: initial config added.

Config file:

- `collector/market_context_config.json`

Initial clusters:

- `BTC/MSTR/COIN`
- `QQQ/NVDA/AMD/MU/SMCI`
- megacap tech
- metals/energy
- crypto beta

## 7. Perps Order Book As Proxy Pressure

Status: implemented.

Collector:

```bash
python3 collector/perps_proxy_context.py --markets BTC-USD,COIN-USD,NVDA-USD,AMD-USD,QQQ-USD
```

Tables:

- `perps_proxy_features`
- `related_market_clusters`

The proxy captures:

- BBO;
- spread bps;
- microprice edge;
- bid/ask depth imbalance;
- simulated slippage for $100 buy/sell;
- recent trade-flow imbalance.

# External Data Roadmap

Date: 2026-07-27

## Why We Need External Data

Arcus data tells us what is happening inside Arcus. To predict better, the Market Field model also needs context from outside Arcus:

- broader crypto market movement;
- related assets;
- macro/index pressure;
- public news/events;
- earnings/calendar events;
- social/sentiment shocks;
- reference exchange liquidity.

This helps distinguish:

- real continuation;
- local Arcus mispricing;
- exhaustion after a broad market move;
- one-market anomaly with no external confirmation.

## Data Sources To Add

### 1. CoinGecko / GeckoTerminal

Use for:

- BTC/ETH/SOL reference prices;
- market cap/volume;
- 24h/7d changes;
- category movement;
- DEX/on-chain token context through GeckoTerminal.

Current connector:

```bash
python3 collector/coingecko_context.py --history-days 1 --store-assets
```

API key is optional at prototype stage. If needed, store it in:

```text
Robinhood_ops/secrets/coingecko.env
```

First connector test:

- Keyless API worked for ping and current prices.
- Stored current prices for BTC, ETH, SOL, LINK, HYPE and DYDX.
- Stored one day of Bitcoin market-chart samples.
- Subsequent historical chart calls hit HTTP 429 rate limits.

Practical recommendation: create a free CoinGecko Demo API key before relying on historical pulls. The connector already reads:

```text
COINGECKO_API_KEY=
```

from `Robinhood_ops/secrets/coingecko.env`.

### 2. Public News Feeds

Use for:

- earnings;
- listings/delistings;
- regulatory news;
- company announcements;
- crypto protocol events;
- ETF/index/macro shocks.

Candidate sources:

- RSS feeds from official companies/projects;
- SEC filings for equities;
- CoinDesk/Cointelegraph/Decrypt feeds for crypto context;
- GitHub release/activity for crypto projects;
- economic calendar APIs if available.

### 3. Related-Market Clusters

Initial clusters:

- BTC, COIN, MSTR, crypto equities.
- ETH, SOL, crypto beta assets.
- NVDA, AMD, MU, SMCI, QQQ.
- SPY, QQQ, mega-cap tech.
- GLD, SLV, USO.

The model should compute whether a ticker is:

- leading its cluster;
- lagging its cluster;
- diverging from its cluster;
- confirming the cluster move.

### 4. Order Book / Trade Flow

Best source for the liquidity-field model:

- Arcus perps L2/BBO/trades;
- spot order book if Arcus exposes it later;
- external exchange depth if licensed and relevant.

Until true spot depth exists, use:

- spot candles;
- spot quote;
- related perps book;
- external crypto reference markets.

### 5. Zerion Wallet / Perps Context

Use Zerion for:

- wallet portfolio value;
- token and DeFi positions;
- wallet transaction history;
- PnL and exposure context;
- manual perps execution planning through Zerion's Hyperliquid-backed perps surface;
- post-trade reconciliation.

Do not use Zerion as the primary prediction feed unless direct market/order-book endpoints are verified. Zerion should answer:

```text
Can this wallet safely take the proposed trade size?
```

Arcus/dYdX/Hyperliquid market data should answer:

```text
Is this market setup worth trading?
```

### 6. GammaFi / Project 0 Yield-Agent Context

Use GammaFi and Project 0 for:

- Solana yield-agent monitoring;
- p0SOL share-price and APY snapshots;
- TVL, 24h volume, depositors, and remaining capacity;
- current strategy holdings and rebalances;
- Project 0 venue/security/risk context;
- comparison against perps opportunities and native SOL staking.

The model should answer:

```text
Is capital better deployed into a directional trade, a yield-agent allocation, or no action?
```

Store:

- source URL;
- fetched timestamp;
- share price;
- current APY;
- solver-predicted APY;
- realized APY;
- TVL;
- 24h volume;
- depositor count;
- capacity;
- performance fee;
- withdrawal fee;
- strategy holdings;
- raw page/API payload.

Until a stable API is verified, capture snapshots manually or through a browser/scraper with timestamped raw data.

## Public Data Only

Do not use inside information. The project should rely only on public, licensed, or user-owned data.

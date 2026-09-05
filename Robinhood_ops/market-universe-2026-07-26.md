# Arcus Market Universe

Snapshot date: 2026-07-26
Environment: mainnet
Source: `GET https://api.arcus.xyz/v1/markets`

Arcus currently returns 43 perpetual markets across four categories: crypto, equities, commodities, and indices. At the time of this snapshot, 37 had mids available from `GET /v1/mids`.

## Markets

| Market | Asset | Category | Type | Status |
| --- | --- | --- | --- | --- |
| BTC-USD | Bitcoin | CRYPTO | PERPETUAL | ONLINE |
| ETH-USD | Ethereum | CRYPTO | PERPETUAL | ONLINE |
| SOL-USD | Solana | CRYPTO | PERPETUAL | ONLINE |
| HYPE-USD | Hyperliquid | CRYPTO | PERPETUAL | ONLINE |
| DYDX-USD | dYdX | CRYPTO | PERPETUAL | ONLINE |
| ZEC-USD | Zcash | CRYPTO | PERPETUAL | ONLINE |
| LIT-USD | Lighter | CRYPTO | PERPETUAL | ONLINE |
| XRP-USD | XRP | CRYPTO | PERPETUAL | ONLINE |
| CASHCAT-USD | CashCat | CRYPTO | PERPETUAL | ONLINE |
| AMD-USD | Advanced Micro Devices | EQUITIES | PERPETUAL | ONLINE |
| INTC-USD | Intel | EQUITIES | PERPETUAL | ONLINE |
| F-USD | Ford Motor Company | EQUITIES | PERPETUAL | OFFLINE |
| BAC-USD | Bank of America | EQUITIES | PERPETUAL | OFFLINE |
| CCL-USD | Carnival | EQUITIES | PERPETUAL | OFFLINE |
| GOOGL-USD | Alphabet | EQUITIES | PERPETUAL | ONLINE |
| META-USD | Meta Platforms | EQUITIES | PERPETUAL | ONLINE |
| MU-USD | Micron Technology | EQUITIES | PERPETUAL | ONLINE |
| BABA-USD | Alibaba Group | EQUITIES | PERPETUAL | ONLINE |
| HOOD-USD | Robinhood Markets | EQUITIES | PERPETUAL | ONLINE |
| CRCL-USD | Circle Internet Group | EQUITIES | PERPETUAL | ONLINE |
| RVI-USD | Robinhood Ventures Fund I | EQUITIES | PERPETUAL | OFFLINE |
| NVDA-USD | NVIDIA | EQUITIES | PERPETUAL | ONLINE |
| TSLA-USD | Tesla | EQUITIES | PERPETUAL | ONLINE |
| AAPL-USD | Apple | EQUITIES | PERPETUAL | ONLINE |
| AMZN-USD | Amazon.com | EQUITIES | PERPETUAL | ONLINE |
| MSFT-USD | Microsoft | EQUITIES | PERPETUAL | ONLINE |
| SNDK-USD | SanDisk | EQUITIES | PERPETUAL | ONLINE |
| DRAM-USD | Roundhill Memory ETF | EQUITIES | PERPETUAL | ONLINE |
| PLTR-USD | Palantir Technologies | EQUITIES | PERPETUAL | ONLINE |
| CRWV-USD | CoreWeave | EQUITIES | PERPETUAL | ONLINE |
| ORCL-USD | Oracle | EQUITIES | PERPETUAL | ONLINE |
| SPCX-USD | Space Exploration Technologies Corp | EQUITIES | PERPETUAL | ONLINE |
| BE-USD | Bloom Energy | EQUITIES | PERPETUAL | ONLINE |
| USAR-USD | USA Rare Earth | EQUITIES | PERPETUAL | ONLINE |
| COIN-USD | Coinbase Global | EQUITIES | PERPETUAL | ONLINE |
| SKHY-USD | SK Hynix | EQUITIES | PERPETUAL | ONLINE |
| GLD-USD | SPDR Gold Shares | COMMODITIES | PERPETUAL | ONLINE |
| SLV-USD | iShares Silver Trust | COMMODITIES | PERPETUAL | ONLINE |
| USO-USD | United States Oil Fund | COMMODITIES | PERPETUAL | ONLINE |
| SPY-USD | SPDR S&P 500 ETF Trust | INDICES | PERPETUAL | ONLINE |
| QQQ-USD | Invesco QQQ Trust | INDICES | PERPETUAL | ONLINE |
| VT-USD | Vanguard Total World Stock ETF | INDICES | PERPETUAL | OFFLINE |
| SGOV-USD | iShares 0-3 Month Treasury Bond ETF | INDICES | PERPETUAL | OFFLINE |

## API Notes

- Market discovery: `GET /v1/markets`
- Mid prices: `GET /v1/mids`
- Candles: `GET /v1/candles?market=BTC-USD&timeframe=1m&to=<unix-micros>&countback=200`
- Live market metadata: WebSocket `markets` channel
- Live order book: WebSocket `l2Orderbook` channel
- Live candles: WebSocket `candles` channel
- Live top-of-book: WebSocket `bbo` channel

Docs:

- https://docs.arcus.xyz/api-reference/public/get-markets
- https://docs.arcus.xyz/api-reference/public/get-all-mid-prices
- https://docs.arcus.xyz/api-reference/public/get-ohlcv-candles
- https://docs.arcus.xyz/api-reference/market-data/l2orderbook
- https://docs.arcus.xyz/api-reference/market-data/candles

# Arcus Research

Date researched: 2026-07-26

## What Arcus Is

Arcus is a decentralized exchange built by the team behind dYdX, in partnership with Robinhood Chain. Its stated focus is tokenized equities, cryptoassets, and perpetual futures. Arcus positions itself as a self-custodial trading venue: users keep custody through wallet-based accounts while Arcus provides exchange and API infrastructure.

Sources:

- https://arcus.xyz/
- https://docs.arcus.xyz/
- https://arcus.xyz/blog/welcome-to-arcus
- https://privy.io/blog/powering-24-7-global-markets-with-arcus

## Product Surface

Arcus currently presents:

- 24/7 stock token trading;
- zero-fee spot stock token trading;
- perpetual futures with leverage via beta/waitlist;
- exposure categories including stocks, indices, commodities, and crypto;
- API trading with order management, account data, and market feeds;
- self-custodial account/wallet infrastructure.

The homepage states that Spot Beta is open to eligible users and that Perps Beta opened on July 1, 2026 by cohort. Arcus states it is not available in the United States, United Kingdom, Canada, and other restricted jurisdictions.

Source:

- https://arcus.xyz/

## Technical Claims

The Arcus docs describe the exchange as using an off-chain matching engine with 100k+ orders per second and roughly 20 ms trade confirmations, while custody and settlement remain non-custodial/on-chain.

Source:

- https://docs.arcus.xyz/

## API Overview

Arcus exposes:

- REST API for account management, perpetuals trading, and historical data;
- WebSocket API for real-time market data and order routing;
- public and authenticated endpoints;
- testnet and mainnet base URLs.

Base URLs:

- Mainnet REST: `https://api.arcus.xyz`
- Mainnet WebSocket: `wss://api.arcus.xyz/v1/ws`
- Testnet REST: `https://api.testnet.arcus.xyz`
- Testnet WebSocket: `wss://api.testnet.arcus.xyz/v1/ws`

Source:

- https://docs.arcus.xyz/api-reference/introduction

## Authentication

Arcus uses Ed25519 API keys. The API key is the public half of an Ed25519 key pair, registered against an Ethereum address. The server does not see the private key.

Protected/mutating requests include:

- API key;
- Unix-nanosecond timestamp;
- Ed25519 signature.

REST uses headers:

- `X-API-Key`
- `X-Timestamp`
- `X-Signature`

WebSocket uses envelope fields:

- `apiKey`
- `timestamp`
- `signature`

Registration is authenticated by an Ethereum wallet signature. The `createApiKey` route is REST-only.

Source:

- https://docs.arcus.xyz/api-reference/authentication

## REST Trading

The REST guide frames REST as the simplest first path: one signed request per call. It is intended for getting started, while production or low-latency trading should use WebSocket.

The docs state testnet requests target `https://api.testnet.arcus.xyz`, and new accounts start empty until funded through the testnet app or on-chain deposit flow.

Source:

- https://docs.arcus.xyz/guides/rest-trading

## WebSocket Trading

The WebSocket API is the primary trading interface. One connection multiplexes subscriptions and request/response calls.

Important details:

- connect to `wss://api.testnet.arcus.xyz/v1/ws` on testnet or `wss://api.arcus.xyz/v1/ws` on mainnet;
- channel subscriptions stream market/account updates;
- order methods are asynchronous and return acknowledgements;
- users should subscribe to order/fill channels to observe lifecycle;
- there is no cancel-on-disconnect or dead-man switch;
- resting orders remain until filled, explicitly cancelled, or expired;
- streamed messages include sequence numbers for ordering, gap detection, and resync.

Source:

- https://docs.arcus.xyz/api-reference/websocket
- https://docs.arcus.xyz/guides/websocket-trading

## Spot Indexer

Arcus also exposes a spot indexer API at `https://indexer.spot.arcus.xyz/`. Public docs show trading statistics endpoints, including account-level spot volume, fees, and trade counts over windows such as `1d`, `14d`, `30d`, or `all`.

Source:

- https://indexer.spot.arcus.xyz/

## Robinhood Chain Context

Robinhood announced Robinhood Chain public mainnet as an Arbitrum-based Layer 2 built for real-world assets and DeFi integrations. Stock Tokens are described as available in more than 120 countries, subject to jurisdiction, and usable for 24/7 on-chain trading and broader DeFi collateral/productivity use cases.

Source:

- https://robinhood.com/us/en/newsroom/robinhood-accelerates-global-expansion-robinhood-chain-mainnet-stock-tokens-agentic-trading/

## Market Context

CoinDesk reported on July 25, 2026 that Robinhood Chain real-world assets had grown materially in the preceding two weeks, with tokenized equities starting to trade in larger size, but memecoins and stablecoins still dominating total chain activity.

Source:

- https://www.coindesk.com/business/2026/07/25/robinhood-chain-s-real-world-assets-jump-fivefold-as-tokenized-stocks-start-trading-in-bigger-size

## Key Risks

- Jurisdiction: Arcus states it is not available in the U.S., U.K., Canada, and other restricted jurisdictions.
- Product risk: stock tokens are not the same as direct stock ownership.
- Market risk: tokenized equities may diverge from underlying equities due to liquidity, redemption constraints, trading hours mismatch, or issuer mechanics.
- Leverage risk: perpetuals can create rapid losses, especially with cross-margin.
- Operational risk: no cancel-on-disconnect means any strategy needs its own kill switch.
- Key risk: API/private keys must be handled locally and never committed.
- Data risk: AI-generated trading rationales need evidence trails and should not be treated as execution authority.

## Open Research Gaps

- Confirm the exact API permissions and account state available to the provided key.
- Determine whether the provided key is a public Ed25519 API key, not a private key.
- Map all REST endpoints from the OpenAPI reference.
- Map all WebSocket channels and payloads into a typed schema.
- Verify current Arcus mainnet/testnet feature parity from the changelog before coding.
- Confirm eligibility and jurisdiction constraints before any production use.

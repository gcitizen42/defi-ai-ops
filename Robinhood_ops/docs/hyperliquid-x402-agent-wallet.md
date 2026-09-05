# Hyperliquid, x402, and Agent Wallet Plan

Date: 2026-08-24

## Hyperliquid API

Use Hyperliquid as a direct perps data source and possible execution venue.

Public data endpoint:

```text
POST https://api.hyperliquid.xyz/info
```

Useful public request types:

- `metaAndAssetCtxs` - perp universe, mark price, 24h notional volume, open interest, funding, leverage metadata.
- `allMids` - midpoint prices.
- `l2Book` - current L2 book for one coin.
- `recentTrades` - recent public prints for one coin.
- `candleSnapshot` - historical candles.
- `openOrders` / `frontendOpenOrders` - user account open orders.
- `userFills` - user fills.
- `clearinghouseState` - account margin/positions if queried with the real account address.

Trading endpoint:

```text
POST https://api.hyperliquid.xyz/exchange
```

The exchange endpoint is for signed actions such as:

- place order;
- cancel order;
- update leverage;
- approve API wallet / agent wallet;
- transfer and account-management actions.

## API Wallet / Agent Wallet

Hyperliquid API wallets are also called agent wallets. A master account can approve an API wallet to sign trading actions on behalf of the master or sub-account.

Important rule:

```text
Use the master/sub-account address for account queries.
Use the API wallet only for signing actions.
```

Do not query balances or positions with the agent wallet address, because it can return an empty account result.

Operational plan:

1. Create a fresh Hyperliquid API wallet from `https://app.hyperliquid.xyz/API`.
2. Name it for this project, for example `robinhood-ops-hermes`.
3. Store only the public account address at first.
4. Keep the API wallet private key out of git and outside chat.
5. Start with public data and paper orders.
6. Add signed order support only after we have:
   - a dry-run mode;
   - max notional limit;
   - max daily loss;
   - isolated-margin-only mode;
   - automatic stop and take-profit pairing;
   - SQLite audit log;
   - kill switch.

Suggested local secret file:

```text
Robinhood_ops/secrets/hyperliquid.env
```

Fields:

```bash
HYPERLIQUID_ACCOUNT_ADDRESS=
HYPERLIQUID_AGENT_ADDRESS=
HYPERLIQUID_AGENT_PRIVATE_KEY=
HYPERLIQUID_ENV=mainnet
HYPERLIQUID_MAX_NOTIONAL_USD=100
HYPERLIQUID_MAX_LEVERAGE=2
HYPERLIQUID_DRY_RUN=1
```

## x402

x402 is useful for machine-to-machine payments, not for perps order signing.

Use x402 / Agentic Wallet for:

- paying for premium APIs;
- buying data from paid endpoints;
- allowing agents to pay for tools with spending limits;
- offering our own paid signal/research API later;
- agent-to-agent commerce if we expose a service.

Do not use x402 as the Hyperliquid trading wallet. Hyperliquid orders need Hyperliquid-compatible signed actions through the exchange endpoint.

## Coinbase Agentic Wallet

Coinbase Agentic Wallet CLI can give an agent a wallet with spending limits, x402 payments, send, and token-trade abilities on supported networks.

Fit for this project:

- good for tool/data payments;
- good for budgeted API consumption;
- not the first choice for Hyperliquid perps execution.

## Architecture

```text
Hermes agent
  -> Hyperliquid public data collector
  -> Arcus/dYdX/Coingecko/Zerion context
  -> volatility and microstructure model
  -> candidate trade plan
  -> human approval
  -> manual Zerion/Hyperliquid execution first
  -> later: Hyperliquid API wallet signed execution with dry-run disabled

x402 / Agentic Wallet
  -> pay for external data/tool calls
  -> enforce API spending budgets
  -> optionally sell our own computed market signals
```

## Safety Boundary

No live agent execution until:

- the strategy has a positive paper-trade record after fees;
- the stop order is submitted atomically or immediately after entry;
- the agent wallet is isolated and revocable;
- the bot can stop trading after a daily loss limit;
- all decisions are stored in SQLite.

## Sources

- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint
- https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/nonces-and-api-wallets
- https://docs.x402.org/core-concepts/wallet
- https://docs.cdp.coinbase.com/x402/welcome
- https://docs.cdp.coinbase.com/agentic-wallet/cli/welcome


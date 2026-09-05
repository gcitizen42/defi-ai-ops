# Toolbox

Selected scripts from the DeFi AI Ops workspace.

## Market Data

Run these commands from `market-ops-lab/` after completing its [setup](../market-ops-lab/collector/README.md).

Collect an Arcus market snapshot:

```bash
python3 collector/arcus_collector.py --once --rest-only
```

Collect Hyperliquid market context:

```bash
python3 collector/hyperliquid_context.py --markets BTC,ETH,SOL --lookback-minutes 240
```

Collect CoinGecko context:

```bash
python3 collector/coingecko_context.py --history-days 1 --store-assets
```

## Research Models

Find historical states similar to the current market:

```bash
python3 collector/spot_present_analog.py --ticker COIN --horizon 60
```

Run a paper-trade monitor that does not place orders:

```bash
python3 collector/paper_trade_watch.py --market BTC-USD --side long --notional 10
```

## On-Chain Operations

Install and verify the TypeScript toolkit:

```bash
cd onchain-ops-toolkit
npm install
npm run build
npm test
```

Inspect modules enabled on Safe accounts:

```bash
npm run start --workspace safe-module-inspector -- --owner 0xYOUR_OWNER_ADDRESS --chains ethereum,gnosis
```

Summarize tBTC redemption treasury fees:

```bash
npm run start --workspace threshold-fee-monitor -- 2025-01-01 2026-01-01
```

List live wallets registered by the tBTC Bridge:

```bash
npm run start --workspace tbtc-wallet-registry
```

See the [on-chain toolkit guide](../onchain-ops-toolkit/README.md) for configuration.

Export Safe multisig history:

```bash
cd references/gnosis-safe-stats
python3 safe_history_rawdata.py YOUR_SAFE_ADDRESS UNUSED --outfile safe-history.csv
```

Add `--fetch-chain` and a real RPC URL in place of `UNUSED` when gas enrichment is needed. See the [Safe analytics guide](../references/gnosis-safe-stats/README.md).

## Protocol Simulation

Simulate a transaction with Tenderly:

```bash
cd protocol-security-lab/challenge-simulations
cp tenderly.env.example tenderly.env
python3 tenderly_simulate.py \
  --from 0xYOUR_SENDER \
  --to 0xTARGET_CONTRACT \
  --input 0xCALLDATA
```

The simulator uses a local ignored credentials file and does not broadcast the transaction. See the [simulation guide](../protocol-security-lab/challenge-simulations/README.md).

## Requirements

| Area | Requirements |
| --- | --- |
| Market collectors | Python 3.11+, packages in `market-ops-lab/collector/requirements.txt` |
| Safe analytics | Python 3.10+, packages in `references/gnosis-safe-stats/requirements.txt` |
| On-chain operations | Node.js 20+, packages locked by `onchain-ops-toolkit/package-lock.json`; archive RPC for historical wallet scans |
| Tenderly simulator | Python 3.11+, Tenderly simulation credentials; Foundry `cast` for encoded helper inputs |

All databases, exports, keys, and local environment files stay outside git.

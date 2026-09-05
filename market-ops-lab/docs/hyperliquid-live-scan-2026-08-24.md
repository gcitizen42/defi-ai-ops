# Hyperliquid Live Scan

Date: 2026-08-24

## Command

```bash
cd /Users/Citizen42/Documents/DeFi-dApps/market-ops-lab
source .venv/bin/activate
python3 collector/hyperliquid_context.py --limit 12 --min-volume-usd 3000000 --lookback-minutes 180 --trade-limit 100 --levels 20
```

## Result

The Hyperliquid public API integration worked and stored:

- market metadata;
- mark price, 24h volume, open interest, funding;
- L2 book features;
- recent trade-flow features;
- 1 minute candles;
- candidate scan rows.

## Prototype Candidates

The first scanner pass favored downside continuation in volatile coins. These are research candidates, not automatic execution orders.

### PURR Short

```text
Entry: 0.13251
Take profit: 0.12787215
Stop loss: 0.13463016
Target: 3.5%
Stop: 1.6%
Reward/risk: 2.1875
Confidence: 0.764
```

Why it passed:

- 1m, 5m, 15m, and 60m returns were negative.
- Recent flow sample was fully sell-heavy.
- 60m move showed strong volatility expansion.

Main risks:

- Spread was 10.56 bps, close to the initial rejection threshold.
- Market is volatile enough to wick through a stop.

### ZRO Short

```text
Entry: 1.1286
Take profit: 1.089099
Stop loss: 1.1466576
Target: 3.5%
Stop: 1.6%
Reward/risk: 2.1875
Confidence: 0.702
```

Why it passed:

- 15m, 60m, and 24h trend were bearish.
- Recent flow sample was fully sell-heavy.
- Spread was acceptable.

### UNI Short

```text
Entry: 4.3158
Take profit: 4.164747
Stop loss: 4.3848528
Target: 3.5%
Stop: 1.6%
Reward/risk: 2.1875
Confidence: 0.667
```

Why it passed:

- 15m, 60m, and 24h trend were bearish.
- Strong sell-heavy recent flow.
- Lower spread than PURR.

### PENGU Short

```text
Entry: 0.009415
Take profit: 0.009085475
Stop loss: 0.00956564
Target: 3.5%
Stop: 1.6%
Reward/risk: 2.1875
Confidence: 0.605
```

Why it passed:

- Negative 1m, 15m, and 60m structure.
- Sell-heavy flow.
- 24h positive move may create reversal/exhaustion context.

## Best Practical Manual Test

For a first manual perp test, `UNI short` is cleaner than `PURR short` despite lower score, because the spread is materially tighter.

Use:

```text
Market: UNI
Side: Short
Entry reference: 4.3158
Take profit: 4.164747
Stop loss: 4.3848528
Max leverage: 2x
Margin: isolated
Hold window: 30m to 4h
```

Reject if:

- price trades above the stop before entry;
- spread widens materially;
- BTC/ETH both reverse strongly upward;
- the setup has not moved toward target within the hold window.


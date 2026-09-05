# Market Visual Intelligence Layer

Date: 2026-07-26
Status: design direction

## Product Idea

Build a market-wide visual analytics layer that makes Arcus markets feel like a live liquidity/weather map:

- waves: volatility and directional movement;
- ripples: trades and order flow impacts;
- water depth: order book liquidity;
- currents: persistent buy/sell pressure;
- tides: funding, open interest, and market-wide regime shifts;
- storms: volatility shocks, thin books, and liquidation-risk conditions.

The goal is to expose powerful insights across all markets and produce trade candidates with:

- probability estimate;
- expected return;
- expected timeframe;
- drawdown estimate;
- liquidity/slippage feasibility;
- risk tier;
- accept/reject decision.

## Important Boundary

The system cannot guarantee only profitable trades.

The correct standard is:

```text
Only execute trades with positive expected value after estimated fees, spread, slippage, funding, and failure probability.
```

For high-risk/high-reward opportunities, the proposed capital allocation cap is:

```text
max_high_risk_allocation = 30% of available strategy funds
```

That cap should still be split across multiple trades or rejected entirely when no high-quality setup exists.

## Visual Formula Families

### 1. Liquidity Depth

Measures how much notional liquidity exists near the current price.

```text
bid_depth_notional = sum(bid_price_i * bid_size_i)
ask_depth_notional = sum(ask_price_i * ask_size_i)
```

Visual:

- deeper water = more liquidity;
- shallow water = risky/slippage-prone;
- cliffs = liquidity gaps.

### 2. Order Book Imbalance

```text
imbalance = bid_depth / (bid_depth + ask_depth)
```

Interpretation:

- above `0.5`: more bid support than ask liquidity;
- below `0.5`: more ask pressure than bid liquidity;
- extreme values can predict short-term movement or spoof/fake pressure.

Visual:

- green current when bid-heavy;
- red current when ask-heavy.

### 3. Microprice

Microprice estimates short-term pressure better than midpoint.

```text
mid = (best_bid + best_ask) / 2
microprice = (best_ask * bid_size + best_bid * ask_size) / (bid_size + ask_size)
micro_edge = (microprice - mid) / mid
```

Visual:

- microprice above mid = upward ripple;
- microprice below mid = downward ripple.

### 4. Spread Cost

```text
spread = best_ask - best_bid
spread_bps = spread / mid * 10000
```

Visual:

- tight spread = calm surface;
- wide spread = turbulent/expensive entry.

### 5. Slippage Curve

Simulate market order entry/exit through order book levels.

```text
avg_fill_price = sum(price_i * filled_size_i) / total_size
slippage_bps = abs(avg_fill_price - mid) / mid * 10000
```

Visual:

- shallow slope = good execution;
- steep slope = dangerous execution.

### 6. Trade Flow Imbalance

```text
flow_imbalance = (aggressive_buy_volume - aggressive_sell_volume)
               / (aggressive_buy_volume + aggressive_sell_volume)
```

Visual:

- ripples moving up when buyers are lifting asks;
- ripples moving down when sellers are hitting bids.

### 7. Volatility Wave

```text
return_t = ln(close_t / close_t-1)
realized_vol = stdev(return_t over window) * sqrt(periods_per_year)
```

Visual:

- bigger waves = higher volatility;
- flat water = low opportunity or low risk;
- chaotic waves = reject unless strategy is built for volatility.

### 8. Volume Shock

```text
volume_zscore = (current_volume - mean(volume_window)) / stdev(volume_window)
```

Visual:

- expanding rings when volume is abnormal.

### 9. Mark / Oracle / Last Divergence

```text
mark_oracle_divergence = (mark_price - oracle_price) / oracle_price
last_mark_divergence = (last_trade_price - mark_price) / mark_price
```

Visual:

- distortion field when market price and reference price diverge.

### 10. Funding and Open Interest Pressure

```text
oi_change = (open_interest_t - open_interest_t-n) / open_interest_t-n
funding_pressure = funding_rate_zscore + oi_change_zscore
```

Visual:

- tide rising = crowded leverage;
- tide turning = possible squeeze/reversal risk.

## Probability Extraction

For every candidate condition, query historical outcomes:

```text
P(target before stop | current_setup)
```

Example:

```text
setup:
  imbalance > 0.65
  spread_bps < 4
  flow_imbalance > 0.25
  volume_zscore > 1.5
  realized_vol within acceptable band

outcome:
  hit +1.0% before -0.4% within 30 minutes
```

The bot should store:

- sample count;
- win rate;
- average win;
- average loss;
- median time to target;
- median time to stop;
- max adverse excursion;
- max favorable excursion;
- expected value after costs.

## Trade Candidate Score

```text
expected_value = P(win) * avg_win - P(loss) * avg_loss - costs

score =
  historical_edge
  + liquidity_quality
  + flow_confirmation
  + regime_fit
  + risk_reward_quality
  - slippage_penalty
  - spread_penalty
  - uncertainty_penalty
  - funding_penalty
```

Decision:

```text
if expected_value <= 0:
  reject
if sample_count < minimum_sample_count:
  reject
if slippage_too_high:
  reject
if max_loss_exceeds_risk_budget:
  reject
if score < threshold:
  reject
else:
  propose trade
```

## Suggested App Views

### 1. Market Ocean

All markets on one screen:

- size = volume;
- color = direction/flow;
- depth = order book liquidity;
- pulse = trade frequency;
- border = risk status;
- grouped by crypto, equities, commodities, indices.

### 2. Liquidity Map

For a selected market:

- bid/ask depth heatmap;
- spread over time;
- slippage curve by order size;
- microprice vs mid.

### 3. Probability Lab

Interactive filters:

- market;
- timeframe;
- target profit;
- stop loss;
- max hold time;
- imbalance threshold;
- spread threshold;
- volume shock threshold.

Output:

- probability of target before stop;
- expected value;
- median time to target;
- max drawdown distribution;
- reject/accept.

### 4. Trade Radar

Ranked candidate trades:

- market;
- direction;
- expected value;
- probability;
- timeframe;
- required capital;
- max risk;
- reason;
- reject reason if blocked.

### 5. High-Risk Allocation Panel

Shows whether any candidate qualifies for the 30% high-risk bucket.

Rules:

- high-risk bucket max: 30%;
- no single trade gets the full bucket by default;
- require higher EV threshold;
- require explicit testnet/paper evidence;
- require stop, take-profit, timeout.

## First Build Step

Add feature-generation tables from the collector:

- `market_features_1m`
- `orderbook_features`
- `trade_flow_features`
- `candidate_setups`
- `setup_outcomes`

Then build the first dashboard panel:

```text
Market Ocean -> click market -> liquidity map -> probability lab
```

This keeps the project focused on collecting accurate data and turning it into visual, probabilistic insight before any execution logic.

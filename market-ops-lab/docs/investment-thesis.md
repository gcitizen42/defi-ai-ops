# Investment Thesis

Date: 2026-08-24

## Core Thesis

The project should not assume short-horizon direction can be reliably predicted. The stronger thesis is:

```text
Direction is noisy.
Volatility is forecastable.
Profitable trading comes from combining volatility forecasts, liquidity state, disciplined entry, and strict risk sizing.
```

The broader control-center thesis is:

```text
Capital should move only when the selected avenue beats the alternatives on risk-adjusted expected value.
```

That means the system compares perps trades, spot trades, idle stablecoin, and yield-agent positions before recommending action.

For perps, the first-order question is not only "will price go up or down?" It is:

```text
How large is the next likely move, over what window, and can we enter with a stop/target structure where payout beats risk after fees and slippage?
```

## Engle / ARCH Foundation

Robert F. Engle's 2003 Nobel Memorial Prize in Economic Sciences recognized methods for analyzing economic time series with time-varying volatility, specifically the ARCH framework.

The canonical ARCH(q) model:

```text
epsilon_t = z_t * sqrt(h_t)
h_t = omega + sum(alpha_i * epsilon_{t-i}^2)
```

Where:

- `epsilon_t` is the residual shock in returns;
- `z_t` is an independent standardized innovation;
- `h_t` is conditional variance using information available at `t-1`;
- `omega > 0` and `alpha_i >= 0` keep variance positive.

Bollerslev's GARCH(p,q) extension adds lagged conditional variance:

```text
h_t = omega + sum(alpha_i * epsilon_{t-i}^2) + sum(beta_j * h_{t-j})
```

The practical workhorse is GARCH(1,1):

```text
h_t = omega + alpha * epsilon_{t-1}^2 + beta * h_{t-1}
```

The persistence term `alpha + beta` describes how slowly volatility shocks decay. In liquid markets this is often high, which matches the observed tendency for high-volatility periods to cluster.

## Trading Implication

Short-horizon return signs are often close to noise. Squared or absolute returns are more structured. That means our system should forecast:

- expected volatility;
- probability of target before stop;
- stop distance needed to avoid normal noise;
- leverage allowed by current volatility;
- whether liquidity can absorb entry/exit without destroying edge.

This supports volatility-targeted sizing:

```text
position_size = target_risk / forecast_volatility
```

Higher forecast volatility reduces size. Lower forecast volatility allows larger size only if liquidity and spread also pass.

## How This Changes The Bot

The bot should not chase the asset with the biggest move. It should search for setups where:

- forecast volatility is expanding enough to make a target reachable;
- spread and slippage are small relative to the target;
- order book imbalance and trade flow agree with the intended side;
- the stop is outside ordinary noise but inside the maximum allowed loss;
- related markets confirm or at least do not contradict;
- funding does not erase expected edge;
- position size is scaled down in violent regimes.

If no directional setup clears the bar, the bot should be allowed to recommend:

- wait in cash/stables;
- park SOL in a monitored yield-agent position;
- reduce exposure;
- collect more data.

## Yield-Agent Thesis

GammaFi / Project 0 p0SOL adds a useful model for non-directional return:

```text
Deposit SOL.
Receive a liquid receipt token.
Let an economic agent allocate across Solana venues.
Track share-price appreciation and risk exposure.
```

This is structurally different from perps:

- perps require entry, stop, take profit, liquidation control, and timing;
- yield agents require protocol-risk scoring, share-price monitoring, APY validation, and withdrawal/liquidity checks.

The control center should treat p0SOL and similar products as an experimental yield lane. It is useful when:

- directional trade quality is low;
- expected yield is competitive against native SOL staking;
- TVL and strategy concentration are stable;
- Project 0 / underlying venue risk remains within limits.

The control center should reject or reduce yield-agent allocation when:

- share-price growth stalls or reverses;
- APY comes from fragile leverage loops;
- TVL exits accelerate;
- holdings concentrate in one venue or strategy;
- Solana market volatility increases liquidation risk.

## Models To Add

Priority:

- realized volatility over 1m, 5m, 15m, 1h windows;
- EWMA volatility;
- GARCH(1,1) or rolling ARCH-style conditional variance;
- volatility regime classifier;
- target-before-stop simulation using forecast volatility;
- liquidity-adjusted expected value.

Later:

- EGARCH or GJR-GARCH for asymmetric volatility response;
- realized-volatility models from high-frequency candles;
- multivariate correlation and DCC-GARCH for BTC/ETH/SOL/alt clusters;
- Bayesian rolling parameter updates.

## Required Candidate Output

Every perps trade plan should include:

- forecast volatility;
- entry;
- stop;
- take profit;
- max hold window;
- reward/risk;
- expected fees and slippage;
- liquidation distance;
- position size from volatility targeting;
- explicit reasons to reject the trade.

Every yield-agent allocation plan should include:

- deposit asset;
- receipt token;
- share price;
- current APY;
- realized APY;
- predicted APY if available;
- TVL;
- capacity;
- strategy holdings;
- protocol-risk score;
- withdrawal fee;
- exit rule;
- reason it beats cash or native staking.

## Limits

ARCH/GARCH does not predict news. It estimates conditional variance from past data. It should improve sizing and stop placement, not create certainty. Direction still requires separate evidence from microstructure, flow, trend, events, and cross-market confirmation.

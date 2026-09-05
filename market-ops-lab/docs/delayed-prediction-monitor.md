# Delayed Prediction Monitor

Date: 2026-07-27

## Idea

A prediction should not be judged only at the exact horizon boundary.

Example:

```text
Prediction: price likely reaches target within 24h.
Actual: target reached at 27h.
```

That is not the same as a fully wrong prediction. It may mean the model was directionally correct but early.

## Terms

- `base_horizon`: the original prediction window.
- `grace`: extra time allowed to detect late target hits.
- `on_time_hit`: target hit inside base horizon.
- `delayed_hit`: target hit after base horizon but inside grace.
- `stopped_before_hit`: stop hit before target.
- `miss`: neither target nor stop during base + grace.

## Why It Matters

Delayed-hit analysis helps estimate:

- timing error;
- whether the model is early or wrong;
- how long to keep monitoring after the expected window;
- whether a trade should use a wider timeout;
- whether a signal is better as an alert than immediate execution.

## Commands

Backtest delayed hits:

```bash
python3 collector/spot_delayed_prediction_monitor.py \
  --mode backtest \
  --ticker COIN \
  --base-horizon 60 \
  --grace 30 \
  --target-pct 0.5 \
  --stop-pct 0.35
```

Create an active monitor:

```bash
python3 collector/spot_delayed_prediction_monitor.py \
  --mode create-monitor \
  --ticker COIN \
  --base-horizon 60 \
  --grace 30 \
  --target-pct 0.5 \
  --stop-pct 0.35
```

Tables:

- `delayed_prediction_runs`
- `delayed_prediction_events`
- `active_prediction_monitors`

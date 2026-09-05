# Present Analog Model

Date: 2026-07-27

## Idea

Recompose the present from past market behaviour.

Instead of asking a model to predict from scratch, the engine asks:

```text
Which historical states looked most like the current state?
What happened next after those states?
How often did they hit target before stop?
Which feature settings reconstructed the present most usefully?
```

This is a deterministic nearest-neighbour analog model. MiroFish can be used later to generate scenario narratives and parameter sweeps, but the core matching should stay auditable.

## Current Implementation

Script:

```bash
python3 collector/spot_present_analog.py --ticker COIN --horizon 60
```

Tables:

- `spot_present_analog_runs`
- `spot_present_analog_matches`

## Feature Settings Tested

- `momentum_volume`
- `breakout_compression`
- `mean_reversion_guarded`
- `low_noise_trend`

Each setting changes the feature weights used to find historical analogs.

## Output

- best setting by walk-forward hit rate;
- current price;
- predicted return over horizon;
- probability of positive return;
- probability target is hit;
- probability stop is hit;
- top historical matches and their actual future outcomes.

## MiroFish Role

MiroFish should not decide trades directly.

Possible useful role:

- generate alternate feature-weight settings;
- simulate scenario narratives for the top analogs;
- stress-test why the nearest matches may be misleading;
- have multiple agents critique whether a present state is genuinely comparable to historical states.

The mathematical accept/reject gate remains:

```text
historical analog evidence
+ liquidity/spread/slippage checks
+ related-market confirmation
+ event/news risk
- uncertainty penalty
```

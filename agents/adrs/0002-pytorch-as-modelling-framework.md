# ADR 0002: PyTorch as the modelling framework

## Status

Accepted

## Context

The repository trains `GradientBoostingClassifier` and `GradientBoostingRegressor`
from scikit-learn. `requirements.txt` additionally lists `xgboost`, which is
imported nowhere.

The supervisor has directed the team to use PyTorch (SRC-003).

This direction is in tension with a real fact: on small tabular datasets,
gradient boosting generally outperforms neural networks. At the honest sample
size currently available — 44 exact seven-day pairs across four stations, or 140
with a relaxed window — a neural network would be indefensible.

The tension resolves once the training unit changes. Under ADR 0004 the model
trains on lake pixels rather than four points, which raises the sample count by
roughly two orders of magnitude and, more importantly, makes the data a spatial
grid. Convolutional and recurrent architectures can exploit the fact that
neighbouring pixels are neighbours; tree ensembles structurally cannot.

## Decision

Adopt PyTorch as the modelling framework for the predictive layer.

Adopt it **together with** the per-pixel redesign in ADR 0004, not independently.
PyTorch on the four-station framing is rejected as unjustifiable.

Near-term target architecture: a multilayer perceptron over per-pixel features
with three quantile output heads, trained with pinball loss, producing
pessimistic, expected and optimistic trajectories in a single model.

Longer-term target, explicitly out of scope before the pitch: a convolutional
recurrent model over the raster sequence. It is currently blocked by having only
56 timesteps, irregular sampling intervals of 3 to 32 days, and cloud-induced
pixel dropout.

## Consequences

- The supervisor's direction is satisfied, and satisfied for a stated technical
  reason rather than by compliance alone.
- Quantile regression becomes natural: one network with three heads replaces
  three separate scikit-learn fits, and yields the uncertainty bands the project
  needs to represent widening error across satellite gaps.
- scikit-learn is retained for data preparation, metrics, and baseline
  computation. It is removed as the shipped model.
- `xgboost` should be dropped from `requirements.txt` unless a use emerges.
- A dependency on PyTorch is added, which is heavier than the current stack. This
  is accepted.
- If the per-pixel redesign fails to land before the pitch, this ADR's premise
  weakens, and a scikit-learn baseline reported honestly is preferable to a
  neural network fitted to 140 rows. That fallback must be stated, not silently taken.

## Sources

- SRC-003 — supervisor direction to use PyTorch
- ADR 0004 — per-pixel redesign, on which this decision depends
- `src/model/train.py` — current scikit-learn implementation
- Audit finding: 44 exact and 140 relaxed honest training pairs at station granularity

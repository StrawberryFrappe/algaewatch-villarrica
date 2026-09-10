# ADR lq-0011: The per-pixel candidate serves `/forecast` behind a model switch

## Status

Accepted (owner decision, 2026-09-10).

## Context

Two models exist and neither is good. The legacy Gradient Boosting artifact drives
`/risk` and `/forecast`; it loses to its baselines, trains on forward-filled rows,
and reads two station coordinates that are not on the water (BL-027, ADR-sf-0007).
The per-pixel quantile candidate (ADR 0004 D1–D4) is the honest rebuild — real
inputs end to end, no fabricated rows, chronological validation with an embargo
and 2×2 spatial blocks — and it *also* loses to persistence and climatology on the
unweighted mean (MAE 0.001999 vs 0.001402 / 0.001296), while beating climatology on
two of four folds and carrying a well-calibrated interval (coverage 0.8135 against
0.80 nominal).

Until now the candidate was reported but inert: `/model/candidate` returned its
metrics with `serving: false`, and nothing in the product ran on it. The owner's
demo needs the progression to be *shown*, not described — "we had this and it
sucked, now we have this one which sucks less" — with a switch a viewer can
actually flip.

`per_pixel_infer.predict_fai_quantiles` already existed as the load-and-predict
path; it had no caller outside the tests.

## Decision

The candidate serves `/forecast` behind an explicit `model` switch. Four points
shape the implementation:

### D1 — A committed prediction table, not inference on the request path

New `scripts/predict_per_pixel_forecast.py` runs the model over the latest anchor
date of `data/processed/per_pixel_anomaly_dataset.csv` and writes a five-row
`data/processed/per_pixel_forecast_latest.csv` (four stations plus a `lake` row)
with `fai_q10/q50/q90`, `anchor_date`, `target_date`, `horizon_days`, `n_pixels`.

This mirrors `fai_series_raw.csv` and `fai_grid_latest.csv`: the backend reads a
compact committed table, and PyTorch never loads inside a request. It also keeps
the table reproducible without credentials, which is the property the README
already claims for the processed tables.

### D2 — The candidate forecast is date-independent

The dataset's newest anchor is 2026-08-17. The candidate cannot produce a genuine
projection for an arbitrary slider date, so it does not pretend to: there is one
projection, and `anchor_date` / `target_date` ride in the payload rather than being
implied by the request. `/risk/grid` already works this way. The `date` argument
only selects the present-risk baseline for `delta_vs_previous_week`.

### D3 — Station aggregation is presentation, not modelling

Per-pixel quantiles are averaged over the 25 water pixels nearest each station
(equirectangular ordering; the error is far below the 300 m grid). The dataset's
own `station_id` column is **not** usable for this — under ADR 0004 D3 it is the
per-pixel training unit and equals `pixel_id` — so the assignment is done from
coordinates against `src/features/stations.py`.

ADR 0004 already anticipated this: "the four-station framing is retained for
presentation, since the dashboard and the design handoff are built around it, but
is no longer the training unit." Two of those four coordinates are off the water,
so their nearest pixels are shoreline-adjacent; that limitation is inherited from
the station catalog, not introduced here.

### D4 — Confidence is measured against the decision scale

The legacy `confidence_pct` is a classifier probability's distance from a coin
flip. A quantile regressor has no such quantity, so the candidate reports
`100 · (1 − width / 2·threshold)` bounded to 0–100: how tight the q10–q90 band is
relative to the alert threshold it would have to resolve. Scaling by the predicted
value instead collapses to zero whenever the prediction sits near zero — which is
most of this lake most of the time — and would report a well-calibrated interval as
no confidence at all.

## Consequences

- **The map is untouched.** `/risk` and `/risk/grid` are a direct reading of the
  present Sentinel-2 FAI and depend on no model; they stay on the legacy path. The
  `serving: false` in `/model/candidate` remains true *of the map*. The UI says so
  explicitly in the Modelo view. This distinction is load-bearing: the candidate
  is a forecast model with no present-state reading.
- **MI-1 is not weakened.** The candidate still loses to both baselines and the
  Modelo view still reports that beside every metric. Serving a model behind a
  labelled switch is not the same as claiming it is validated, and rule MI-1
  requires the loss to be reported, not the model to be withheld.
- **GATE-MODEL is unaffected.** No training code, no `src/features/`, no dataset
  builder changed. `pytest -q tests/test_model_integrity.py` is unchanged at
  9 passed / 8 xfailed.
- **The visible contrast is stark and should be expected in a demo.** At the
  committed anchor the legacy model reports pucón 81 / sur 69 (ALTO) from
  shoreline vegetation, while the candidate reports every station at 4–5
  (MUY_BAJO) from water pixels only. That divergence is the argument, not a bug.
- A new committed data file must be regenerated whenever the candidate is
  retrained. `scripts/predict_per_pixel_forecast.py` is the one command.
- New `tests/test_candidate_forecast.py` (7 cases) pins the switch, the shape
  parity between paths, the quantile ordering, the 404 fallback, and that the
  legacy numbers are unchanged.

## Sources

- Owner decision, 2026-09-10 (demo-prep session).
- ADR 0004 D1–D4 (continuous per-pixel anomaly, chronological validation, and the
  explicit retention of the four-station framing for presentation).
- ADR-sf-0007 / BL-027 — station coordinates off the water.
- ADR-sf-0010, EV-024 — the candidate's measured verdict against its baselines.
- `src/model/per_pixel_infer.py`, `backend/app/data_source.py`,
  `backend/app/routers/forecast.py`, `scripts/predict_per_pixel_forecast.py`.

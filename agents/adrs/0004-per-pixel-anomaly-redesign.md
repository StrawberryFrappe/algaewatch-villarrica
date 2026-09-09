# ADR 0004: Predict continuous per-pixel FAI anomaly, validated chronologically

## Status

Accepted

## Context

The 2026-09-09 audit established that the predictive layer does not predict. Six
findings, all reproducible from committed CSVs:

1. Bloom rates per station under the pooled absolute threshold of 0.0259 are
   sur 0.98, pucon 0.50, norte 0.00, tolten 0.00. The label tracks location.
2. A rule reading only the station name scores precision 0.97, recall 0.74,
   F1 0.84 — beating the trained classifier's 0.84 / 0.47 / 0.60 on every metric.
3. Thresholding `fai_now` directly reproduces the `bloom_7d` label on 90% of rows,
   so the classifier is re-reading the present rather than forecasting.
4. 218 real readings were forward-filled into 1,356 rows; 85% of rows have
   `fai_now` identical to `fai_lag_1d`, and only 363 unique combinations exist.
5. `StratifiedKFold(shuffle=True)` over those duplicates placed copies of one
   observation in both train and validation folds. CV AUC 0.99 against temporal
   holdout AUC 0.90 is the signature.
6. The regressor's MAE of 0.00865 is 43% worse than persistence at 0.00603.

Three root causes underlie all six: the target is binarised against a pooled
absolute constant, which encodes place; training rows were fabricated by
forward-fill; and validation shuffled time-ordered, duplicated rows.

A fourth constraint follows from fixing the first three. Honest pairing at
station granularity yields 44 exact seven-day pairs, or 140 with a 5-to-9-day
window — far too few to train anything.

## Decision

Four changes, adopted together. They are interdependent; adopting a subset
reintroduces the defect the others fix.

### D1 — Predict a continuous quantity, threshold downstream

Predict FAI, or preferably the change in FAI over the horizon. Apply any alert
threshold afterwards, at serving time.

This preserves magnitude information, decouples the alert policy from the
trained weights so thresholds can change without retraining, enables quantile
uncertainty bands, and removes the binarisation step that encodes location into
the label. Formalised as rule MI-3.

### D2 — Express the target as an anomaly against a local baseline

Compare each location against its own baseline rather than against a
lake-pooled constant, using a standardised deviation. Where sample depth allows,
make the baseline seasonal; with one year of data a rolling window is the honest
approximation.

### D3 — Train on lake pixels, not four placeholder stations

`FaiRaster.sample_grid` already downsamples each pass to roughly 1,860 water
pixels and is currently used only to draw the heatmap. Training on those pixels
raises the honest sample count from about 140 to roughly 65,000 across 35 usable
date pairs, using satellite data already downloaded, and removes the dependency
on station coordinates that are admitted placeholders.

### D4 — Validate chronologically, with an embargo

Replace shuffled k-fold with expanding-window chronological splits. Leave a gap
of at least the forecast horizon between the end of training and the start of
validation, because the current train/holdout boundary at 2026-06-09 has no gap
and the last training rows' targets fall inside the holdout window. Never
forward-fill for training. Formalised as rules MI-2 and PR-3.

## Consequences

- Reported metrics will fall, and that is the intended outcome. The present
  figures are inflated by leakage and lose to trivial baselines.
- Every model must be reported against persistence and trivial-rule baselines
  under rule MI-1. A model that fails to beat them is reported as failing.
- The four-station framing is retained for presentation, since the dashboard and
  the design handoff are built around it, but is no longer the training unit.
- `data/processed/training_dataset.csv` must not train a shipped model. It is
  retained as evidence of the audited defect.
- Per-pixel counts are not independent-sample counts. Only temporal splitting is
  in scope before the pitch; spatial block cross-validation is deferred and must
  be declared as a limitation wherever metrics appear (ASM-007, ASM-008).
- D3 requires the grid collected across all 56 dates, which requires Copernicus
  credentials. That is the single external dependency, tracked as the P0
  unanswered question.
- Beating persistence will likely require change-drivers the project does not yet
  have — wind, temperature, radiation, runoff. This reframes ERA5-Land from an
  unfinished task into the principal explanation for the persistence failure.

## Fallback

If credentials do not arrive, apply D1, D2 and D4 to the existing station data.
The result will be honest and unimpressive on roughly 140 samples. Present D3 as
the argued remedy with its arithmetic shown, rather than as a built system. This
fallback is acceptable and must be stated plainly rather than taken silently.

## Sources

- SRC-002 — supervisor: improve training, understand the numbers
- SRC-009 — audit session of 2026-09-09
- SRC-006, SRC-007, SRC-011 — the CSVs from which every figure above is reproducible
- `src/features/fai.py` — `sample_grid` and `at_latlon`
- `src/features/build_dataset.py` — forward-fill and threshold calibration
- `src/model/train.py` — shuffled cross-validation and the holdout boundary
- Reproduction commands: `agents/validation/EVIDENCE_INDEX.md`

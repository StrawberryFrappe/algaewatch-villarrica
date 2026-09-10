# ADR-sf-0008: Lake-mean FAI is the interim training signal, and the trivial rule becomes climatology

## Status

Accepted 2026-09-10. Design accepted; **implementation blocked** on BL-029 to
BL-031.

## Context

ADR 0004 laid out four modelling changes and a fallback. The fallback reads: "If
credentials do not arrive, apply D1, D2 and D4 to the existing station data."
ADR-sf-0007, accepted one day later, then disqualified station-point FAI as a
training signal altogether — two of the four coordinates are off the lake and
their readings are shoreline vegetation.

So the fallback names a data source the next ADR forbids, and D3 — per-pixel
sampling — needs a grid backfill blocked on BL-028. WI-005 ("honest retrain on
station data") inherits the contradiction. A contributor reading the three
documents in order cannot tell what WI-005 is supposed to train on.

There is a third source, and it was in the repository the whole time.
`data/processed/fai_series_raw.csv` carries a `lake_mean_fai` column alongside
the four station columns. It comes from `FaiRaster.lake_mean` in
`src/features/fai.py`, which is `nanmean(fai[is_water])` over the SCL water mask
— the whole lake, no station coordinate anywhere in its derivation. ADR-sf-0007
bars `fai_<station_id>` columns; it does not touch this one, and the reason it
gives for barring them does not apply.

Its arithmetic, measured rather than assumed (EV-019, EV-020):

| Fact | Value |
|---|---|
| Real pass dates | 56, 2025-09-04 to 2026-08-22 |
| Honest pairs, 5 to 9 days apart, nearest to 7 | 35 |
| Actual horizons in those pairs | 5d ×10, 6d ×1, 7d ×11, 8d ×13 |
| Persistence MAE | 0.001333 |
| Causal expanding-mean climatology MAE | **0.000945** |
| `lake_mean_fai` range | −0.008248 to +0.001999 |
| Recorded bloom threshold | 0.025916 |

Two of those rows changed the design.

**Climatology beats persistence.** On the station table the trivial rule was the
leak — it beat the model because the label encoded place. On the lake-wide series
the trivial rule is the *harder* bar: the signal is noise around a stable mean, so
predicting the mean beats predicting today by a third. A model that clears
persistence has cleared nothing.

**The recorded threshold is unusable here.** 0.025916 sits an order of magnitude
above the lake-wide maximum of 0.001999, because it was calibrated by
`calibrate_bloom_threshold` on the contaminated station series — the very
contamination ADR-sf-0007 documents. Applied to lake-wide data it labels every
row negative.

## Decision

### D1 — `lake_mean_fai` is the interim training signal

Admissible because it is derived from the water mask and not from any station
coordinate. It replaces the station columns for the duration of BL-027, and is
superseded by per-pixel sampling (ADR 0004 D3) when BL-007 lands.

35 rows is not a training set. What this buys is an honest measurement of whether
anything beats the baselines on real data, and a pipeline the per-pixel table can
be poured into unchanged. Both are worth having; a model worth shipping is not
claimed. This is ADR 0004's fallback, redirected to the one source that survives
ADR-sf-0007, and it must be stated as such rather than presented as D3 arriving
early.

The pairing and anomaly-baseline code is parameterised on a spatial-unit column
from the start, so D3 substitutes `pixel_id` for the lake-wide sentinel instead of
requiring a rewrite.

### D2 — The trivial rule becomes climatology where there is one spatial unit

`trivial_rule` predicts from location. One lake-wide series has one location, so
the rule is degenerate — and worse than degenerate as currently written: it
reduces to "always predict positive", which is not the baseline it documents.
See BL-030.

Where the table carries fewer than two spatial groups, the trivial-rule baseline
is **predict the training-window mean**, using no satellite measurement, which is
what rule MI-1 actually asks of a trivial rule. The location form is retained for
tables that have groups, because it is what reproduces EV-002.

Consequence, and it is the point: any lake-wide model must beat 0.000945.
`check_beats_persistence` on its own is now too weak a bar and must be read
beside `check_beats_trivial_rule`, not instead of it.

### D3 — An inapplicable check is omitted, never passed

`check_label_not_stratified_by_station` measures the spread of positive rates
across stations. On one spatial unit that spread is 0.000, which is inside the
0.50 ceiling, so the check **reports a pass** — not because the defect was fixed
but because nothing is left to compare.

Where the table carries fewer than two spatial groups the check declares itself
inapplicable and is omitted from the gate's verdict. This follows the precedent
already in `src/model/integrity.py`: `run_all` omits `check_station_points_on_water`
when coordinates are absent, and `check_no_fabricated_rows` refuses to pass an
empty table for exactly this reason.

The guard belongs **inside the check function**, not only in `run_all` —
`tests/test_model_integrity.py` calls the check directly, so a dispatcher-only
guard leaves the vacuous pass reachable. That is BL-031.

### D4 — The classification surface is null until the threshold is recalibrated

Under PR-3 a figure that cannot be computed is reported as `null`, never
fabricated. The `ValidationMetrics` model in `backend/app/schemas.py` already types all five
metrics as `float | None` in anticipation.

Until a threshold is calibrated on the lake-wide distribution, `bloom_7d` is
constant and precision, recall, F1 and AUC are not computable from it. They are
reported as `null` with the reason recorded. `mae_fai` is the headline figure, and
it is reported with its cross-validation spread rather than as a single number
from a seven-row fold, where one flipped prediction moves the estimate more than
any modelling choice would.

## Consequences

**Improves.** WI-005 has a data source that does not contradict ADR-sf-0007, and
the contradiction between ADR 0004's fallback and ADR-sf-0007 is now written down
instead of left for the next reader to discover. The trivial-rule baseline becomes
the binding constraint, which is the honest reading of EV-019. And the design
review found three defects in already-committed code (BL-029 to BL-031) that
would otherwise have been discovered *after* a green gate was reported over a
still-leaking split.

**Gets harder.** 35 rows against 4 to 6 features means the smallest fold trains
on 8 rows. Coefficient stability across folds is a reportable limitation, not a
detail. 18 of the 35 dates serve as both a target and a feature anchor, so the
rows are not independent and the splits cannot pretend otherwise (BL-033).

**Does not fix.** The dashboard's four station cards. A lake-wide model produces
one number for the lake, and ADR-sf-0007 already names this as a visible product
gap that PR-3 requires be shown as absent rather than filled in. Nothing here
changes that, and WI-005 does not rewire the serving path: `backend/app/data_source.py`
imports `build_daily_series` from `src/features/build_dataset.py`, which imports
`sentinelhub` at module scope, so the backend cannot even start on a machine
without BL-028 resolved.

**Must be revisited** when BL-007 delivers the per-pixel grid. At that point the
spatial-unit column becomes `pixel_id`, D2 and D3 both switch back to their group
forms because pixels are real spatial groups, and spatial block cross-validation
stops being deferred (ADR 0004, ASM-008).

## Sources

- ADR 0004 — the redesign whose fallback this redirects
- ADR-sf-0007 — the disqualification that made the fallback unusable as written
- EV-019, EV-020 — the measurements above, with a reproduction command
- BL-029, BL-030, BL-031 — the defects that block implementing this
- BL-033 — the overlapping-pair limitation
- `src/features/fai.py` — `FaiRaster.lake_mean`, the signal's derivation
- `src/model/baselines.py`, `src/model/integrity.py` — the code the decisions change
- `backend/app/schemas.py` — the `float | None` contract D4 relies on

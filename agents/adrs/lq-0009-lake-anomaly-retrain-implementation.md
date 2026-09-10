# ADR-lq-0009: Implementation of the lake-mean anomaly retrain (WI-005)

## Status

Accepted 2026-09-10. Records the execution decisions ADR-sf-0008 left open;
does not revisit the design, which ADR-sf-0008 settled and the user approved.

Minted by `lq`, who implemented WI-005 this session standing in for `sf` on the
model half. The slug records who minted the ID, not who owns the subject
(WORKFLOW.md).

## Context

ADR-sf-0008 fixed the signal (`lake_mean_fai`), the baseline redefinition
(climatology where there is one spatial unit) and the null classification
surface. It left the execution details to the implementer, and its own design
review found four defects in already-committed gate code (BL-029 to BL-032) that
had to be fixed first. Those are done (branch `fix/sf-model-gate-correctness`,
tests green, both false passes demonstrated fixed).

This ADR records what was decided while building `src/features/lake_anomaly.py`,
`src/model/lake_anomaly.py` and `scripts/train_lake_anomaly.py`.

## Decision

### D1 — Two-step table build, pairing kept separable from the baseline

`build_pairs` does pure anchor→target pairing and reproduces EV-019 exactly (35
pairs, `persistence_mae` 0.001333). `add_causal_baseline` attaches the local
baseline and drops rows. `build_anomaly_pairs` composes them. Keeping pairing on
its own means the EV-019 provenance stays checkable without the baseline
filter's choices in the way.

### D2 — Target is the standardised causal anomaly; `mae_fai` is back-transformed

The model predicts `anomaly_future = (fai_future - baseline_mean) / baseline_std`
(ADR 0004 D2). For reporting, the prediction is mapped back with
`fai = baseline_mean + z * baseline_std`, so `mae_fai` is in raw FAI units and
comparable to the recorded persistence and climatology figures. `z = 0` is
exactly climatology, which is why the model is reported against **both**
baselines (ADR-sf-0008 D2).

### D3 — `min_prior = 5`

Minimum causal observations before an anchor for its baseline `std` to mean
something. On the 56-date series the pair count is **flat at 34 for any value
from 0 to 7** — the only dropped anchor is 2025-09-06, which has one prior pass
and falls below the `max(min_prior, 2)` floor regardless — and `baseline_std`
barely moves across that range (5.7e-4 to 2.0e-3, and the first twelve anchors
are all ~6e-4). The choice is insensitive; 5 sits clear of the sample-std floor
of 2, with every kept pair backed by at least 7 real prior passes. Reproduction:
run the curve in `EVIDENCE_INDEX.md` EV-021.

### D4 — Ridge, 2 features, expanding-window CV

`Pipeline([StandardScaler, Ridge(alpha=1.0)])` on `["anomaly_now",
"horizon_days"]`. Cross-validation is four expanding chronological windows with a
per-row target-date embargo (the BL-029 rule): the last four equal blocks are
validation, one per fold; a training row is dropped if `date + horizon_days`
reaches the validation block. Smallest fold trains on 9 rows.

Alpha and feature sweep (0.1 to 100; `anomaly_now` alone; adding `fai_now`) was
run: **every combination loses to both baselines.** Heavier shrinkage moves
`mae_fai` from 0.0039 toward 0.0033 but never near climatology's 0.0008, because
the folds are tiny and one anchor sits ~15 baseline sigma out. Defaults kept;
the honest result is reported, not tuned around (rule MI-1, ADR 0004: "Reported
metrics will fall, and that is the intended outcome").

### D5 — Artifacts in `src/model/artifacts/lake_anomaly/`, backend untouched

`metrics.json` + `ridge.joblib` in a new subdirectory. `src/model/artifacts/`
itself is byte-unchanged: the backend loads it at import and serves per-station,
and a lake-wide model cannot fill four station cards (ADR-sf-0008). The dataset
is committed at `data/processed/lake_anomaly_dataset.csv` — derived from
committed data, no credentials, and the gate needs it.

### D6 — The gate re-points via two env vars, and dataset-dependent xfails are conditioned

`tests/conftest.py` gained `ALGAEWATCH_METRICS` beside the existing
`ALGAEWATCH_DATASET`, and `embargoed_split` now passes `horizon_col` when the
table carries one. Two dataset-dependent GATE-MODEL xfail marks
(`test_pr3_no_fabricated_rows`, `test_label_is_not_a_proxy_for_location`) are
conditioned on `not ON_CANDIDATE`; `test_mi2_training_split_is_chronological_with_embargo`
is `skipif(ON_CANDIDATE)` because its `pipeline_split` fixture mirrors
`train.py`'s four-station no-embargo slice, a path WI-005 never uses (its real
CV embargo is covered by `TestExpandingWindowFolds` in `tests/test_lake_anomaly_model.py`);
`test_forecast_is_not_a_re_reading_of_the_present` is kept unconditional by owner
decision. So

```
ALGAEWATCH_DATASET=data/processed/lake_anomaly_dataset.csv \
ALGAEWATCH_METRICS=src/model/artifacts/lake_anomaly/metrics.json \
python -m pytest tests/test_model_integrity.py
```

gives a real pass/fail verdict on the retrain instead of XPASS noise. Result:
**11 passed, 1 skipped, 4 xfailed.** The retrain passes `no_fabricated_rows`
(PR-3) and `label_not_a_proxy` (inapplicable, one spatial unit — omitted per
BL-031); it still xfails MI-1 against persistence (0.0039 vs 0.0014), the
trivial-rule check (f1 null), the constant-label present-reading check, and
station provenance (BL-027).

**Why the present-reading check fails rather than declaring itself inapplicable,
unlike the stratification check (D3).** Both are vacuous on the lake table —
one spatial unit, one constant label. D3 makes `check_label_not_stratified_by_station`
declare `applicable=False` because a one-unit table is a legitimate shape the
per-pixel future will *not* have, and omitting it is the honest reading. The
constant `bloom_7d` is different: it is a symptom of an *uncalibrated threshold*
(EV-020), a defect to be fixed, not a shape to be accommodated. Failing closed
on it keeps the pressure to recalibrate visible in the gate rather than silently
omitted. Owner decision, 2026-09-10.

### D7 — Independent review, and the realised-boundary fix

The BL-029..032 + WI-005 diff was reviewed by a subagent (`general-purpose`),
verdict **APPROVE WITH FIXES**, no Critical findings, both false passes
confirmed closed and unreachable, the legacy four-station path confirmed
untouched. Review recorded at
`agents/reviews/20260910/implementation-review.lq.md`.

One Important finding, fixed in the same branch: `check_chronological_split`
false-*failed* a correctly per-row-embargoed **dense variable-horizon** split —
`gap_days` is measured on feature dates and tracks the *minimum* kept horizon,
so `gap >= max_horizon_days` rejected a clean split (the per-pixel table shape
ADR 0004 D3 requires this code to accept unchanged). `Split` now records
`max_kept_target_date` — the realised boundary the embargo enforced — and the
check asserts that is strictly before the first holdout date when a per-row
embargo was applied, falling back to the scalar gap otherwise.
`chronological_split`'s horizon branch also moved to strict `<` so a training
target landing exactly on the first holdout date is dropped, matching the CV
path in `lake_anomaly.py`. Regression test:
`test_check_passes_a_correctly_embargoed_dense_variable_horizon_split`.

Minor review findings also applied: `check_no_fabricated_rows` now reports
`lag_signature_checked` and says so in its detail when the lag column is
absent; two artifact-consistency tests (`TestCommittedArtifact`) assert the
committed `ridge.joblib` and `metrics.json` match a fresh `fit_and_evaluate`.

## Consequences

**Improves.** WI-005 is built, PR-3 is satisfied on a real table, and the gate
is genuinely re-pointable — `conftest` no longer hard-codes the four-station
artifact. The pairing/anomaly code is parameterised on `unit_col`, so ADR 0004
D3 substitutes `pixel_id` without a rewrite.

**Gets harder / does not fix.** The retrain loses to both baselines; that is
reported, not hidden. The dashboard's four station cards are unchanged — a
lake-wide model produces one number. The overlapping-pair non-independence
(BL-033) stands: 18 of the 35 dates are both an anchor and a target. One anchor
is a ~15-sigma outlier against its causal baseline — a real heavy tail in the
series.

**Must be revisited** when BL-007 delivers the per-pixel grid: `unit_col`
becomes `pixel_id`, the trivial rule and the stratification check switch back to
their group forms, and spatial block cross-validation stops being deferred
(ADR 0004, ASM-008).

## Sources

- ADR-sf-0008 — the design this implements
- BL-029 to BL-032 — the gate defects fixed first (branch `fix/sf-model-gate-correctness`)
- EV-019, EV-020 — the lake-wide signal measurements
- EV-021 — the `min_prior` curve and the retrain's headline numbers
- `src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`, `scripts/train_lake_anomaly.py`
- `agents/local/logbook/20260910/sf-gate-correctness.md` — session notes

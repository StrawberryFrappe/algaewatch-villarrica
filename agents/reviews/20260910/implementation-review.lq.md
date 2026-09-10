# Implementation Review — BL-029..032 + WI-005 (`lq`)

**Date:** 2026-09-10
**Range:** `9dd939b..e29609a` on `fix/sf-model-gate-correctness`
**Reviewer:** independent subagent (`general-purpose`), read-only checkout
**Verdict:** APPROVE WITH FIXES — no Critical findings

## Scope

The four gate-correctness fixes (BL-029 to BL-032) and WI-005, the interim
lake-mean anomaly retrain. Requirements: `AGENTS.md` PR-1/PR-3, rules
MI-1/MI-2, ADR 0004, ADR-sf-0008, ADR-lq-0009, `TEST_STRATEGY.md`.

## What the review verified

- Ran the full suite (67 passed, 7 xfailed, **0 XPASS**), the candidate gate
  (`10 passed, 5 xfailed` at review time), `harness_doctor --strict` (0/0), and
  `scripts/train_lake_anomaly.py` — reproduced the dataset, `metrics.json` and
  `ridge.joblib` **byte-identical**.
- **Both false passes are genuinely closed and unreachable** by any traced path:
  `check_chronological_split` (`gap is None` → fail; `max_horizon_days=None` →
  legacy fallback), the single-group guard inside
  `check_label_not_stratified_by_station` (robust to `group_col` absent, empty
  df, all-NaN ids).
- **The legacy four-station path is untouched**: `chronological_split` with no
  `horizon_col`, `trivial_rule` with ≥2 groups (guard inserted before
  `idxmax`), `run_all` on the four-station table; the 7 original strict xfails
  stay xfail, no XPASS.
- `build_pairs` reproduces EV-019 exactly; the `date < anchor` baseline is
  strict, no off-by-one.
- `fit_and_evaluate` is honest: `mae_fai`, persistence and climatology over the
  same val rows in raw units; `beats_baselines` `{False, False}` reported;
  `predict_fai` cannot divide by zero (guarded upstream); classification `null`
  with a reason.
- `min_prior=5` justified — pair count flat 0..7, drops at 8.
- PR-1 / BL-028 hold — verified via `sys.modules` that importing either module
  pulls in no `sentinelhub` / `rasterio`.

## Findings and disposition

| # | Severity | Finding | Disposition |
|---|---|---|---|
| 1 | Important | `check_chronological_split` false-*fails* a correctly per-row-embargoed dense variable-horizon split: `gap_days` tracks the minimum kept horizon, so `gap >= max_horizon_days` rejects a clean split. Safe direction (never a false pass) but blocks the per-pixel table (ADR 0004 D3). | **Fixed.** `Split.max_kept_target_date` records the realised boundary; the check asserts it is `<` the first holdout date under a per-row embargo. Regression test `test_check_passes_a_correctly_embargoed_dense_variable_horizon_split`. See ADR-lq-0009 D7. |
| 2 | Minor | Embargo boundary inconsistent: `baselines.py` kept `target <= first_holdout`, `lake_anomaly.py` used strict `<`. | **Fixed.** `chronological_split` horizon branch → strict `<`, matching the CV path. |
| 3 | Minor | `check_no_fabricated_rows` half-runs silently on a table with no `fai_lag_1d`. | **Fixed.** `measured["lag_signature_checked"]` and the detail string now say when the lag half is not applicable. |
| 4 | Minor | D4's present-reading check fails vacuously on the constant label rather than declaring inapplicability, asymmetric with D3. | **Documented.** ADR-lq-0009 D6 now explains why: a constant `bloom_7d` is an uncalibrated-threshold *defect*, not a table shape to accommodate — failing closed keeps the recalibration pressure visible. |
| 5 | Minor | The candidate-run MI-2 xfail uses `pipeline_split`, a path WI-005 never uses. | **Fixed.** `skipif(ON_CANDIDATE)` with a reason pointing at `TestExpandingWindowFolds`. |
| 6 | Minor | Doc drift (fold size 8 vs 9, xfail count, "zero-history" anchor wording). | **Fixed** in ADR-lq-0009 D3/D6. |
| 7 | Minor | `ON_CANDIDATE` constant interleaved with imports. | **Fixed.** Moved below the import block. |
| — | Recommendation | Add a test pinning `ridge.joblib` to a fresh fit. | **Added** — the `TestCommittedArtifact` cases in `tests/test_lake_anomaly_model.py` (predictions and metrics). |

## State after fixes

- `python -m pytest -q` → **70 passed, 7 xfailed**
- candidate gate → **11 passed, 1 skipped, 4 xfailed**
- `harness_doctor.py --strict` → 0 blockers, 0 warnings
- `check_translations.py` → 5 of 5 current

## Deviations flagged by the reviewer, confirmed intentional

- Two dataset-dependent xfails **conditioned** (not removed) on `ON_CANDIDATE`,
  because the default station table still genuinely fails those checks — WI-005
  does not change the default training table. No XPASS on the default suite, so
  `TEST_STRATEGY.md`'s "no green through a fix" holds. Designed in ADR-lq-0009 D6.
- `test_forecast_is_not_a_re_reading_of_the_present` left unconditional (owner
  decision, constant-label vacuity — ADR-sf-0008 D4).

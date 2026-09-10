# Handoff: WI-005 shipped, and the brief for the retrain that beats the baselines

Written 2026-09-10 by `lq`, standing in for `sf` on the model half this session.
Supersedes the **modelling** content of `agents/execution/SESSION_HANDOFF.sf.md`
(which is stale — it names `develop`, retired 2026-09-10, and a Windows
checkout). Read `AGENTS.md` and `agents/RUN_STATE.md` first; this assumes them.

This is not a session recap for its own sake. Its job is the **next modelling
push**: retrain so the model beats *both* baselines on real lake data, honestly.
Everything you need for that is below.

---

## Part 1 — Where things stand (done this session, on `main`)

Branch `fix/sf-model-gate-correctness` (`9dd939b → e29609a → 23cbc30`), reviewed
(APPROVE WITH FIXES, `agents/reviews/20260910/implementation-review.lq.md`),
merged to `main`.

### BL-029 to BL-032 — the GATE-MODEL was reporting false passes; fixed

- **BL-029** `chronological_split` (`src/model/baselines.py`) gained `horizon_col`.
  With it, the embargo clears each row's **target** date (`date + horizon`), not
  its feature date. `Split` carries `max_horizon_days` and `max_kept_target_date`
  (the realised boundary — added after review, because `gap_days` tracks the
  *minimum* kept horizon on a dense table). `check_chronological_split` asserts
  the realised boundary is strictly before the first holdout date. The legacy
  fixed-horizon path (no `horizon_col`) is byte-unchanged.
- **BL-030** `trivial_rule` dispatches on cardinality: `< 2` spatial groups →
  climatology (predict the training-window mean label); `>= 2` groups → the
  location rule, untouched (reproduces EV-002).
- **BL-031** `CheckResult` gained `applicable`. `check_label_not_stratified_by_station`
  returns `applicable=False` on `< 2` groups from **inside** the function;
  `run_all` filters inapplicable results.
- **BL-032** the plumbing tests assert a check-name set + omission reasons, not a
  magic count. Dataset-dependent GATE-MODEL xfails are conditioned on
  `ON_CANDIDATE` (env `ALGAEWATCH_DATASET` set), so pointing the gate at a
  candidate table gives a real verdict, not XPASS noise.

### WI-005 — the interim lake-mean retrain (ADR-sf-0008, ADR-lq-0009)

New, all consuming a built table only (PR-1 intact), pure pandas/numpy/sklearn,
no `sentinelhub`, no CUDA:

- `src/features/lake_anomaly.py` — `build_pairs` (anchor→target pairing,
  reproduces EV-019: 35 pairs) + `add_causal_baseline` (mean/std from passes
  strictly before the anchor; drop anchors with `< max(min_prior, 2)` priors;
  `min_prior=5`) + `build_anomaly_pairs` (compose). **Parameterised on
  `unit_col`** — this is the seam for per-pixel (below).
- `src/model/lake_anomaly.py` — `predict_fai` (z → raw: `baseline_mean + z·baseline_std`),
  `expanding_window_folds` (chronological, per-row target-date embargo),
  `fit_and_evaluate` (Ridge on the standardised anomaly; `mae_fai` ± CV spread;
  reported beside **persistence and climatology**; classification `null`).
- `scripts/train_lake_anomaly.py`, `data/processed/lake_anomaly_dataset.csv`
  (committed), `src/model/artifacts/lake_anomaly/` (`metrics.json`, `ridge.joblib`)
  (committed). `src/model/artifacts/` — the backend's — is untouched.

**Result (EV-021), the honest measurement:**

| | MAE (raw FAI) | model beats it? |
|---|---|---|
| Ridge, 4-fold expanding CV | **0.003919 ± 0.002135** | — |
| persistence (predict today) | 0.001362 | **no** (2.9× worse) |
| climatology (predict causal baseline mean) | 0.000775 | **no** (5× worse) |
| precision / recall / F1 / AUC | `null` | `bloom_7d` constant, EV-020 |

This is the intended outcome of ADR 0004's fallback: *"Reported metrics will
fall, and that is the intended outcome."* The interim model exists to **measure**
that nothing beats the baselines on 34 lake-wide rows, and to lay a pipeline the
bigger table pours into unchanged.

---

## Part 2 — The goal for the next push

**Beat persistence (~0.00136) AND climatology (~0.00078) on real lake data, with
a methodology that survives review.** Climatology is the binding bar (ADR-sf-0008
D2): because `z_pred = 0` reproduces climatology exactly, any shrinkage model
clears persistence almost for free — a result that only counts if it also clears
climatology.

A low honest number with correct methodology **passes** GATE-MODEL. A high number
from a leaky pipeline **fails** it (GATES.md). Do not tune toward a number.

### Why the interim model can't get there, and what actually would

The lake-mean series is essentially noise around a slowly declining mean, so
"predict the mean" (climatology) is already near-optimal and `anomaly_now`
carries almost no signal about `anomaly_future`. Two changes, **both required**
(ADR 0004 adopts D1–D4 together; a subset reintroduces the defect the others
fix):

#### Leap A — per-pixel sampling (ADR 0004 **D3**, backlog BL-007 / BL-008)

`data/processed/fai_grid_latest.csv` is **one** pass (1,861 water pixels).
Backfill the same grid across **all 56 clear passes** → ~65,000 (pixel, pass)
samples (EV-008). Then:

- Feed the per-pixel table through the *same* `build_anomaly_pairs`, with
  `unit_col="pixel_id"`, `value_col="fai"`. The pairing and the **causal local
  baseline become per-pixel** — each pixel compared against its own history, which
  is exactly ADR 0004 D2 done properly (the lake-mean version is the degenerate
  one-unit case).
- With `>= 2` spatial groups, `trivial_rule` and `check_label_not_stratified_by_station`
  automatically switch back to their group forms (BL-030/BL-031 handle this).
- **Spatial block cross-validation** becomes mandatory (ADR 0004 ASM-008,
  BL-016): hold out lake *regions*, not random pixels, or neighbouring-pixel
  correlation inflates the score. `expanding_window_folds` gives you the temporal
  axis; add a spatial hold-out on top.
- Model: ADR 0002 mandates **PyTorch** for BL-008 — per-pixel, three quantile
  heads, pinball loss. Not installed on `lq`'s `.venv` (EV-017 measured `sf`'s
  GTX 1650; this machine is an RTX 2050 4 GB, unscanned for torch). Keep the
  `predict_fai` back-transform and the dual-baseline reporting from
  `src/model/lake_anomaly.py`.

#### Leap B — change-drivers (ADR 0004 **D4**, backlog BL-012)

The 2026-09-09 handoff said it plainly: *"beating persistence will probably
require change-drivers the project does not have — wind, temperature, radiation,
runoff."* Blooms are driven by weather; the model currently sees none of it.

- `src/features/era5.py` already fetches ERA5-Land daily temp / precip / wind and
  reduces to a lake-area value per day. It needs: `cdsapi` + `xarray` installed
  (WI-011), `CDS_TOKEN` (present), and **the CDS dataset licence accepted once,
  manually**, per the module docstring — HTTP 403 until then.
- Backfill weather over the 56 pass dates, join to the per-pixel (or lake-mean)
  pairs as features. This is the single most likely thing to move `mae_fai` below
  climatology.

### Prerequisites (all currently blocking, mostly the user's)

| # | What | Status |
|---|---|---|
| WI-011 / BL-028 | `pip install cdsapi rasterio xarray` in the `.venv` (`sentinelhub` 3.11.5 already present) | **user** — not done |
| — | CDSE credentials (Sentinel-2) | working, EV-015 |
| — | CDS ERA5 licence accepted manually in the CDS web UI | unknown — check first |
| BL-007 | Run grid collection across all 56 clear dates. `scripts/collect_fai_grid.py` does only the *latest* pass — adapt it to loop `find_clear_dates` over the full range and stack, writing a new grid-series CSV under `data/processed/` with a `pixel_id` column | not started |
| BL-024 / WI-010 | PyTorch + CUDA on this machine (for BL-008) | torch absent on `lq`'s `.venv` |
| BL-027 | Real station GPS (only relevant if you ever reintroduce station columns — don't, until this lands) | blocked on SNIA |

---

## Part 3 — Reuse, don't rewrite

| Need | Use |
|---|---|
| Build honest pairs + per-unit causal baseline | `build_anomaly_pairs(series, value_col="fai", unit_col="pixel_id")` in `src/features/lake_anomaly.py` — already generalised |
| Chronological split, per-row target-date embargo | `chronological_split(df, horizon_col="horizon_days")` in `src/model/baselines.py` (post-review: asserts the realised boundary) |
| Expanding-window CV | `expanding_window_folds` in `src/model/lake_anomaly.py` — add a spatial block on top for per-pixel |
| z → raw FAI back-transform | `predict_fai` in `src/model/lake_anomaly.py` |
| Metrics shape, dual-baseline verdict, `null` classification | `fit_and_evaluate` in `src/model/lake_anomaly.py` — swap the estimator, keep the reporting |
| Judge the candidate table by the gate | `ALGAEWATCH_DATASET=<table>.csv ALGAEWATCH_METRICS=<metrics>.json python -m pytest -q tests/test_model_integrity.py` — the `ON_CANDIDATE` conditioning already handles a lake-wide *or* multi-group table |
| Baselines (persistence, trivial/climatology) | `src/model/baselines.py` — `compute`, `beats_baselines` |

---

## Part 4 — Hard constraints (violating any of these fails review)

- **PR-1** — `src/features/` never imports `src/model/` and never calls the
  Sentinel-2 / CDS APIs from model code; `src/model/` consumes a built table.
- **PR-3** — no forward-fill. One row per real observation pair. For per-pixel:
  one row per `(pixel_id, anchor pass)` with a real later pass 5–9 days out.
- **MI-1** — every `mae_fai` reported beside persistence *and* climatology on the
  *same* rows/folds. Losing is reported, never hidden or omitted.
- **MI-2** — chronological splits only, embargo ≥ the table's max horizon. For
  per-pixel, **also** spatial block CV (hold out regions).
- **MI-3** — continuous target; thresholds applied at serving time. The recorded
  bloom threshold `0.025916` is ~10× the lake-wide max (EV-020) — **recalibrate
  on the actual distribution**, or report the classification surface as `null`
  with the reason. Never bake a threshold into training labels.
- **ADR-sf-0007** — no `fai_<station_id>` columns as a training signal until real
  GPS arrives (BL-027). `check_station_points_on_water` enforces it.
- Do **not** overwrite `src/model/artifacts/` — the backend loads it at import
  and serves per-station. New model → new artifact dir (as WI-005 did with
  `.../lake_anomaly/`).
- `data/processed/training_dataset.csv` must **never** train a shipped model — it
  is retained as evidence of the audited defect.
- **BL-033** — overlapping pairs: dates that serve as both an anchor and a
  target make residuals non-independent across rows. Declare it wherever metrics
  appear; per-pixel makes it worse, not better.

---

## Part 5 — Definition of done

1. A per-pixel FAI table backfilled across all 56 passes, committed, reproducible
   from a script, **no forward-fill**, with a `pixel_id` column.
2. (If pursued) ERA5 weather joined as features, backfilled over the same dates.
3. A model reported with `mae_fai` ± CV spread beside persistence *and*
   climatology, on chronological **and** spatial-block splits, with real sample
   counts stated (pixels are not independent samples — say so).
4. Verdict stated plainly:
   - beats climatology → the win, with the split design and counts shown;
   - does not → reported honestly (ADR 0004's fallback is acceptable *stated*,
     not taken silently). A correct low number passes GATE-MODEL.
5. Classification surface: recalibrated threshold, or `null` + reason.
6. `python -m pytest -q` green; the candidate-gate command green;
   `python agents/harness_doctor.py --root . --strict` 0/0;
   `python agents/check_translations.py` current.
7. Independent implementation review (subagent) **before** merge — the WI-004 /
   WI-005 precedent (`agents/reviews/reviews_index.md`).
8. A new ADR (`sf-00NN` or the acting contributor's slug) recording the
   modelling choices, with reproduction commands added to `EVIDENCE_INDEX.md`.
9. `RUN_STATE.md` + `RUN_STATE.es.md` updated (RUN_STATE is an entry doc — keep
   the Spanish sibling current and re-record its `source_sha`).

---

## Part 6 — Traps this project has already hit (don't repeat them)

From the 2026-09-09 audit and three "a claim outran reality" incidents
(`agents/validation/DOCTOR.md`):

- Shuffled k-fold over time-ordered / duplicated rows (EV-013 — CV AUC 0.99 vs
  temporal 0.90 is the leakage signature).
- Forward-filling a sparse series onto a daily grid, then training on it (EV-004).
- A pooled absolute threshold as the label — it encodes location (EV-001).
- Station-point FAI as signal — two of four points are off the water (EV-014).
- Reporting a metric without its baselines (rule MI-1).
- Claiming "done" before running the verification command
  (`superpowers:verification-before-completion`).
- `RUN_STATE.md` asserting a state that isn't true — every quoted figure needs a
  reproduction command in `EVIDENCE_INDEX.md`.

---

## Pointers

- Design: `agents/adrs/0004-per-pixel-anomaly-redesign.md` (D1–D4),
  `agents/adrs/sf-0007-station-points-are-not-a-training-signal.md`,
  `agents/adrs/sf-0008-lake-mean-as-interim-training-signal.md`,
  `agents/adrs/lq-0009-lake-anomaly-retrain-implementation.md`.
- Evidence: `agents/validation/EVIDENCE_INDEX.md` EV-007, EV-008 (sample-size
  arithmetic), EV-019, EV-020, EV-021.
- Roadmap: `agents/planning/ROADMAP.md` M3; backlog BL-007, BL-008, BL-012,
  BL-014, BL-016.
- Gates: `agents/validation/GATES.md` (GATE-MODEL, GATE-TEST),
  `agents/validation/TEST_STRATEGY.md`.
- Collection: `scripts/collect_fai_grid.py`, `scripts/collect_fai.py`,
  `src/features/fai.py` (`FaiRaster.sample_grid`, `lake_mean`),
  `src/features/era5.py`, `src/features/config.py` (`LAKE_BBOX`, tokens).
- This session's local notes: `agents/local/logbook/20260910/sf-gate-correctness.md`.

# Project Brief

## Project Name

AlgaeWatch Villarrica

## Product / System Intent

A monitoring and short-horizon prediction platform for cyanobacteria blooms on
Lago Villarrica, Región de La Araucanía, Chile.

The system derives the Floating Algae Index (FAI) from free Sentinel-2 L2A
satellite imagery, serves current lake conditions through a FastAPI backend, and
presents them in a React dashboard with four views (Mapa, Estaciones,
Tendencias, Modelo). A predictive model projects bloom risk seven days ahead.

The workshop brief was to predict algae appearance on a specific lake using
freely available satellite data and any other obtainable sources.

## Users / Audiences

| Audience | Role | Horizon |
|---|---|---|
| Workshop supervisor and evaluators | Assess the work at the pitch | Immediate |
| Repository owner (portfolio) | Demonstrate applied remote sensing plus ML | Ongoing |
| Lake authorities / SNIA | Notional end user of bloom warnings | Aspirational, not engaged |

The system is not in the hands of any operational user and makes no field-validated claims.

## Success Criteria

1. The predictive claim is honest and survives scrutiny: every reported metric is
   reproducible and compared against trivial baselines.
2. Training uses chronological validation with no fabricated rows.
3. The pitch can state plainly what works, what does not, and why.
4. The visible product is credible enough to show without embarrassment
   (GATE-PQ is active).

Success is not a high accuracy number. A low honest number with a correct
methodology passes; a high number produced by leakage fails.

## Non-Goals

- Production deployment or hosting.
- Real in-situ sensor integration (SNIA CSVs never arrived; `insitu.py` stays a stub).
- Field validation of predictions.
- Operational alerting to any public authority.
- Rewriting the satellite ingestion layer, which was audited and found correct.

## Current Project State

- Type: data/ML project with a web frontend and REST backend.
- Existing code: 2,479 lines of Python, JavaScript and JSX across `src/`,
  `backend/`, `scripts/` and `frontend/src` (1,503 of that Python), plus 445
  lines of CSS. Single commit `4b37bea` authored by the teammate.
- Existing docs/specs: root `README.md`, `backend/README.md`, `frontend/README.md`,
  and `design_handoff_algaewatch_villarrica/README.md` (frontend spec).
- Existing tests: none. No CI, no test runner, no `pytest` configuration.
- Existing deployment: none.

## Audit Findings Carried Into This Harness

An audit on 2026-09-09 established the following, all reproducible from the
committed CSVs:

1. **The label encodes location, not blooms.** With a single pooled absolute
   threshold (0.0259), bloom rates per station are: sur 0.98, pucon 0.50,
   norte 0.00, tolten 0.00. A rule reading only the station name scores
   precision 0.97 / recall 0.74 / F1 0.84, beating the trained classifier's
   0.84 / 0.47 / 0.60 on every metric.
2. **Training rows were fabricated.** 218 real satellite readings (56 pass
   dates across 4 stations, less 6 cells where no water pixel was found) were
   forward-filled into 1,356 daily rows; only 363 unique
   (station, fai_now, fai_future) combinations exist, and 85% of rows have
   `fai_now` identical to `fai_lag_1d`.
3. **Cross-validation leaked.** `StratifiedKFold(shuffle=True)` over those
   duplicated rows put copies of the same observation in both train and
   validation folds. CV AUC 0.99 versus temporal holdout AUC 0.90 (EV-013) is the
   signature.
4. **The temporal holdout also leaks at the seam.** Train and holdout share the
   boundary date 2026-06-09 with no embargo, so the last training rows'
   seven-day targets fall inside the holdout window.
5. **The regressor loses to persistence.** Predicting "same as today" gives
   MAE 0.00603; the trained regressor gives 0.00865, 43% worse.
6. **The classifier is re-reading the present.** Thresholding `fai_now`
   directly reproduces the `bloom_7d` label on 90% of rows.

The satellite pipeline itself was checked and is sound: the FAI formula matches
Hu (2009), water masking via the Sentinel-2 SCL band is correct, and rasters are
co-registered across dates by a fixed bbox and resolution.

## Quality Bar

`GATE-PQ Portfolio Quality` is **active** — the repository owner intends to use
this work as a portfolio piece.

What would be embarrassing to show:

- Metrics inflated by leakage, presented as real performance.
- A dashboard whose generated-looking visual style undercuts the science.
- The risk scale: a 4-stop qualitative palette (blue, green, orange, red) that
  is not perceptually uniform, and whose green/orange/red stops are exactly the
  confusable set for the commonest colour vision deficiencies, on what is
  nominally a public-health signal.
- Heatmap risk painted over land because the overlay is not clipped to the lake.

## Open Questions

See `agents/intake/QUESTIONS_SUMMARY.md`.

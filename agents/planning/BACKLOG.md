# Backlog

| ID | Priority | Area | Owner | Work Item | Done Evidence |
|---|---|---|---|---|---|
| BL-001 | P0 | Harness | `sf` | Complete harness mounting | Harness review accepted |
| BL-002 | P0 | Validation | `sf` | Make the persistence and trivial-rule baselines permanent, re-runnable checks | Test output recorded in `EVIDENCE_INDEX.md` |
| BL-003 | P0 | Model | `sf` | Replace the binarised target with a continuous one; move thresholding to serving time (D1) | Retrain output showing a continuous target and a serving-side threshold |
| BL-004 | P0 | Model | `sf` | Express the target as a standardised anomaly against a local baseline (D2) | Per-location bloom rates no longer stratify by station |
| BL-005 | P0 | Model | `sf` | Remove forward-filled rows from every training path; pair only real observations (D4) | Row count equals real pairs; no duplicated lag values |
| BL-006 | P0 | Model | `sf` | Replace shuffled k-fold with expanding-window chronological splits, with a horizon-length embargo (D4) | Split boundaries recorded; no shared boundary date |
| BL-007 | P1 | Data | `sf` | Backfill the FAI grid across all 56 pass dates (D3 prerequisite) | Grid CSV covering every collected date |
| BL-008 | P1 | Model | `sf` | Train per-pixel with PyTorch, three quantile heads, pinball loss (D3, ADR 0002) | Metrics beside baselines; stated sample counts |
| BL-009 | P1 | Frontend | `lq` | Replace the 4-stop qualitative risk palette (`frontend/src/utils/risk.js`) with a perceptually uniform, colourblind-safe sequential scale | Screenshot plus a colourblind simulation check |
| BL-010 | P1 | Frontend | `lq` | Clip the risk overlay to the lake surface so risk is not painted over land | Screenshot showing the overlay bounded by the shoreline |
| BL-011 | P1 | Docs | unassigned | Correct the root README status claims that overstate what runs on real data (CONF-001) | Updated README consistent with `PROJECT_BRIEF.md` |
| BL-012 | P2 | Data | `sf` | Backfill ERA5-Land weather over the collected pass dates, as the only available source of change-drivers | Weather columns populated and non-null |
| BL-013 | P2 | Frontend | `lq` | Extend staleness disclosure beyond the header. `Header.jsx` already flags a stale last pass via `overlay.updated_at`, but the date slider, map overlay and station cards still present forward-filled values with no indication of pass age | Screenshot showing pass age at station and map level |
| BL-014 | P2 | Data | `sf` | Extend the Sentinel-2 history beyond one year; consider 60 m resolution to reduce quota cost | Extended series CSV with recorded date span |
| BL-015 | P3 | Data | `sf` | Evaluate Sentinel-3 OLCI as a daily-revisit, chlorophyll-oriented complement to Sentinel-2 | Feasibility note with quota and resolution findings |
| BL-016 | P3 | Model | `sf` | Spatial block cross-validation, holding out lake regions rather than random pixels (ASM-008) | Region-held-out validation results |
| BL-017 | P3 | Model | `sf` | Convolutional recurrent model over the raster sequence, once timestep depth allows (ADR 0002) | Blocked pending BL-014 or BL-015 |
| BL-020 | P1 | Harness | `sf` | **Done 2026-09-09.** Upgraded `a5f428d` → `5dee2cf` by diff-merge; local half mounted, i18n mounted, tooling vendored into `agents/` | Doctor passes; commit recorded in `RUN_STATE.md`; review at `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| BL-021 | P2 | Frontend | `lq` | Reduce the generated-default visual excess: the two blurred colour halos in `app.css`, and the blanket `backdrop-filter: blur(18px) saturate(140%)` on every panel. Full restyle if time allows; removing the decorative excess is the floor | Screenshots before and after |
| BL-019 | P1 | Frontend | `lq` | Render the mandated "TRL 2 · resultados no validados en campo" seal in the Modelo view. It is currently an unreachable default in `backend/app/routers/model_metrics.py`, shadowed by the populated `caveats` key in `metrics.json`. The seal and the smoke-test caveats are different texts and both belong | Screenshot of the Modelo view showing the seal |
| BL-018 | P3 | Hygiene | unassigned | Remove `xgboost` from `requirements.txt` unless a use appears (ASM-011) | Updated requirements file |
| BL-022 | P1 | Harness | `sf` | Deliver the handoff and confirm `lq` can work: local half built, `agents/harness_doctor.py` and `agents/check_translations.py` both passing on his machine | His confirmation, plus a doctor run he performed |
| BL-023 | P2 | Harness | either | Keep the five Spanish translations current. Translate on touch, or leave stale deliberately and say so. `python agents/check_translations.py` is the check | A passing checker run in the same change as any canonical edit |
| BL-024 | P2 | Model | user | Install PyTorch, or record that BL-008 cannot proceed. Binding from the supervisor (SRC-003, ADR 0002); not installed on the owner's machine as of the 2026-09-09 scan | `python -c "import torch"` succeeds where BL-008 will run |
| BL-025 | P3 | Kernel | `sf` | Carry three findings back to `agent-harness-kernel`: (1) the doctor belongs inside the mounted harness rather than in the kernel, since a harness that hops repositories cannot check itself without it; (2) the mounting guide should **ask** whether to keep a kernel backup rather than leaving it unstated; (3) the `--kernel` adaptation check compares raw bytes, so it is silently defeated whenever the harness and the kernel clone differ in line endings — it should normalise before comparing, or the kernel should pin its own `.gitattributes`. See `agents/validation/DOCTOR.md` | Kernel commits, or an issue recorded against the kernel repository |

## Rules

- Backlog items should be tied to source, ADRs, user decisions, or explicit
  project goals.
- Do not pad the backlog with work that has no product, quality, evidence, or
  operational value.
- If a work item changes visible behavior, define how it will be verified.
- Owner uses author slugs (ADR-sf-0005). `unassigned` is a real state; do not
  assign an item to make the table look complete.
- Append new rows at the end, so concurrent additions by two contributors
  conflict visibly rather than interleaving silently.

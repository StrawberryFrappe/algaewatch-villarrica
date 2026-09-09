# Backlog

| ID | Priority | Area | Work Item | Done Evidence |
|---|---|---|---|---|
| BL-001 | P0 | Harness | Complete harness mounting | Harness review accepted |
| BL-002 | P0 | Validation | Make the persistence and trivial-rule baselines permanent, re-runnable checks | Test output recorded in `EVIDENCE_INDEX.md` |
| BL-003 | P0 | Model | Replace the binarised target with a continuous one; move thresholding to serving time (D1) | Retrain output showing a continuous target and a serving-side threshold |
| BL-004 | P0 | Model | Express the target as a standardised anomaly against a local baseline (D2) | Per-location bloom rates no longer stratify by station |
| BL-005 | P0 | Model | Remove forward-filled rows from every training path; pair only real observations (D4) | Row count equals real pairs; no duplicated lag values |
| BL-006 | P0 | Model | Replace shuffled k-fold with expanding-window chronological splits, with a horizon-length embargo (D4) | Split boundaries recorded; no shared boundary date |
| BL-007 | P1 | Data | Backfill the FAI grid across all 56 pass dates (D3 prerequisite) | Grid CSV covering every collected date |
| BL-008 | P1 | Model | Train per-pixel with PyTorch, three quantile heads, pinball loss (D3, ADR 0002) | Metrics beside baselines; stated sample counts |
| BL-009 | P1 | Frontend | Replace the 4-stop qualitative risk palette (`frontend/src/utils/risk.js`) with a perceptually uniform, colourblind-safe sequential scale | Screenshot plus a colourblind simulation check |
| BL-010 | P1 | Frontend | Clip the risk overlay to the lake surface so risk is not painted over land | Screenshot showing the overlay bounded by the shoreline |
| BL-011 | P1 | Docs | Correct the root README status claims that overstate what runs on real data (CONF-001) | Updated README consistent with `PROJECT_BRIEF.md` |
| BL-012 | P2 | Data | Backfill ERA5-Land weather over the collected pass dates, as the only available source of change-drivers | Weather columns populated and non-null |
| BL-013 | P2 | Frontend | Extend staleness disclosure beyond the header. `Header.jsx` already flags a stale last pass via `overlay.updated_at`, but the date slider, map overlay and station cards still present forward-filled values with no indication of pass age | Screenshot showing pass age at station and map level |
| BL-014 | P2 | Data | Extend the Sentinel-2 history beyond one year; consider 60 m resolution to reduce quota cost | Extended series CSV with recorded date span |
| BL-015 | P3 | Data | Evaluate Sentinel-3 OLCI as a daily-revisit, chlorophyll-oriented complement to Sentinel-2 | Feasibility note with quota and resolution findings |
| BL-016 | P3 | Model | Spatial block cross-validation, holding out lake regions rather than random pixels (ASM-008) | Region-held-out validation results |
| BL-017 | P3 | Model | Convolutional recurrent model over the raster sequence, once timestep depth allows (ADR 0002) | Blocked pending BL-014 or BL-015 |
| BL-020 | P1 | Harness | Upgrade the mounted harness when the kernel is next revised. Mounted from `agent-harness-kernel` `testing` @ `a5f428d`; the owner is actively improving the kernel, partly from findings this mount produced. Re-mount or diff-merge, re-run the doctor, and record the new kernel commit in `RUN_STATE.md` | Doctor passes against the new kernel; commit recorded |
| BL-021 | P2 | Frontend | Reduce the generated-default visual excess: the two blurred colour halos in `app.css`, and the blanket `backdrop-filter: blur(18px) saturate(140%)` on every panel. Full restyle if time allows; removing the decorative excess is the floor | Screenshots before and after |
| BL-019 | P1 | Frontend | Render the mandated "TRL 2 · resultados no validados en campo" seal in the Modelo view. It is currently an unreachable default in `backend/app/routers/model_metrics.py`, shadowed by the populated `caveats` key in `metrics.json`. The seal and the smoke-test caveats are different texts and both belong | Screenshot of the Modelo view showing the seal |
| BL-018 | P3 | Hygiene | Remove `xgboost` from `requirements.txt` unless a use appears (ASM-011) | Updated requirements file |

## Rules

- Backlog items should be tied to source, ADRs, user decisions, or explicit
  project goals.
- Do not pad the backlog with work that has no product, quality, evidence, or
  operational value.
- If a work item changes visible behavior, define how it will be verified.

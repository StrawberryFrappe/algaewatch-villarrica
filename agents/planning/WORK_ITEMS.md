# Work Items

Use this file for current, actionable work. Keep the larger backlog stable.

Owner column uses author slugs (ADR-sf-0005): `sf` StrawberryFrappe,
`lq` Luchosqi, `user` either contributor acting as themselves rather than through
an agent.

| ID | Status | Task | Owner | Evidence |
|---|---|---|---|---|
| WI-001 | done | Mount harness and obtain user acceptance | `sf` | Accepted by the user 2026-09-10. Review at `agents/reviews/20260909/harness_mount_review.md`; upgrade review at `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| WI-002 | done | Obtain Copernicus Data Space Ecosystem credentials | user | EV-015: the CDSE token endpoint returns 200 with an `access_token`. Verified 2026-09-10; the credentials were already in place and the blocker was stale |
| WI-003 | done | Notify the original author that the modelling layer is being rebuilt, and raise the map-library question (ADR 0003) | `sf` | Absorbed into `agents/execution/HANDOFF.md`, which states both. Superseded as a separate errand by ADR-sf-0005 |
| WI-004 | done | Make persistence and trivial-rule baselines permanent, re-runnable checks (BL-002) | `sf` | EV-016: `python -m pytest -q` → 36 passed, 7 xfailed. `src/model/baselines.py`, `src/model/integrity.py`, `tests/` |
| WI-005 | blocked | Honest retrain on **lake-mean** FAI, not station data: continuous target, local-baseline anomaly, real observation pairs, chronological splits with a per-row embargo (BL-003 to BL-006). Scope and signal settled in ADR-sf-0008; the original "on station data" phrasing is void under ADR-sf-0007. Designed and design-reviewed 2026-09-10, **not implemented** — blocked on BL-029, BL-030 and BL-031, three defects in already-committed code that the review found. Building over them would have produced a green gate on a still-leaking split | Metrics reported beside both baselines, `mae_fai` with its CV spread, classification figures `null` until the threshold is recalibrated (EV-020) |
| WI-006 | done | Upgrade the mounted harness to the revised kernel (BL-020) | `sf` | Kernel `5dee2cf` recorded in `RUN_STATE.md`; doctor run in `agents/validation/DOCTOR.md`; review in `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| WI-007 | pending | Hand the repository back: deliver `agents/execution/HANDOFF.md`, confirm `lq` can build his local half and run both checks | `sf` | `lq` confirms receipt and a passing `harness_doctor.py` run on his machine |
| WI-008 | pending | Settle ADR 0003 — Leaflet stands, or Mapbox returns | `lq` | ADR 0003 status moves from provisional to accepted or superseded |
| WI-009 | pending | Frontend credibility pass: BL-009, BL-010, BL-013, BL-019, BL-021 | `lq` | Screenshots of the running app, plus a colourblind simulation check for BL-009 |
| WI-010 | done | Install PyTorch, or record that BL-008 cannot proceed | user | EV-017: `torch 2.14.0+cu126`, CUDA available on a GTX 1650 (sm_75). Installed 2026-09-10 |
| WI-011 | pending | Create a venv and install the feature-pipeline dependencies (BL-028) | user | `python -c "import sentinelhub, cdsapi, rasterio, xarray"` succeeds |
| WI-012 | blocked | Replace the station sample points, or keep them disqualified (BL-027, ADR-sf-0007) | `sf` | `test_station_points_are_on_the_lake` in `tests/test_model_integrity.py` stops being xfail |

## Dependencies

- WI-002 and WI-010 both cleared on 2026-09-10, so **M3 is no longer blocked on
  credentials or on the framework**. What now stands between here and BL-007 is
  WI-011: the collection scripts cannot import `sentinelhub`, `cdsapi`,
  `rasterio` or `xarray` on this machine, so working credentials do not yet mean
  a runnable pipeline.
- WI-011 gates BL-007, BL-012 and BL-014, and therefore BL-008 in practice: a
  per-pixel model needs the grid backfill that collection produces.
- WI-008 gates WI-009. Frontend work starting before the map library is settled
  risks doing Leaflet work twice.
- WI-004 gated WI-005 by sequencing choice, not technical necessity, and is now
  done. The baselines are executable, so the retrain is measured against them
  from its first run rather than compared retrospectively and flattered.
- **WI-012 constrains WI-005.** ADR-sf-0007 disqualifies station-point FAI as a
  training signal, and the real coordinates have not arrived. WI-005 as written
  says "honest retrain on station data"; that phrasing predates EV-014. The
  honest retrain can fix the target, the pairing and the splits, and it still
  cannot make four placeholder points measure the lake. Read WI-005 as the
  modelling fixes only, with per-pixel sampling (ADR 0004 D3) as the path to a
  model that is about water.
- **WI-005's signal is settled and its implementation is not.** ADR-sf-0008 names
  `lake_mean_fai` as the interim source — water-mask mean, no station coordinate
  in its derivation, so ADR-sf-0007 does not reach it. 35 honest pairs (EV-019).
  Three defects in committed code block the build, in this order: **BL-029**
  (`chronological_split` embargoes the feature date, so a variable horizon leaks
  and the check still reports pass), **BL-030** (`trivial_rule` reduces to
  "always predict positive" on one group), **BL-031** (the inapplicability guard
  must sit inside the check, not only in `run_all`). BL-032 follows immediately —
  two non-xfailed tests hardcode the check count and break outright against a
  single-group table. None is large; all three are correctness fixes to the gate
  itself, and the gate is what makes WI-005 checkable.
- **WI-011 remains the highest-leverage unblock, and it is the user's.** Four pip
  installs (`sentinelhub`, `cdsapi`, `rasterio`, `xarray`) turn working
  credentials into a runnable pipeline, which gives BL-007 the per-pixel grid,
  which turns 35 rows into roughly 65,000 (EV-008) and makes WI-005's successor
  a real model rather than an honest measurement of a small sample.

## Status Values

- pending
- in_progress
- blocked
- done

## Rules

- Do not mark a work item done until verification evidence is recorded.
- Append new rows at the end, so concurrent additions by two contributors
  conflict visibly rather than interleaving silently.

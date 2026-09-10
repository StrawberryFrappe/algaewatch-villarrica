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
| WI-005 | pending | Honest retrain on station data: continuous target, local-baseline anomaly, chronological splits with embargo (BL-003 to BL-006) | `sf` | Metrics reported beside both baselines |
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

## Status Values

- pending
- in_progress
- blocked
- done

## Rules

- Do not mark a work item done until verification evidence is recorded.
- Append new rows at the end, so concurrent additions by two contributors
  conflict visibly rather than interleaving silently.

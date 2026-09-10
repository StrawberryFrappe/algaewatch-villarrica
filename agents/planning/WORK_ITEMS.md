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
| WI-005 | done | Honest retrain on **lake-mean** FAI, not station data: continuous standardised-anomaly target, causal local baseline, real observation pairs, chronological splits with a per-row embargo (BL-003 to BL-006). Scope and signal settled in ADR-sf-0008; implementation decisions in ADR-lq-0009. Built 2026-09-10 after clearing BL-029 to BL-032: `src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`, `scripts/train_lake_anomaly.py`, `data/processed/lake_anomaly_dataset.csv`, `src/model/artifacts/lake_anomaly/`. **The retrain loses to both baselines** — that is the reported result (rule MI-1, ADR 0004) | EV-021: `mae_fai` 0.003919 ± 0.002135 vs persistence 0.001362 and climatology 0.000775, `beats_baselines` both `false`; classification `null` (EV-020). Candidate gate run → 10 passed, 5 xfailed. Independent implementation review still pending |
| WI-006 | done | Upgrade the mounted harness to the revised kernel (BL-020) | `sf` | Kernel `5dee2cf` recorded in `RUN_STATE.md`; doctor run in `agents/validation/DOCTOR.md`; review in `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| WI-007 | pending | Hand the repository back: deliver `agents/execution/HANDOFF.md`, confirm `lq` can build his local half and run both checks | `sf` | `lq` confirms receipt and a passing `harness_doctor.py` run on his machine |
| WI-008 | done | Settle ADR 0003 — Leaflet stands, or Mapbox returns | `lq` | ADR 0003 status moved from provisional to Accepted on 2026-09-10; Leaflet confirmed by `lq` |
| WI-009 | done | Frontend credibility pass: BL-009, BL-010, BL-013, BL-019, BL-021 | `lq` | Done 2026-09-10. `agents/reviews/20260910/frontend_credibility_pass.lq.md` + screenshots; palette CVD validation in that review; deviations in ADR-lq-0007 |
| WI-010 | done | Install PyTorch, or record that BL-008 cannot proceed | user | EV-017: `torch 2.14.0+cu126`, CUDA available on a GTX 1650 (sm_75). Installed 2026-09-10, re-verified 2026-09-10 in a second worktree. Evidence covers `sf`'s machine only; `lq`'s is unscanned, and BL-008 has no owner-machine requirement recorded |
| WI-011 | pending | Create a venv and install the feature-pipeline dependencies (BL-028) | user | `python -c "import sentinelhub, cdsapi, rasterio, xarray"` succeeds |
| WI-012 | blocked | Replace the station sample points, or keep them disqualified (BL-027, ADR-sf-0007) | `sf` | `test_station_points_are_on_the_lake` in `tests/test_model_integrity.py` stops being xfail |
| WI-013 | done | Light pastel theme + topbar + contained layout (owner redirect 2026-09-10). Focused pass, not a per-view redesign. **Minted by `lq` as WI-011 and renumbered here** — see the ID-collision note below | `lq` | Done 2026-09-10. ADR-lq-0008; `agents/reviews/20260910/light-theme-pass_screens/`. Light-mode risk ramp re-validated. Pending: real `logo.png`, sub-768px QA |

## Dependencies

- WI-002 and WI-010 both cleared on 2026-09-10, so **M3 is no longer blocked on
  credentials or on the framework**. What now stands between here and BL-007 is
  WI-011: the collection scripts cannot import `sentinelhub`, `cdsapi`,
  `rasterio` or `xarray` on this machine, so working credentials do not yet mean
  a runnable pipeline.
- WI-011 gates BL-007, BL-012 and BL-014, and therefore BL-008 in practice: a
  per-pixel model needs the grid backfill that collection produces.
- WI-008 gated WI-009, and both are now done. Leaflet stands (ADR 0003 Accepted),
  so no Leaflet work was done twice.

### ID collision, 2026-09-10 — WI-011

**Two work items were minted as WI-011.** `sf` minted it at 00:34:51 in `23b30ca`
for the venv and feature-pipeline install (BL-028); `lq` minted it again at
01:17:17 in `24fa5fd` for the light-theme pass, from a base commit that contained
neither row. The merge surfaced the clash rather than interleaving it, which is
what the append-at-the-end rule below is for.

Resolved by mint order: the earlier claim keeps the number. WI-011 remains the
venv install, and `lq`'s light-theme pass is **WI-013**. `ADR-lq-0008` and
`agents/reviews/20260910/light-theme-pass_screens/` still describe it correctly;
only the ID moved. Anything of `lq`'s citing "WI-011" for the theme work means
WI-013.

Two lessons, and neither is about the table. `lq` committed both changes directly
to `main`, which `agents/execution/WORKFLOW.md` reserves for released state merged
from `develop` — had the work landed on `develop`, the clash would have appeared
at push time instead of two commits later. And he re-marked WI-010 as `blocked`
against EV-017, which records PyTorch working with CUDA. That was not a
disagreement: EV-017 was written 43 minutes before his commit, on a branch he had
not fetched. The number is restored to `done` and its scope is now stated —
`sf`'s machine, measured — so the next reader can tell what was verified where.
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

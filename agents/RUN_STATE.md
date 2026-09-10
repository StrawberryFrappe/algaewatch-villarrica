# Run State

## Current Phase

Harness accepted. Implementation under way on `sf`'s half. **WI-004 is done** —
the baselines and the model-integrity checks are a permanent test suite.
**WI-005 is designed and blocked**: its signal and scope are settled in
ADR-sf-0008, and a design review found three defects in already-committed code
(BL-029 to BL-031) that must be fixed before any retrain can be judged honestly.

## Status

- **Harness accepted by the user on 2026-09-10**, clearing GATE-HM. Kernel
  `5dee2cf`, two contributors, English canonical with Spanish siblings.
- **GATE-LOCAL was not actually clear when this session began.** The previous
  RUN_STATE asserted that `agents/local/CAPABILITIES.md` existed; it did not, in
  either the main checkout or the worktree, and `harness_doctor.py --strict`
  reported it as a hard blocker on the first run. A fresh scan was written and
  the doctor now reports 0 blockers, 0 warnings. This is the second time a
  RUN_STATE claim has outrun reality — see the script-limitation note in
  `agents/validation/DOCTOR.md`.
- **WI-004 / BL-002 delivered.** `src/model/baselines.py` (persistence, trivial
  rule, one embargoed chronological splitter), `src/model/integrity.py` (seven
  GATE-MODEL checks), and `tests/` (36 passed, 7 xfailed). EV-016.
- **Reviewed by a subagent**, not self-reviewed. Three findings, all fixed. The
  serious one: the baselines were being scored on a partition rebuilt by a
  non-stable sort, so they could have been measured on different rows than the
  model. See `agents/reviews/20260910/implementation-review.sf.md`.
- **`train.py` now reports baselines** beside every metric, and
  `src/model/artifacts/metrics.json` carries `baselines` and `beats_baselines`,
  both `false`. Rule MI-1 is satisfied in the artifact. It is **not** satisfied
  on screen: the Modelo view still shows bare metrics, which is BL-026.
- **A new defect was found, upstream of the audit's findings.** Two of the four
  station coordinates are not on the lake — pucon 0.77 km, sur 0.98 km from the
  nearest sampled water pixel, sur south of the lake entirely — so their FAI is
  shoreline vegetation, not water. EV-014, ADR-sf-0007, BL-027.
- **Credentials work.** The CDSE token endpoint authenticates (EV-015). The
  WI-002 blocker recorded here was stale. `CDS_TOKEN` and `GEMINI_API_KEY` are
  present but still unexercised.
- **PyTorch installed with working CUDA** — `2.14.0+cu126` on a GTX 1650, sm_75
  (EV-017). WI-010 / BL-024 cleared.
- **PR-2 restored.** The real `.env` was sitting *inside* the repository root at
  `H:\algaewatch-villarrica\.env`, protected only by a gitignore line rather than
  structurally. Moved one directory above the root, where `find_dotenv()` still
  resolves it. Nothing had leaked: it was untracked, and EV-006 still holds.
- Existing project rules preserved and fused into `AGENTS.md` as PR-1 to PR-4.
- Two working languages, GATE-I18N active (ADR-sf-0006).
- **GATE-I18N was failing, and the check was what was wrong.** The status below
  claimed 5 of 5 current; the next session's first run reported one stale.
  `RUN_STATE.es.md` had recorded the **CRLF** blob sha of a source it had in fact
  translated correctly and completely. `check_translations.py` hashed the bytes on
  disk, so the recorded hash described the previous session's working copy rather
  than the commit. It now folds CRLF to LF before hashing. EV-018, commit
  `c875514`; the third instance of a claim outrunning reality, and the first whose
  remedy was to fix the check rather than the claim — see `DOCTOR.md`.
- **WI-005 is designed, not built (ADR-sf-0008).** Its original phrasing, "honest
  retrain on station data", is void under ADR-sf-0007. The admissible signal is
  `lake_mean_fai` — the water-mask mean, with no station coordinate in its
  derivation — giving 35 honest pairs. Two measurements shaped the design: causal
  climatology (MAE 0.000945) **beats** persistence (0.001333), so beating
  persistence alone proves nothing; and the recorded bloom threshold of 0.025916
  is an order of magnitude above the lake-wide maximum of 0.001999, so applied
  lake-wide it labels every row negative and the whole classification surface is
  vacuous until recalibrated. EV-019, EV-020.
- **The design review found three defects in committed code**, which is why
  nothing was implemented: `chronological_split` embargoes the feature date rather
  than the target date and its check still reports pass (BL-029); `trivial_rule`
  reduces to "always predict positive" on a single-group table (BL-030); and the
  inapplicability guard must sit inside the check, not only in `run_all`, because
  the tests call it directly (BL-031). Two of the three cause a **false pass**.

## Next Action

Fix **BL-029, BL-030, BL-031 and BL-032**, in that order, before implementing
WI-005. All four are corrections to the gate and its baselines; two of them
currently produce a false pass, which is worse than a failure. The gate is what
makes a retrain checkable, so it has to be right first.

Then implement WI-005 per ADR-sf-0008: a new `lake_anomaly.py` module under `src/features/`, with
no `sentinelhub` import, parameterised on a spatial-unit column so ADR 0004 D3
substitutes `pixel_id` rather than forcing a rewrite; a causal rolling baseline
from observations strictly **before** `t`; Ridge rather than GradientBoosting on
35 rows; `mae_fai` with its CV spread as the headline and the classification
figures `null` under PR-3. Honest artifacts go to a new directory —
`src/model/artifacts/` must not be overwritten, because the backend loads it at
import and serves per-station, so a lake-wide model cannot fill four station
cards. Rewiring the serving path is not WI-005.

**WI-011 is the highest-leverage item on the board and it is the user's.** Four
installs — `sentinelhub`, `cdsapi`, `rasterio`, `xarray` — turn working
credentials into a runnable pipeline, which gives BL-007 the per-pixel grid, which
turns 35 rows into roughly 65,000 (EV-008).

`lq` still owes ADR 0003 before frontend work begins.

A session handoff covering what was done, what the backlog expects next, and
how to resume from `develop` is at `agents/execution/SESSION_HANDOFF.sf.md`.

## Progress Checklist

Kept current so another contributor can pick this up mid-flight.

| Step | State |
|---|---|
| Harness accepted (GATE-HM) | done 2026-09-10 |
| Local half built (GATE-LOCAL) | done — `agents/local/CAPABILITIES.md`, doctor 0/0 |
| `.env` moved out of the repository tree (PR-2) | done |
| `src/model/baselines.py` | done, committed |
| `src/model/integrity.py` | done, committed |
| `tests/` suite + `pytest.ini` + `pytest` in requirements | done, committed |
| `train.py` records baselines; artifacts regenerated | done, committed |
| Evidence, ADR, backlog, work items, test strategy updated | done |
| Doctor and translation checks re-run and recorded | done |
| Independent review of the WI-004 diff | done — APPROVE WITH FIXES, 3 findings, all resolved in `c49c9a5` |
| GATE-I18N hashing fix | done — EV-018, commit `c875514` |
| WI-005 signal and scope | done — ADR-sf-0008, user-approved |
| WI-005 design review | done — three committed-code defects found, BL-029 to BL-031 |
| WI-005 retrain | **blocked** on BL-029, BL-030, BL-031, BL-032 |

## Blockers

- **BL-029, BL-030, BL-031, BL-032 — the gate's own correctness.** Two of the
  four produce a false pass rather than a failure: `chronological_split` embargoes
  the feature date instead of the target date and `check_chronological_split`
  compares only against the constant `HORIZON_DAYS = 7`; and
  `check_label_not_stratified_by_station` reports a 0.000 spread as a pass on a
  single-group table. These block WI-005 and, through it, BL-003 to BL-006.
- **WI-011 / BL-028 — the feature pipeline cannot run on this machine.**
  `sentinelhub`, `cdsapi`, `rasterio` and `xarray` are all absent from the
  interpreter on PATH and there is no virtual environment. Credentials working
  does not mean collection working. This blocks BL-007, BL-012 and BL-014, and
  therefore BL-008 in practice.
- **WI-012 / BL-027 — station coordinates.** Blocked on the real GPS arriving
  with the SNIA CSVs. Until then, ADR-sf-0007 disqualifies station-point FAI as a
  training signal, and `check_station_points_on_water` enforces it.
- **ADR 0003** (map library) is `lq`'s to settle and he has not yet answered.
  Frontend work should not begin before he does.

## Last Verified State

- `python agents/harness_doctor.py --root . --strict` — 0 blockers, 0 warnings.
  Recorded in `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — 5 of 5 current, after the hashing fix
  in `c875514`. Re-verified by rewriting a source as CRLF and confirming the gate
  stays green, so this figure is now transferable between checkouts.
- `python -m pytest -q` — 36 passed, 7 xfailed (EV-016).
- Model artifacts regenerated from the committed `training_dataset.csv`.
  Precision, recall, F1, AUC and the confusion matrix reproduce exactly;
  `mae_fai` moved 0.00865 → 0.00867 and mean CV AUC 0.9922 → 0.9925. The
  committed artifact already disagreed with EV-013's own reproduction before this
  change; the drift and its likely cause are recorded in `EVIDENCE_INDEX.md`
  rather than silently superseded.
- `data/processed/` is byte-unchanged. Artifacts were regenerated by calling
  `train()` on the committed table, not through `scripts/train_model.py`, which
  would have rebuilt and overwritten the table every evidence figure is pinned to.
- The backend load path still works against the regenerated artifacts
  (`src.model.infer.load_artifacts`, `predict_risk`).
- **Application code has now been modified**, for the first time since the fork:
  `src/model/train.py` and the artifacts under `src/model/artifacts/`, plus the
  new modules and tests. `src/features/`, `backend/`, `frontend/`, `scripts/` and
  `data/` remain as the original author left them.

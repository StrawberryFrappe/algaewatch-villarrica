# Run State

## Current Phase

Harness accepted. Implementation under way on `sf`'s half. **WI-004 is done** —
the baselines and the model-integrity checks are a permanent test suite — and
the next step is WI-005, the honest retrain.

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

## Next Action

`sf` begins **WI-005** — the honest retrain: continuous target, local-baseline
anomaly, real observation pairs only, chronological splits with a horizon-length
embargo (BL-003 to BL-006). The gate is already written, so success is defined in
advance: `tests/test_model_integrity.py` xfails must flip to passes and their
marks be removed in the same change.

Read WI-005's "on station data" phrasing in light of ADR-sf-0007. The modelling
fixes are all still correct and worth making; they cannot by themselves make four
placeholder coordinates measure the lake. Per-pixel sampling (ADR 0004 D3) is the
path to a model that is about water, and it needs WI-011 first.

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
| WI-005 retrain | not started |

## Blockers

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
- `python agents/check_translations.py` — 5 of 5 current.
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

# Run State

## Current Phase

**The per-pixel retrain is built, trained and measured (2026-09-10, ADR-sf-0010),
on branch `feat/per-pixel-retrain-verdict` — not yet merged and NOT yet
independently reviewed.** It is the first model in this repository trained on
fully real inputs end to end: 56 Sentinel-2 passes, 13 months of ERA5-Land, no
forward-filled row.

**It loses to both baselines.** MAE 0.001999 ± 0.001501 against persistence
0.001402 and climatology 0.001296 — the reported result under rule MI-1, not a
number to be improved by tuning. Two of four folds *do* beat climatology; fold 2
(2026-02-13..2026-03-08, the most volatile window in the series and the one that
matters operationally) is catastrophic at 0.004568 and drags the unweighted
mean. The q10–q90 interval is well calibrated: 0.8135 coverage against a nominal
0.80.

**Wired into the product on branch `demoday` (based on the above).**
`src/model/per_pixel_infer.py` gives the artifact its first load path — it was
write-only — and `GET /model/candidate` reports the candidate beside its
baselines with the per-fold detail. The Modelo view renders it, badged
`NO ALIMENTA EL MAPA`, because `/risk` and `/forecast` still run the legacy
artifacts. Three bugs fixed on the way: a Windows cp1252 encoding bug that
rendered the Spanish caveats as mojibake, a `leaflet.heat` zero-width
`getImageData` crash that unmounted the **entire** dashboard, and the absence of
any React error boundary. Tests 92 passed / 8 xfailed.

Also on that branch: the two open questions from `PARA_JUN.md` §3 are decided
(ADR-sf-0010 D1/D2), and three defects found by running the runbook end to end
are fixed — `collect_era5.py` could never complete, `baselines.trivial_rule`
crashed the whole gate on a continuous-target table, and a plumbing test asserted
a label was always present. See "Blockers" for what is still open.

Harness accepted. Implementation under way on `sf`'s half. **WI-004 is done** —
the baselines and the model-integrity checks are a permanent test suite.
**BL-029 to BL-032 are fixed** — the four gate-correctness defects the WI-005
design review found, two of which produced a false pass. **WI-005 is built**
(ADR-lq-0009): `src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`, a
committed candidate table and honest artifacts. The interim lake-mean retrain
**loses to both baselines** — the reported result under rule MI-1. All of this
was on branch `fix/sf-model-gate-correctness`, **independently reviewed** —
APPROVE WITH FIXES, no Critical, both false passes confirmed closed, the legacy
path confirmed untouched; the one Important finding (a false-*fail* on dense
variable-horizon splits) and six Minor findings fixed on the same branch, then
**merged to `main` 2026-09-10.** The brief for the next push — retrain to beat
both baselines via per-pixel + weather — is at
`agents/execution/SESSION_HANDOFF.lq.md`.

## Status

- **BL-029 to BL-032 fixed and WI-005 built, 2026-09-10** (ADR-lq-0009), by
  `lq` standing in for `sf` on the model half. **Independently reviewed**
  (APPROVE WITH FIXES, no Critical — `implementation-review.lq.md`), all findings
  applied, **merged to `main` 2026-09-10.** The four gate defects — two of them
  false passes — are
  corrected with before/after evidence. The interim lake-mean retrain
  (`src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`) is honest and
  **loses to persistence and climatology** (EV-021); it satisfies PR-3 and
  drops the location-proxy label. It is not shippable and does not fill the four
  station cards. `unit_col` seam is in place for ADR 0004 D3 (`pixel_id`).
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
- **`lq`'s frontend work is merged, and it arrived on `main`.** ADR 0003 accepted
  (Leaflet stands), WI-009's credibility pass done with screenshots — BL-009's
  CVD-validated magma ramp, BL-010's overlay clipped to the lake, BL-013's
  staleness disclosure, BL-019's TRL-2 seal now actually rendered, BL-021's glass
  and halos cut — plus a light pastel theme and topbar (ADR-lq-0008). Both commits
  went straight to `main`, which `WORKFLOW.md` reserves for released state merged
  from `develop`; `develop` now contains them by merge.
- **One ID collision, resolved by mint order.** Two work items were minted as
  WI-011: the venv install at 00:34:51, `lq`'s light-theme pass at 01:17:17 from a
  base holding neither. WI-011 stays the venv install; the theme pass is WI-013.
  `lq` also re-marked WI-010 as blocked against EV-017 — not a disagreement, he
  had not fetched the branch that recorded it. Restored to done, with its scope
  now stated as `sf`'s machine. The full note is in `WORK_ITEMS.md`; the
  append-at-the-end rule is what made both visible instead of silent.
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

**1. Merge `demoday`.** It carries the retrain, the serving path and the docs,
and it has been independently reviewed (APPROVE WITH FIXES, all applied). Nothing
in it is known-broken. Merging is a judgement call for the owner, not a blocked
step — the branch is `demoday` precisely because it was cut for a demo.

**2. Decide what to do about `check_no_fabricated_rows` (BL-037).** It fails on
the per-pixel table with inflation 1.011. Investigated: false positive. 562
duplicate groups, *none* sharing a date, on a `fai_now` carrying only 1,996
distinct values across 56,668 rows because FAI is quantised to 5 decimals. The
check was deliberately **not** changed — adding `date` to its key would make it
pass and would also destroy the forward-fill detection it exists for. Someone
other than the candidate's author should choose the fix.

**3. Then, if the model is to be improved:** the fold detail says the problem is
volatility, not features. Fold 2's target std is 2.35 against ~0.7 elsewhere. A
heavier-tailed loss, a variance-aware baseline, or simply more passes are the
honest levers. Do not tune against the reported folds.

Historical context for the push that produced this — `agents/execution/SESSION_HANDOFF.lq.md`. In short: the interim
lake-mean model can't clear climatology because the lake-mean series is noise
around a slow mean and it has no change-drivers. The real leap is ADR 0004 D3 +
D4 together — **per-pixel sampling** (BL-007: backfill the FAI grid across all
56 passes → ~65,000 samples, feed it through the same `build_anomaly_pairs` with
`unit_col="pixel_id"`) and **ERA5 weather change-drivers** (BL-012). Both are
blocked on **WI-011** (the user's: `pip install cdsapi rasterio xarray`), plus
the CDS ERA5 licence and, for BL-008, PyTorch on this machine (ADR 0002).

WI-005 recap (ADR-lq-0009, EV-021): the interim lake-mean retrain is honest and
does **not** beat persistence (0.0014) or climatology (0.0008) — `mae_fai`
0.0039 ± 0.0021 over 4-fold expanding CV. It fixes fabrication (PR-3) and the
location-proxy label; it is not a shippable model, and it does not fill the
dashboard's four station cards. `src/model/artifacts/` (the backend's) is
byte-unchanged; honest artifacts are in `src/model/artifacts/lake_anomaly/`.

`lq`'s half: ADR 0003 accepted, WI-008 / WI-009 / WI-013 done. `develop` was
retired 2026-09-10 — work lands on `main` directly (`WORKFLOW.md`).

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
| WI-005 design review | done — four committed-code defects found, BL-029 to BL-032 |
| BL-029 to BL-032 gate fixes | done — ADR-lq-0009; both false passes shown fixed; default suite 70 passed / 7 xfailed |
| WI-005 retrain | done — ADR-lq-0009; loses to both baselines (EV-021); candidate gate 11 passed / 1 skipped / 4 xfailed |
| Independent review of the BL-029..032 + WI-005 diff | done — APPROVE WITH FIXES, `implementation-review.lq.md`; 1 Important + 6 Minor findings applied |
| Merge `fix/sf-model-gate-correctness` to `main` | done 2026-09-10 |
| Retrain-to-beat-baselines brief | done — `agents/execution/SESSION_HANDOFF.lq.md` (per-pixel D3 + ERA5 D4, prerequisites, reuse map, constraints, done criteria) |

## Blockers

- **BL-037 — `check_no_fabricated_rows` misfires on the per-pixel table. OPEN.**
  Inflation 1.011. Investigated and confirmed a false positive (EV-024c): 562
  duplicate groups, none sharing a date, on a `fai_now` carrying only 1,996
  distinct values across 56,668 rows, because FAI is quantised to 5 decimals.
  Deliberately **not** fixed by the candidate's author — adding `date` to the
  key makes it pass and destroys the forward-fill detection the check exists
  for. Needs someone else's decision. Blocks a clean GATE-MODEL run, not the
  verdict itself.
- **BL-035, BL-036 — cleared 2026-09-10** (ADR-sf-0010, EV-024). `era5.py`'s
  assembly dropped a column its own projection had already removed, so
  `collect_era5.py` could never complete; `baselines.trivial_rule` crashed the
  whole gate on a table with no `bloom_7d`; and the plumbing test assumed a
  label was always present. All three fixed.
- **WI-011 / BL-028 — CLEARED 2026-09-10.** The feature pipeline runs. A fresh
  `.venv` from `pip install -r requirements.txt` imports `sentinelhub`,
  `cdsapi`, `rasterio`, `xarray`, `netCDF4` and `torch`, and `collect_era5.py`
  completed a full 13-month backfill. Note the earlier entry below was itself
  stale: **no `.venv` existed in any of the six checkouts** when this session
  started (EV-022).
- **Definition of Done §7 — CLEARED 2026-09-10 for `demoday`.** Independent
  subagent review of the full diff against `32a1af9`: **APPROVE WITH FIXES**, no
  Critical, no Important. It cleared the branch's central claim (early stopping
  selects on training data only and cannot leak into the reported MAE) and
  confirmed the one relaxed gate assertion is a correction rather than a
  weakening. Three findings, all applied — including a stale `requirements.txt`
  comment the author had falsified himself on the same branch.
  `agents/reviews/20260910/implementation-review-demoday.sf.md`.
- **BL-029, BL-030, BL-031, BL-032 — cleared 2026-09-10** (ADR-lq-0009). The
  target-date embargo, the single-group climatology dispatch, the in-check
  inapplicability guard and the shape-agnostic plumbing tests are all in place;
  both false passes are demonstrated fixed. No longer block BL-003 to BL-006 or
  WI-005 — WI-005 is built.
- **WI-011 / BL-028 — the feature pipeline still cannot run.** On `lq`'s `.venv`
  (2026-09-10) `sentinelhub` 3.11.5 is present but `cdsapi`, `rasterio` and
  `xarray` are not, so `python -c "import sentinelhub, cdsapi, rasterio, xarray"`
  still fails. Credentials working does not mean collection working. Blocks
  BL-007, BL-012, BL-014, and BL-008 in practice. (The earlier "no virtual
  environment" note described `sf`'s machine; corrected here — a `.venv` exists
  on `lq`'s checkout and runs the tests and both retrains.)
- **WI-012 / BL-027 — station coordinates.** Blocked on the real GPS arriving
  with the SNIA CSVs. Until then, ADR-sf-0007 disqualifies station-point FAI as a
  training signal, and `check_station_points_on_water` enforces it.
- **ADR 0003 is settled** and no longer blocks anything. Leaflet stands, accepted
  by `lq` on 2026-09-10, and WI-008 and WI-009 are both done.

## Last Verified State

### 2026-09-10, `feat/per-pixel-retrain-verdict` (per-pixel retrain)

Environment rebuilt from scratch this session — **no `.venv`, no
`data/raw/era5/`, no `frontend/node_modules` existed in the main checkout or any
of the five worktrees**, contrary to `PARA_JUN.md` §1. Python 3.11.0,
`torch 2.14.0+cpu` from a plain `pip install -r requirements.txt`.

- `python -m pytest -q` — **80 passed, 8 xfailed** (was 78/8; +2 for the
  early-stopping seam).
- `python agents/harness_doctor.py --root . --strict` — 0 blockers, 0 warnings.
  GATE-LOCAL needed a fresh `agents/local/CAPABILITIES.md`; that directory is
  never committed, so **every new worktree must re-scan**.
- `python agents/check_translations.py` — 5 checked, 0 problems.
- `python scripts/collect_era5.py` — 13 months, **56 rows** to
  `data/processed/era5_daily.csv`. Took ~50 min of CDS queue.
- `python scripts/build_per_pixel_dataset.py` — 56,668 pairs, 1,866 pixels,
  34 anchors. Blocks {0: 3625, 1: 11932, 2: 9977, 3: 31134}. ~30s, no API.
- `python scripts/train_per_pixel.py` — **MAE 0.001999 ± 0.001501 |
  persistence 0.001402 | climatology 0.001296 | beats both: false.**
- **Candidate GATE-MODEL run** —
  `ALGAEWATCH_DATASET=data/processed/per_pixel_anomaly_dataset.csv`
  `ALGAEWATCH_METRICS=src/model/artifacts/per_pixel/metrics.json`
  `python -m pytest -q tests/test_model_integrity.py` → **12 passed, 2 skipped,
  3 failed.** The three failures are the two honest MI-1 losses plus the
  documented `no_fabricated_rows` false positive (BL-037). No check crashes any
  more. Note the runbook in `PARA_JUN.md` step 4 gives this command with a bare
  filename; the variable takes a **repo-root-relative path**.
- Dashboard verified running end to end: `uvicorn backend.app.main:app --port
  8000` plus `npm run dev --prefix frontend`; all four views render real data,
  `npm run build` clean in 2.17s. The Modelo view's BL-026 baselines card
  displays correctly.
- `src/model/artifacts/` (the backend's legacy model) is **unchanged except for
  the `caveats` string**; every metric is byte-identical, verified key-wise.

### Earlier

- `python agents/harness_doctor.py --root . --strict` — 0 blockers, 0 warnings.
  Recorded in `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — 5 of 5 current, after the hashing fix
  in `c875514`. Re-verified by rewriting a source as CRLF and confirming the gate
  stays green, so this figure is now transferable between checkouts.
- `python -m pytest -q` — **70 passed, 7 xfailed** on `lq`'s `.venv` (py3.13,
  scikit-learn 1.7.2). Was 36/7 at EV-016; +34 from the BL-029..032 gate fixes,
  WI-005, and the review-fix regression/artifact tests.
- **Candidate GATE-MODEL run** —
  `ALGAEWATCH_DATASET=data/processed/lake_anomaly_dataset.csv`
  `ALGAEWATCH_METRICS=src/model/artifacts/lake_anomaly/metrics.json`
  `python -m pytest -q tests/test_model_integrity.py` → **11 passed, 1 skipped,
  4 xfailed**. The lake-mean retrain passes `no_fabricated_rows` (PR-3) and
  `label_not_a_proxy` (inapplicable, one unit); still xfails MI-1 vs persistence,
  the trivial-rule check (f1 null), the constant-label shortcut check, and
  station provenance. The MI-2 test is skipped — its `pipeline_split` fixture is
  a four-station path WI-005 does not use.
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
- **Application code modified this session** (branch `fix/sf-model-gate-correctness`):
  `src/model/baselines.py`, `src/model/integrity.py` (BL-029..032); new
  `src/features/lake_anomaly.py`, `src/model/lake_anomaly.py`,
  `scripts/train_lake_anomaly.py` (WI-005); new tests. New committed data:
  `data/processed/lake_anomaly_dataset.csv`, `src/model/artifacts/lake_anomaly/`.
  `src/model/artifacts/` (the backend's) and `src/model/train.py` are
  byte-unchanged from the WI-004 state; `backend/`, `frontend/` untouched by `sf`.

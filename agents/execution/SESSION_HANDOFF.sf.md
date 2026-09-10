# Handoff: GATE-I18N fixed, WI-005 designed and blocked

Written 2026-09-10 by `sf`, replacing the previous handoff of the same name.
Distinct from `agents/execution/HANDOFF.md`, which is the one-time handback of
the repository to `lq` and must not be overwritten with session state.

Read `AGENTS.md` and `agents/RUN_STATE.md` first; this file assumes them.

## Current State

Branch **`develop`**, pushed through `c3beadf`; later commits are local only.
`main` is untouched at `912376c`.

```
f4c8f2d         docs(harness): settle WI-005's signal, record the defects that block it
c875514         fix(harness): hash LF-normalized bytes in the translation gate
c3beadf         docs(harness): add a session handoff and write down branch naming
23b30ca         docs(harness): record WI-004, the station-provenance defect, and cleared blockers
```

Application code is unchanged this session. `src/model/` is as WI-004 left it;
`src/features/`, `backend/`, `frontend/`, `scripts/` and `data/` are as the
original author left them. The only non-document change is
`agents/check_translations.py`, which is harness tooling.

## What Happened

### GATE-I18N was failing, and the check was the thing that was wrong

The previous handoff and `RUN_STATE.md` both recorded translations as "5 of 5
current". The first run of this session reported one stale.

`agents/RUN_STATE.es.md` had recorded `source_sha` `28592ee…`. That is the blob
sha of the current `agents/RUN_STATE.md` **with CRLF line endings**; the LF sha,
and the committed blob, is `ef31b0a…`, and `28592ee…` names no object in the
repository at all. The Spanish text was a complete and current translation — the
section structure matches 1:1 and the paragraph added in `c3beadf` is present.

Cause: `check_translations.py` hashed with `git hash-object --no-filters`, which
reads the bytes on disk. `.gitattributes` pins `agents/**/*.md` to `eol=lf`, which
fixes what a *checkout* writes but not what an editor or shell heredoc writes
during the session that records the hash. The same file hashed one way there and
another way in every checkout since.

Fixed in `c875514`: `blob_sha` folds CRLF to LF before hashing, in Python rather
than through a subprocess. On a clean tree that is byte-identical to what the
protocol's hand recipe prints, so the recipe still stands. Verified by rewriting a
source as CRLF and confirming the gate stays green. EV-018;
`TRANSLATION_PROTOCOL.md` carried the wrong reasoning and now states the limit
accurately; `DOCTOR.md` logs it as a third instance of a harness claim outrunning
reality, and why its remedy differs from the first two.

### WI-005 was designed, reviewed, and deliberately not built

**WI-005's premise was void.** "Honest retrain on station data" cannot be done:
ADR-sf-0007 clause 1 bars any training path from consuming `fai_<station_id>`
columns, and ADR 0004's fallback — the document WI-005 descends from — names
station data explicitly, having been written one day before that bar existed.

**The signal that survives is `lake_mean_fai`**, in
`data/processed/fai_series_raw.csv`, from `FaiRaster.lake_mean` — the nanmean of
FAI over the SCL water mask. No station coordinate appears in its derivation, so
ADR-sf-0007 does not reach it. Settled in **ADR-sf-0008**, with the user's
approval on all three decisions: lake-mean now with a pixel-ready seam; the
trivial rule becomes climatology where there is one spatial unit; an inapplicable
check is omitted, never passed.

**Two measurements changed the design** (EV-019, EV-020):

- 35 honest pairs at a 5-to-9-day spacing. Persistence MAE 0.001333;
  causal expanding-mean climatology MAE **0.000945**. Climatology *beats*
  persistence — the reverse of the station table, where the trivial rule was the
  leak. Any lake-wide model must clear 0.000945, so `check_beats_persistence`
  alone is no longer a meaningful bar.
- `lake_mean_fai` spans −0.008248 to +0.001999. The recorded bloom threshold is
  0.025916, an order of magnitude above the maximum, because it was calibrated on
  the contaminated station series. Applied lake-wide it labels every row negative,
  so `bloom_7d` is constant and the entire classification surface — two of the
  seven gate checks, four of five `ValidationMetrics` fields — is vacuous until a
  threshold is recalibrated.

**A design review then found three defects in already-committed code.** They are
why nothing was implemented: building over them produces a green gate on a split
that still leaks, which is precisely the failure this project's gate exists to
prevent.

## Blockers

Ordered by what unblocks what.

| ID | What | Who |
|---|---|---|
| **BL-029** | `chronological_split` embargoes the row's **feature** date, not its target date. With horizons of 5 to 8 days and a 7-day embargo, a training row's target lands inside the validation window — EV-005's defect through a new door. `check_chronological_split` compares against the constant `HORIZON_DAYS = 7`, so it reports **pass** on a leaking split | `sf` |
| **BL-030** | `trivial_rule` on a single-group table picks the only group and predicts `True` for every row: "always predict positive", not the location rule it documents and not climatology. Needs a cardinality dispatch, **not** an in-place rewrite — the group form is what reproduces EV-002 | `sf` |
| **BL-031** | The inapplicability guard must live **inside** `check_label_not_stratified_by_station`. `tests/test_model_integrity.py` calls it directly, so a guard only in `run_all` still yields a 0.000-spread vacuous pass — surfacing under `xfail(strict=True)` as a spurious XPASS *failure* | `sf` |
| **BL-032** | Two non-xfailed tests hardcode the check count (7 and 6). A single-group candidate table breaks them outright, red rather than xfail | `sf` |
| WI-011 / BL-028 | `sentinelhub`, `cdsapi`, `rasterio`, `xarray` absent; no venv. Blocks BL-007, BL-012, BL-014, and BL-008 in practice. **Highest leverage item on the board** — four installs turn 35 rows into ~65,000 | user |
| WI-012 / BL-027 | Station coordinates, blocked on real GPS from SNIA | `sf` |
| WI-008 | ADR 0003, the map library, unanswered. Gates the frontend pass | `lq` |

BL-033 (declare overlapping-pair non-independence — 18 of 35 dates are both a
target and a feature anchor) and BL-034 (make MI-3 executable) are recorded but
do not block.

## Next Exact Action

**Fix BL-029, BL-030, BL-031 and BL-032 first, in that order.** All four are
corrections to the gate and its baselines, none is large, and all four are
prerequisites for judging any retrain honestly. Two of them currently cause a
*false pass*, which is worse than a failure.

Then implement WI-005 per ADR-sf-0008:

- a new `lake_anomaly.py` module under `src/features/` — pure pandas/numpy, **no `sentinelhub`
  import**, so it is importable and testable on a machine without BL-028;
  parameterised on a spatial-unit column so ADR 0004 D3 substitutes `pixel_id`
  rather than requiring a rewrite;
- one row per honest pair, no forward-fill, `fai_now` / `fai_future` kept in raw
  FAI units so `persistence_mae` stays comparable to the recorded evidence;
- causal rolling baseline from observations **strictly before** `t` — the review
  flagged that including `fai[t]` in its own baseline damps the anomaly it is
  meant to measure, and that a one-point window makes `sigma` `NaN`, so a minimum
  prior-observation count is required and pairs that miss it are dropped;
- Ridge or similar, not GradientBoosting, on 35 rows. Note that `z_pred = 0`
  reproduces climatology exactly, so a shrinkage model beats persistence almost
  by construction — report against both baselines or the result means nothing;
- `mae_fai` with its CV spread as the headline; precision, recall, F1 and AUC
  `null` with a recorded reason until the threshold is recalibrated;
- honest artifacts in a **new** directory. Do not overwrite
  `src/model/artifacts/` — the backend loads it at import, and its serving path is
  per-station, so a lake-wide model cannot fill four station cards. Rewiring is
  not WI-005.

Do not write new assertions to suit the new model. Point the existing gate at the
candidate table:

```bash
ALGAEWATCH_DATASET=data/processed/lake_anomaly_dataset.csv python -m pytest tests/test_model_integrity.py
```

Expect `test_station_points_are_on_the_lake` to keep xfailing — it is BL-027's and
waits on SNIA. Expect the classification checks to keep xfailing while the
threshold is uncalibrated. That is an honest outcome, not a failure to fix.

## Verification

All four run from the repository root and need no credentials:

```bash
python -m pytest -q                              # 36 passed, 7 xfailed
python agents/harness_doctor.py --root . --strict # 0 blockers, 0 warnings
python agents/check_translations.py               # 5 of 5 current
git diff --stat main...develop -- data/           # empty: data tables unchanged
```

## Resuming

`develop` is checked out in worktree
`H:/worktreesclaude/algaewatch-villarrica/algaewatch-villarrica-agents-621d84`.
Detach or remove it before switching `develop` elsewhere. From a fresh session:

```bash
git -C H:/algaewatch-villarrica fetch origin
git -C H:/algaewatch-villarrica switch develop
```

**Then build the local half for that machine** — `agents/LOCAL_SETUP.md`,
GATE-LOCAL. `agents/local/` does not travel, so a fresh checkout arrives without
it and `harness_doctor.py --strict` reports a hard blocker until it exists. Write
a fresh scan; do not copy another worktree's. Copying is how the previous scan
came to list "PyTorch absent" in its downgrade table two rows below its own record
of a working CUDA install.

Work lands on `develop` (confirmed with the user this session, over the global
`git-workflow` skill's preference for a prefixed branch). A tool-generated
`claude/...` branch is renamed before it is pushed — `agents/execution/WORKFLOW.md`.

## Translation Status

English only, deliberately. ADR-sf-0006 scopes Spanish siblings to the entry
documents — `AGENTS.md`, `agents/README.md`, `RUN_STATE.md`, `LOCAL_SETUP.md`,
`HANDOFF.md`. A session handoff is not an entry document. `RUN_STATE.es.md` is
current and carries the same status in Spanish.

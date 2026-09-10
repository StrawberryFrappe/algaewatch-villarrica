# Handoff: WI-004 complete, WI-005 next

Written 2026-09-10 by `sf`, at the end of the session that delivered WI-004.
Distinct from `agents/execution/HANDOFF.md`, which is the one-time handback of
the repository to `lq`. This one is for whoever picks the work up next —
including a later session of `sf`'s own agent.

Read `AGENTS.md` and `agents/RUN_STATE.md` first; this file assumes them.

## Current State

Branch **`develop`** at `23b30ca`, pushed to `origin/develop`. Four commits
ahead of `main`, which is untouched at `912376c`.

```
23b30ca docs(harness): record WI-004, the station-provenance defect, and cleared blockers
c49c9a5 fix(model): score baselines on the model's own partition (review findings)
874befc feat(model): report baselines beside every metric (rule MI-1)
85c95d2 feat(model): make baselines and integrity checks re-runnable (BL-002)
```

This is the first session in which application code changed since the fork.
`src/features/`, `backend/`, `frontend/`, `scripts/` and `data/` are still as the
original author left them; what moved is `src/model/`.

## Completed

**WI-004 / BL-002 — the baselines and integrity checks are permanent.**

- `src/model/baselines.py` — persistence, an honestly-fitted trivial rule, one
  chronological splitter with a horizon-length embargo, and `split_from_frames`
  for callers that already hold their partition.
- `src/model/integrity.py` — seven GATE-MODEL checks, each returning measured
  numbers rather than a bare boolean.
- `tests/` — 36 passed, 7 xfailed. The xfails are the gate.
- `src/model/train.py` — records `baselines` and `beats_baselines` in
  `metrics.json`, both `false`. Artifacts regenerated.

**Three things found along the way that were not on anyone's list.**

1. **GATE-LOCAL was never actually cleared.** The previous `RUN_STATE.md` said
   `agents/local/CAPABILITIES.md` existed; it did not, in either tree. Written
   now. See the second note in `agents/validation/DOCTOR.md`.
2. **Two of four station coordinates are not on the lake** — pucon 0.77 km, sur
   0.98 km from the nearest water pixel, sur outside the lake's southern extent
   entirely. Their FAI is shoreline vegetation, which is why the "bloom" label is
   close to "is this station sur or pucon". EV-014, ADR-sf-0007, BL-027.
3. **The `.env` was inside the repository root**, protected only by a gitignore
   line. Moved to `H:\.env`. Nothing had leaked — it was untracked and EV-006
   still holds — but PR-2 asks for structural protection and now has it.

**Two blockers turned out to be stale and are cleared.** CDSE credentials
authenticate (EV-015, WI-002). PyTorch is installed with working CUDA on a GTX
1650 (EV-017, WI-010).

## Verification

All four run from the repository root and need no credentials:

```bash
python -m pytest -q                              # 36 passed, 7 xfailed
python agents/harness_doctor.py --root . --strict # 0 blockers, 0 warnings
python agents/check_translations.py               # 5 of 5 current
git diff --stat main...develop -- data/processed/ # empty: data tables unchanged
```

## Blockers

| ID | What | Who |
|---|---|---|
| WI-011 / BL-028 | `sentinelhub`, `cdsapi`, `rasterio`, `xarray` absent; no venv. Working credentials do **not** mean a runnable pipeline. Blocks BL-007, BL-012, BL-014, and BL-008 in practice | user |
| WI-012 / BL-027 | Station coordinates, blocked on real GPS from SNIA. Until then ADR-sf-0007 disqualifies station-point FAI as a training signal | `sf` |
| WI-008 | ADR 0003, the map library, unanswered. Gates the frontend pass | `lq` |

## What The Backlog Expects Next

Ordered by what actually unblocks what, not by ID.

**Immediately doable, no dependencies:**

- **WI-005 / BL-003 to BL-006** — the honest retrain. Continuous target,
  local-baseline anomaly, real observation pairs only, chronological splits with
  an embargo. This is the next action.
- **BL-011** — correct the root `README.md` claims that overstate what runs on
  real data. Cheap, and it is currently the most misleading document in the repo.
- **BL-018** — drop `xgboost` from `requirements.txt`; nothing uses it.

**Unblocked by one install (WI-011):**

- **BL-007** — backfill the FAI grid across all 56 pass dates. Prerequisite for
  the per-pixel model, and the thing that makes ADR 0004 D3 real.
- **BL-012** — ERA5-Land backfill; the only available source of change-drivers.
- **BL-014** — extend Sentinel-2 history beyond one year.

**Then:**

- **BL-008** — per-pixel PyTorch model, three quantile heads, pinball loss.
  Framework is now present; it needs BL-007's data.

**`lq`'s half, gated on ADR 0003:** BL-009 palette, BL-010 overlay clipping,
BL-013 staleness disclosure, BL-019 the TRL-2 seal, BL-021 visual excess, and the
new **BL-026** — surface the baselines in the Modelo view. `metrics.json` carries
them now, but `backend/app/routers/model_metrics.py` builds a fixed response that
drops them, so GATE-PQ's "no displayed metric without its baseline" is still
failing on screen.

## Next Exact Action

Start WI-005. Success is already defined: the seven `xfail(strict=True)` marks in
`tests/test_model_integrity.py` name the backlog item that fixes each check, and
when a fix lands pytest reports XPASS as a **failure**, so the mark must come off
in the same change. Do not write new assertions to suit the new model — point the
existing gate at the candidate table:

```bash
ALGAEWATCH_DATASET=data/processed/candidate.csv python -m pytest tests/test_model_integrity.py
```

Read WI-005's phrase "on station data" against ADR-sf-0007. The target, pairing
and split fixes are all still correct and worth making. None of them can make
four placeholder coordinates measure the lake, so do not expect
`test_station_points_are_on_the_lake` to flip — it is BL-027's, and BL-027 waits
on SNIA.

## Resuming

`develop` is checked out in no worktree — this session's worktree was detached
before handing over, so the branch is free. From a fresh session:

```bash
git -C H:/algaewatch-villarrica fetch origin
git -C H:/algaewatch-villarrica switch develop
```

Or in a new worktree:

```bash
git -C H:/algaewatch-villarrica worktree add H:/worktreesclaude/algaewatch-villarrica/<name> develop
```

Then build the local half for that machine — `agents/LOCAL_SETUP.md`, GATE-LOCAL —
before implementation work. It is uncommitted by design and does not travel.

Branch naming is now written down in `agents/execution/WORKFLOW.md`: work lands
on `develop`, and a tool-generated `claude/...` branch is renamed before it is
pushed. It was not written down before this session, which is how one reached the
remote under its generated name.

## Translation Status

English only, deliberately. ADR-sf-0006 scopes Spanish siblings to the entry
documents — `AGENTS.md`, `agents/README.md`, `RUN_STATE.md`, `LOCAL_SETUP.md`,
`HANDOFF.md`. A session handoff is not an entry document. `RUN_STATE.es.md` is
current and carries the same status in Spanish.

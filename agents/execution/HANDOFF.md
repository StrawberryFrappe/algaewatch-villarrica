# Handoff

Written 2026-09-09, at the end of the harness mounting session.

## Current State

The harness is mounted and `harness_doctor.py` passes with zero hard blockers and
zero warnings, including under `--strict`. Implementation has **not** started and
is blocked at the kernel's mandatory acceptance gate.

**No application code has been modified.** The only changes to the repository are
the new `AGENTS.md` and the new `agents/` tree. Everything under `src/`,
`backend/`, `frontend/`, `scripts/` and `data/` is exactly as the original author
left it at commit `4b37bea`.

Git remotes were rewired: `origin` now points at the owner's fork
(`StrawberryFrappe/algaewatch-villarrica`), `upstream` at the original repository
(`Luchosqi/algaewatch-villarrica`). Local `main` tracks `origin/main`. Both are at
`4b37bea`, so history and authorship are preserved.

## What Was Done

1. **Audited the modelling layer.** Six defects established, all reproducible
   from committed CSVs. Recorded in `agents/intake/PROJECT_BRIEF.md`, with
   reproduction commands in `agents/validation/EVIDENCE_INDEX.md`.
2. **Cloned the harness kernel** from the private `agent-harness-kernel`
   repository, branch `testing`, commit `a5f428d`, through the existing git
   credential helper. Confirmed byte-identical to the copies installed in two
   other local projects.
3. **Wired the fork** and verified history and authorship survived.
4. **Grilled the owner** on four decisions, recorded in
   `agents/intake/QUESTIONS_SUMMARY.md` and promoted into ADRs 0002 to 0004.
5. **Preserved existing project rules.** The repository had no `AGENTS.md` or
   `CLAUDE.md`, but the root `README.md` carried implicit rules. These were fused
   into `AGENTS.md` as PR-1 to PR-4 rather than discarded.
6. **Added project-specific model integrity rules** MI-1 to MI-3 and a
   `GATE-MODEL` gate, encoding the defects the audit found so they cannot
   silently return.
7. **Mounted the harness** and ran the doctor.
8. **Delegated the mount review to a subagent**, per the kernel's review
   protocol. It returned **HOLD** on a P0 and three P1 findings — including a
   completion claim in `RUN_STATE.md` pointing at a review document that did not
   yet exist, and two harness claims about current code state that were simply
   false. All eleven findings were verified against source and resolved; the
   review now reads APPROVE WITH FIXES.

## What Was Verified

| Claim | How |
|---|---|
| Every audit figure | Re-executed the reproduction scripts on 2026-09-09; all reproduce exactly |
| Harness structural integrity | `harness_doctor.py --strict`: 0 blockers, 0 warnings |
| Kernel provenance | Clone at `a5f428d`, diffed byte-identical against two installed copies |
| Fork integrity | `git ls-remote` confirms `4b37bea` on the fork, matching upstream |
| Credential hygiene | No secrets tracked, none in git history |
| Satellite pipeline correctness | FAI formula matches Hu (2009); SCL water masking correct; rasters co-registered by fixed bbox and resolution |
| Independent review findings | Each re-checked against source rather than accepted on the reviewer's word: the staleness indicator in `Header.jsx`, the unreachable TRL-2 seal in `model_metrics.py`, the 218-reading count, the line count, and the 4-stop palette in `risk.js` |

## What Was Not Done

- No application code changed. No model retrained. No data collected.
- No test suite exists yet. GATE-TEST cannot pass until BL-002 lands.
- No frontend verification, no screenshots. GATE-PQ has not been exercised.
- Architecture documents (C4, 4+1, SRS) were deliberately not mounted, to avoid
  shipping placeholder-only files. Recorded as a P2 open question.
- ERA5-Land was not backfilled. This is deliberate: it is the most commonly
  assumed next step but cannot be completed and validated before the pitch.

## Blockers

1. **User acceptance of the mounted harness.** Unconditional; nothing proceeds
   without it.
2. **WI-002 — Copernicus credentials.** Blocks BL-007 and BL-008, and therefore
   milestone M3, the per-pixel redesign. Does **not** block M2, the
   credential-free honest retrain, which is the guaranteed deliverable.
3. **WI-003 — the original author has not been notified** that the modelling
   layer is being rebuilt, nor consulted on the map library. ADR 0003 is held
   provisional until he responds, and frontend work should not begin before then.

## Harness Upgrade

This harness was mounted from `agent-harness-kernel` `testing` @ `a5f428d`. The
owner is actively revising that kernel, in part from findings this mount
produced — notably the doctor's inability to detect a completion claim pointing
at a document that does not exist.

**Before relying on this harness in a later session, check whether the kernel has
moved.** If it has, carry out BL-020 / WI-006:

```bash
git -C <kernel> fetch && git -C <kernel> log --oneline a5f428d..origin/testing
```

Then diff-merge the template against the mounted tree rather than overwriting it.
Project-specific content lives in `AGENTS.md` (rules PR-1 to PR-4, MI-1 to MI-3)
and across intake, planning and validation; a blind re-copy would destroy it.
Four files are byte-identical to the kernel by design and can be re-copied
freely: `agents/README.md`, `agents/execution/WORKFLOW.md`,
`agents/execution/REVIEW_PROTOCOL.md`, `agents/execution/LOGBOOK_POLICY.md`.

Record the new kernel commit in `RUN_STATE.md` and re-run the doctor afterwards.

## Owner-Held Items And Their Timings

Committed by the owner on 2026-09-09:

| Item | Owner action | Expected |
|---|---|---|
| WI-003 | Notify the original author; raise the map-library question | ~8 hours |
| WI-002 | Obtain Copernicus credentials; development starts | ~11 hours |

WI-003 lands before WI-002, so ADR 0003 should be settled before frontend work
begins. Until WI-002 clears, only the credential-free track (M2) is available,
and that track is the guaranteed deliverable regardless.

## Next Exact Action

Obtain the owner's explicit acceptance of the mounted harness.

On acceptance, begin **WI-004 / BL-002**: convert the persistence and
trivial-rule baselines from ad-hoc audit scripts into permanent, re-runnable
checks. This is sequenced before any retraining so the new model is measured
against them from its first run rather than compared retrospectively.

Do **not** begin with the retrain, the per-pixel work, or the frontend. The
baselines come first; that ordering is the point.

## Context A Future Session Will Not Recover On Its Own

- The pitch is roughly 2026-09-10 (ASM-001). Confirm before planning around it.
- The reported metrics in `src/model/artifacts/metrics.json` are **not**
  performance. They came from a leaking pipeline and lose to trivial baselines.
  The file is retained for provenance only.
- The four monitoring stations have **placeholder** coordinates. They carry no
  scientific meaning. One originally fell on dry land.
- `data/processed/training_dataset.csv` must never train a shipped model. It is
  retained as evidence of the audited defect.
- The satellite ingestion layer passed audit. Resist rewriting it alongside the
  model layer.
- A green `harness_doctor.py` run is a structural check, not a truth check. It
  reported zero blockers while `RUN_STATE.md` asserted a review that did not
  exist. Do not treat a clean run as evidence that a document's claims are true.
- Any figure quoted in a harness document must carry a reproduction command in
  `EVIDENCE_INDEX.md`. Every figure that had one stayed accurate; both figures
  that lacked one had drifted by the time they were reviewed.
- The project runs with zero credentials against committed data. Protect that.

## Required Reads For Next Agent

1. `AGENTS.md`
2. `agents/RUN_STATE.md`
3. Relevant local logbook notes from `agents/local/logbook/YYYYMMDD/`, if
   available
4. Latest relevant review under `agents/reviews/`
5. Current backlog/work item files

Project-specific, read before touching anything under `src/model/`:

6. `agents/adrs/0004-per-pixel-anomaly-redesign.md` — what is being rebuilt and why
7. `agents/validation/EVIDENCE_INDEX.md` — the numbers, and how to reproduce them
8. `agents/validation/TEST_STRATEGY.md` — the six model integrity checks

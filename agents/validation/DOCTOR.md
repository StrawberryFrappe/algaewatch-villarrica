# Doctor Workflow

Doctor is a harness coherence check, not a product runtime.

## Hard Blockers

- Root `AGENTS.md` does not point to `agents/`.
- `agents/RUN_STATE.md` does not show the current phase.
- Implementation is marked ready before harness review and user acceptance.
- Existing project rules were overwritten or ignored without a recorded
  decision.
- Major stack/product/deployment decisions are undocumented.
- Local/raw memory is not gitignored.
- Validation gates do not identify evidence.

## Warnings

- Placeholder sections remain.
- ADRs are missing for medium-impact decisions.
- Review index is stale.
- Traceability is sparse.
- Deployment target is deferred.
- Subagents are unavailable, reducing review strength.

## Doctor Record

| Date | Result | Hard Blockers | Warnings | Next Action |
|---|---|---|---|---|
| 2026-09-09 | fail | 2 | 0 | First run during mounting, before `DOCTOR.md` and `reviews_index.md` existed. Both written; re-run |
| 2026-09-09 | pass | 0 | 0 | Structural pass, but see the note below: the script did not catch the P0 the independent review found |
| 2026-09-09 | pass | 0 | 0 | After resolving all eleven review findings. Present the mounted harness for user acceptance |

### Script Limitation Observed

The 2026-09-09 mount review found a P0 that `harness_doctor.py` reported as
clean: `RUN_STATE.md` asserted the harness review was complete while the review
file it pointed at did not exist. The script's dated-review check requires only
that *some* markdown file exist in a `YYYYMMDD/` folder, and `capability_scan.md`
satisfied that vacuously.

A green doctor run is a structural check, not a truth check. It does not verify
that a document's claims match reality, and it must not be treated as evidence
that they do.

## Manual Blocker Review

The script checks structure. The blocker list above is judgement, and was
assessed by hand on 2026-09-09:

| Blocker | Status |
|---|---|
| Root `AGENTS.md` points to `agents/` | Satisfied — required read order and core rules present |
| `RUN_STATE.md` shows current phase | Satisfied — "Harness mounted; awaiting user acceptance" |
| Implementation marked ready prematurely | Not applicable — implementation explicitly blocked, no application code touched |
| Existing rules overwritten | Not applicable — no `AGENTS.md` or `CLAUDE.md` existed. Rules implicit in the README were preserved as PR-1 to PR-4 rather than discarded |
| Major decisions undocumented | Satisfied — stack in ADR 0002, map library in ADR 0003, modelling redesign in ADR 0004, deployment posture in `PROJECT_PROFILE.md` |
| Local memory not gitignored | Satisfied — `agents/.gitignore` excludes `local/**`; `agents/local/.gitignore` excludes everything but itself |
| Gates do not identify evidence | Satisfied — every gate in `GATES.md` names its evidence, and `EVIDENCE_INDEX.md` carries runnable reproduction commands |

## Known Warnings Carried Forward

These are accepted rather than resolved, and are tracked elsewhere:

- Deployment target deferred — deliberate, GATE-DEPLOY inactive.
- No test surface yet — GATE-TEST cannot pass until BL-002 lands.
- No frontend verification or screenshot evidence — GATE-PQ not yet exercised.
- Architecture documents (C4, 4+1, SRS) not mounted, to avoid shipping
  placeholder-only files. Recorded as a P2 open question.
- Four mounted files are byte-identical to the kernel template by design:
  `agents/README.md`, `agents/execution/WORKFLOW.md`,
  `agents/execution/REVIEW_PROTOCOL.md`, and
  `agents/execution/LOGBOOK_POLICY.md`. These describe generic agent process
  rather than anything project-specific, and adapting them would have added
  wording without adding meaning. Project-specific content lives in `AGENTS.md`
  (rules PR-1 to PR-4, MI-1 to MI-3) and in the intake, planning and validation
  documents. Recorded here so the identity is a decision rather than an oversight.

## Script Policy

Use the kernel's `scripts/harness_doctor.py` after mounting to automate
missing-file, placeholder, stale-path, and contradiction checks. The workflow
remains authoritative; the script is a guardrail against theatrical completion.

Invocation used for this project:

```bash
python <kernel>/scripts/harness_doctor.py --root .
```

Add `--strict` to promote placeholder markers from warnings to hard blockers.

# Run State

## Current Phase

Harness mounted; awaiting user acceptance.

## Status

- Kernel cloned from `agent-harness-kernel`, branch `testing`, commit `a5f428d`.
- Project inspection complete. A full audit of the modelling layer was performed
  on 2026-09-09; findings are recorded in `agents/intake/PROJECT_BRIEF.md` and
  are reproducible via `agents/validation/EVIDENCE_INDEX.md`.
- User grill complete. Four decisions accepted, recorded in
  `agents/intake/QUESTIONS_SUMMARY.md` and promoted into ADRs 0002 to 0004.
- Existing project rules preserved and fused into `AGENTS.md` as PR-1 to PR-4.
- Capability scan complete, including recorded downgrades.
- Harness mount review complete, delegated to an independent subagent. Its
  original verdict was HOLD, on a P0 and three P1 findings; all eleven findings
  are resolved and the review now reads APPROVE WITH FIXES. See
  `agents/reviews/20260909/harness_mount_review.md`.
- Implementation is blocked until the user accepts the mounted harness.

## Next Action

Present the mounted harness for explicit user acceptance.

On acceptance, the first work item is WI-004: make the persistence and
trivial-rule baselines permanent, re-runnable checks, before any retraining
begins.

## Blockers

- User has not accepted the mounted harness. This gate is unconditional.
- WI-002: Copernicus Data Space Ecosystem credentials are not yet available.
  This blocks BL-007 and BL-008 and therefore milestone M3. It does **not** block
  M2, the credential-free honest retrain, which is the guaranteed deliverable.
- WI-003: the original author has not yet been notified that the modelling layer
  is being rebuilt, and has not been consulted on the map-library question.
  ADR 0003 is held provisional until he responds.

## Last Verified State

- `scripts/harness_doctor.py` run recorded in `agents/validation/DOCTOR.md`.
- Independent review findings re-verified against source on 2026-09-09: the
  staleness indicator in `Header.jsx`, the unreachable TRL-2 seal in
  `model_metrics.py`, the 218 real-reading count, the line count, and the
  4-stop risk palette in `risk.js` were each checked directly rather than
  accepted on the reviewer's word.
- No project validation has been run: there is no test suite yet (BL-002).
- No frontend verification has been performed; no screenshot evidence exists.
- Audit figures verified by re-execution on 2026-09-09; all reproduce.
- Git remotes verified: `origin` is the owner's fork, `upstream` the original
  repository, both at `4b37bea` with history and authorship intact.

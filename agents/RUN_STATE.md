# Run State

## Current Phase

Harness upgraded to kernel `5dee2cf` and split for two contributors; awaiting
user acceptance.

## Status

- Kernel upgraded from `agent-harness-kernel` `testing` @ `a5f428d` to `5dee2cf`
  by diff-merge, not re-mount. No kernel backup is kept in the repository
  (ADR 0001); the next upgrade re-clones and diffs from `5dee2cf`.
- Harness tooling now lives **inside** the harness: `agents/harness_doctor.py`
  (vendored from the kernel) and `agents/check_translations.py`
  (project-specific). Copying `agents/` into another repository carries its own
  checks.
- Local half mounted. `agents/local/CAPABILITIES.md` exists and is gitignored,
  clearing GATE-LOCAL. Capability scans are now per contributor.
- Two contributors as of 2026-09-09: `sf` (owner) and `lq` (Luchosqi, original
  author). Author slugs adopted, work split agreed, repository being handed back.
  See ADR-sf-0005.
- Two working languages. English canonical, Spanish siblings for entry
  documents, GATE-I18N active. See ADR-sf-0006.
- Project inspection and the full modelling audit remain as recorded on
  2026-09-09 in `agents/intake/PROJECT_BRIEF.md`, reproducible via
  `agents/validation/EVIDENCE_INDEX.md`.
- Existing project rules preserved and fused into `AGENTS.md` as PR-1 to PR-4.
- Implementation of application code is blocked until the user accepts.

## Next Action

Present the upgraded harness for explicit user acceptance.

On acceptance:

- `sf` begins **WI-004** — make the persistence and trivial-rule baselines
  permanent, re-runnable checks, before any retraining. The ordering is the
  point: the new model is then measured against them from its first run rather
  than compared retrospectively and flattered.
- `lq` receives `agents/execution/HANDOFF.md`, builds his local half, and settles
  ADR 0003 before frontend work begins.

## Blockers

- User has not accepted the upgraded harness. This gate is unconditional.
- **WI-002** — Copernicus Data Space Ecosystem credentials are not yet
  available. Blocks BL-007 and BL-008, therefore milestone M3. Does **not** block
  M2, the credential-free honest retrain, which is the guaranteed deliverable.
- **PyTorch is not installed** on the owner's machine, found during the
  2026-09-09 local capability scan. ADR 0002 makes it binding from the supervisor
  (SRC-003) and BL-008 requires it, so this blocks BL-008 independently of the
  credentials. M2 is unaffected — it deliberately stays scikit-learn. Recorded as
  a P1 open question.
- **ADR 0003** (map library) is `lq`'s to settle and he has not yet answered.
  Frontend work should not begin before he does.

## Last Verified State

- `python agents/harness_doctor.py --root . --strict` — recorded in
  `agents/validation/DOCTOR.md`.
- `python agents/check_translations.py` — recorded in the same place.
- Kernel delta reviewed commit by commit: `798f1b3` (doctor follows citations),
  `fd122ff` (shared/local split, slugs), `e22f283` (translation protocol),
  `5dee2cf` (line-ending caveat). The new doctor's referential-integrity check
  caught two live dangling citations in this harness and two more introduced
  during the upgrade itself.
- Independent review findings from the 2026-09-09 mount review re-verified
  against source: the staleness indicator in `Header.jsx`, the unreachable TRL-2
  seal in `model_metrics.py`, the 218 real-reading count, the line count, and the
  4-stop risk palette in `risk.js` were each checked directly rather than
  accepted on the reviewer's word.
- Audit figures verified by re-execution on 2026-09-09; all reproduce.
- No project validation has been run: there is no test suite yet (BL-002).
- No frontend verification has been performed; no screenshot evidence exists.
- Git remotes verified: `origin` is the owner's fork, `upstream` the original
  repository, with history and authorship intact.
- **No application code has been modified.** `src/`, `backend/`, `frontend/`,
  `data/` and the collection scripts are as the original author left them.

# Reviews Index

Use this index to highlight important reviews without flattening dated review
folders.

| Date | Review | Verdict | Why It Matters |
|---|---|---|---|
| 2026-09-09 | Capability scan | Recorded | Establishes what this platform can actually do, and records four downgrades — notably no `gh` CLI and no test runner |
| 2026-09-09 | Harness mount review | APPROVE WITH FIXES (originally HOLD) | Independent subagent review. Found a P0 — a completion claim pointing at a review document that did not yet exist — plus two false claims about current code state. All eleven findings resolved. Established the rule that any figure quoted in a harness document must carry a reproduction command |
| 2026-09-09 | Harness upgrade review (`sf`) | See the document | Independent subagent review of the `a5f428d` → `5dee2cf` upgrade, the two-contributor split, and the i18n mount. Reviewed before the repository is handed to a second person, which is the point at which a wrong harness claim stops being self-inflicted |
| 2026-09-10 | Implementation review — WI-004 (`sf`) | APPROVE WITH FIXES | First review of application code. Found that the baselines were scored on a partition rebuilt by a non-stable sort, so they could differ from the model's own holdout and happened not to. Also caught a check that passed vacuously on an empty table. Both are the same class of bug the suite exists to catch: a gate that reports success without having tested anything |

## A Note On The Capability Scan

The 2026-09-09 capability scan above is a record of **one machine on one day**.
Since kernel `5dee2cf` (ADR-sf-0005), capability scans are per contributor and
live uncommitted at `agents/local/CAPABILITIES.md`.

Do not read that dated scan as a claim about the current environment. It asserts
subagents, worktrees and a working credential helper; an agent on another machine
believing it would plan delegated reviews it may be unable to run, and report
them as done.

## Review Types

- Harness mount review
- Capability scan
- Maturity review
- Plan review
- Implementation review
- Adversarial review
- Final review

## Rules

- Store detailed reviews under `agents/reviews/YYYYMMDD/`.
- Keep this index short and high-signal.
- A blocking review finding must appear in `agents/RUN_STATE.md`.

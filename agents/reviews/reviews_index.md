# Reviews Index

Use this index to highlight important reviews without flattening dated review
folders.

| Date | Review | Verdict | Why It Matters |
|---|---|---|---|
| 2026-09-09 | Capability scan | Recorded | Establishes what this platform can actually do, and records four downgrades — notably no `gh` CLI and no test runner |
| 2026-09-09 | Harness mount review | APPROVE WITH FIXES (originally HOLD) | Independent subagent review. Found a P0 — a completion claim pointing at a review document that did not yet exist — plus two false claims about current code state. All eleven findings resolved. Established the rule that any figure quoted in a harness document must carry a reproduction command |

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

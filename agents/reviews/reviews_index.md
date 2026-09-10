# Reviews Index

Use this index to highlight important reviews without flattening dated review
folders.

| Date | Review | Verdict | Why It Matters |
|---|---|---|---|
| 2026-09-09 | Capability scan | Recorded | Establishes what this platform can actually do, and records four downgrades — notably no `gh` CLI and no test runner |
| 2026-09-09 | Harness mount review | APPROVE WITH FIXES (originally HOLD) | Independent subagent review. Found a P0 — a completion claim pointing at a review document that did not yet exist — plus two false claims about current code state. All eleven findings resolved. Established the rule that any figure quoted in a harness document must carry a reproduction command |
| 2026-09-09 | Harness upgrade review (`sf`) | See the document | Independent subagent review of the `a5f428d` → `5dee2cf` upgrade, the two-contributor split, and the i18n mount. Reviewed before the repository is handed to a second person, which is the point at which a wrong harness claim stops being self-inflicted |
| 2026-09-10 | Frontend credibility pass (`lq`) | Done, GATE-PQ evidence attached | WI-009 / BL-009, BL-010, BL-013, BL-019, BL-021. Risk palette moved to a CVD-validated magma ramp; risk overlay clipped to the lake; staleness disclosed on slider/map/cards/popup; mandated TRL-2 seal rendered; generated-default glass and halos cut. Handoff deviations in ADR-lq-0007. Screenshots of the running app on real data |
| 2026-09-10 | Light-theme pass (`lq`) | Done, focused pass | WI-011. Owner redirect: light pastel theme, topbar nav, centred `max-width` container with adaptive gutters, no neon / no glass. Light-mode risk ramp re-validated (CVD worst ΔE 8.5). Wholesale visual deviation from the handoff — ADR-lq-0008. Not done: real logo asset, sub-768px QA, per-view re-architecture |

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

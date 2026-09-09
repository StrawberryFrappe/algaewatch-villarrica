# Questions Summary

This file preserves accepted answers in digestible form. Raw Q&A and personal
context should stay under `agents/local/` and remain gitignored unless promoted
into a durable project document.

## Answered Decisions

| Date | Topic | Accepted Answer | Promoted To |
|---|---|---|---|
| 2026-09-09 | Purpose of the work | Coursework deliverable and portfolio piece, both | `PROJECT_BRIEF.md`, GATE-PQ activation |
| 2026-09-09 | Modelling framework | PyTorch is a binding constraint from the supervisor | ADR 0002 |
| 2026-09-09 | Map library | Keep Leaflet, record the deviation, but keep Mapbox open as long as possible pending consultation with the original author | ADR 0003 (status: provisional) |
| 2026-09-09 | Portfolio Quality gate | Active | `PROJECT_PROFILE.md`, `GATES.md` |
| 2026-09-09 | Collaboration model | Undecided by design: proceed solo-first on the fork, keep it rebase-friendly against upstream | `PROJECT_PROFILE.md`, `REVIEW_PROTOCOL.md` |
| 2026-09-09 | Architectural change latitude | Broad change permitted; satellite ingestion layer preserved because it passed audit | `PROJECT_BRIEF.md` non-goals |
| 2026-09-09 | Deployment | Out of scope before the pitch; local evidence only | `PROJECT_PROFILE.md`, GATE-DEPLOY inactive |
| 2026-09-09 | Prediction target | Predict a continuous quantity and threshold downstream, rather than training on a binarised label | ADR 0004, rule MI-3 |
| 2026-09-09 | Training unit | Move from 4 placeholder stations to lake pixels | ADR 0004 |
| 2026-09-09 | Fork topology | `origin` is the owner's fork; the original author's repository retained as `upstream`; history and authorship preserved | `PROJECT_PROFILE.md` |
| 2026-09-09 | Harness kernel source | Cloned from the private `agent-harness-kernel` repository, branch `testing`, commit `a5f428d`, via the existing git credential helper | `agents/reviews/20260909/capability_scan.md` |

## Unanswered Questions

| Priority | Question | Why It Matters | Default If Deferred |
|---|---|---|---|
| P0 | Are Copernicus Data Space Ecosystem credentials obtainable before the pitch? | Gates the grid backfill across all 56 dates, and therefore the entire per-pixel redesign | Fall back to the credential-free track: fix labelling and validation on existing station data, and present the per-pixel design as the argued remedy rather than a built one |
| P1 | Does the original author accept the move away from his implementation? | Affects whether the fork stays mergeable upstream and how the pitch is framed jointly | Proceed solo-first; keep commits reviewable and the fork rebase-friendly |
| P1 | Is the map library decision final, or does Mapbox return? | ADR 0003 is deliberately provisional; a late reversal costs frontend hours | Leaflet stands. Revisit only if the original author objects before frontend work begins |
| P2 | Which architecture documents are wanted — C4, 4+1, SRS? | They were not mounted, to avoid shipping placeholder-only files | Omitted. Add on request when the redesign stabilises |
| P2 | Should ERA5-Land weather be backfilled before the pitch? | It is the only available source of change-drivers, which is why the model cannot currently beat persistence | Deferred. Recorded as the principal reason for the persistence failure rather than attempted under time pressure |
| P2 | Extend the Sentinel-2 history beyond one year, or add Sentinel-3 OLCI? | Both raise sample count and revisit frequency; Sentinel-3 is arguably the better-suited instrument | Roadmap only. Not attempted before the pitch |
| P3 | Which colourblind-safe ramp replaces the red/green risk scale? | GATE-PQ and accessibility both bear on it | Choose a perceptually uniform sequential ramp during the frontend pass |

## Grill Checklist

- Product goal and audience — asked and answered
- Existing code maturity — established by inspection and audit
- Source authority — recorded in `SOURCE_MANIFEST.md`, including four conflicts
- Stack and architecture — asked; PyTorch binding, map library provisional
- Data and persistence — established: committed CSVs plus model artifacts, no database
- Authentication and security — no auth surface; credential hygiene verified clean
- Deployment target — asked, deferred out of scope
- Test and evidence bar — set by GATE-TEST and rule MI-1
- User-facing quality expectations — GATE-PQ active at the owner's request
- Collaboration and handoff preferences — asked; solo-first, upstream-compatible

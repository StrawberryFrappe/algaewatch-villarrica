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
| 2026-09-09 | Collaboration model | ~~Undecided by design: proceed solo-first on the fork~~ **Superseded the same day.** Luchosqi joins as a contributor; the repository is handed back to him | ADR-sf-0005, `PROJECT_PROFILE.md` |
| 2026-09-09 | Architectural change latitude | Broad change permitted; satellite ingestion layer preserved because it passed audit | `PROJECT_BRIEF.md` non-goals |
| 2026-09-09 | Deployment | Out of scope before the pitch; local evidence only | `PROJECT_PROFILE.md`, GATE-DEPLOY inactive |
| 2026-09-09 | Prediction target | Predict a continuous quantity and threshold downstream, rather than training on a binarised label | ADR 0004, rule MI-3 |
| 2026-09-09 | Training unit | Move from 4 placeholder stations to lake pixels | ADR 0004 |
| 2026-09-09 | Fork topology | `origin` is the owner's fork; the original author's repository retained as `upstream`; history and authorship preserved | `PROJECT_PROFILE.md` |
| 2026-09-09 | Harness kernel source | Cloned from the private `agent-harness-kernel` repository, branch `testing`, commit `a5f428d`, via the existing git credential helper | `agents/reviews/20260909/capability_scan.md` |
| 2026-09-09 | Kernel upgrade | Diff-merge `a5f428d` → `5dee2cf`, not a re-mount. A blind re-copy would destroy the project content in `AGENTS.md`, `GATES.md` and the intake documents | `RUN_STATE.md`, `agents/reviews/20260909/harness_upgrade_review.sf.md` |
| 2026-09-09 | Harness tooling location | `harness_doctor.py` and `check_translations.py` live in `agents/`, not `scripts/`. A harness that cannot check itself without its kernel is not portable | ADR 0001 |
| 2026-09-09 | Kernel backup | None kept. Provenance recorded instead; the next upgrade re-clones. Avoids publishing the private kernel's template tree into a repository headed upstream | ADR 0001 |
| 2026-09-09 | Author slugs | `sf` (StrawberryFrappe), `lq` (Luchosqi). ADRs 0001–0004 keep bare numbers and belong to `sf` | ADR-sf-0005 |
| 2026-09-09 | Work split | `sf` keeps the model layer (WI-004, WI-005); `lq` takes the frontend (BL-009, BL-010, BL-013, BL-019, BL-021). Split by subsystem so the halves share no files | ADR-sf-0005, `WORK_ITEMS.md` |
| 2026-09-09 | Canonical language | English canonical, Spanish siblings for entry documents only. Spanish-canonical rejected on cost, not principle — revisit after the pitch | ADR-sf-0006 |
| 2026-09-09 | Line endings | Pinned to LF for `AGENTS.md` and `agents/**`, scoped to the harness so the handover commit does not renormalize `lq`'s own README files | ADR-sf-0006, `.gitattributes` |

## Unanswered Questions

| Priority | Question | Why It Matters | Default If Deferred |
|---|---|---|---|
| P0 | Are Copernicus Data Space Ecosystem credentials obtainable before the pitch? | Gates the grid backfill across all 56 dates, and therefore the entire per-pixel redesign | Fall back to the credential-free track: fix labelling and validation on existing station data, and present the per-pixel design as the argued remedy rather than a built one |
| P1 | Does the original author accept the move away from his implementation? | Affects whether the fork stays mergeable upstream and how the pitch is framed jointly | **Asked, awaiting answer.** `agents/execution/HANDOFF.md` puts it to him directly, with the findings and their reproduction commands so he can check them rather than take them on trust |
| P1 | Is the map library decision final, or does Mapbox return? | ADR 0003 is deliberately provisional; a late reversal costs frontend hours | **Now `lq`'s to settle** — the frontend half is his. Leaflet stands until he answers; frontend work should not start before then |
| P2 | Which architecture documents are wanted — C4, 4+1, SRS? | They were not mounted, to avoid shipping placeholder-only files | Omitted. Add on request when the redesign stabilises |
| P2 | Should ERA5-Land weather be backfilled before the pitch? | It is the only available source of change-drivers, which is why the model cannot currently beat persistence | Deferred. Recorded as the principal reason for the persistence failure rather than attempted under time pressure |
| P2 | Extend the Sentinel-2 history beyond one year, or add Sentinel-3 OLCI? | Both raise sample count and revisit frequency; Sentinel-3 is arguably the better-suited instrument | Roadmap only. Not attempted before the pitch |
| P3 | Which colourblind-safe ramp replaces the red/green risk scale? | GATE-PQ and accessibility both bear on it | `lq`'s call as part of BL-009. Any perceptually uniform sequential ramp qualifies; the constraint is that green/orange/red must not carry the signal alone |
| P1 | Is PyTorch going to be installed, and by whom? | ADR 0002 makes it binding from the supervisor (SRC-003) and BL-008 requires it. It is **not installed** on the owner's machine, found during the 2026-09-09 capability scan | Blocks BL-008 independently of the Copernicus credentials. Surface before planning M3, not during it. M2 is unaffected — it deliberately stays scikit-learn |

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
- Collaboration and handoff preferences — asked. Answered "solo-first,
  upstream-compatible" on 2026-09-09 and **superseded the same day**: Luchosqi
  joins, the repository is handed back, and the work is split. See ADR-sf-0005
  and the Answered Decisions table above

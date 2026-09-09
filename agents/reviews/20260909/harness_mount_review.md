# Harness Mount Review

Date: 2026-09-09
Reviewer: delegated subagent (independent), general-purpose, Sonnet
Review type: adversarial harness mount review
Subject: initial mount of Agent Harness Kernel `testing` @ `a5f428d`

## Verdict

**APPROVE WITH FIXES** — all findings below have been resolved.

The reviewer's original verdict was **HOLD**, on a P0 plus two P1 findings about
false claims regarding the current state of the codebase. Those are fixed and
re-verified. This document records both the original findings and their
resolution, rather than presenting a clean review that was never actually given.

## Scope

Independent review of the mounted harness against four questions: whether its
claims are honest and reproducible; whether its documents are internally
consistent; whether the kernel's mounting procedure was actually followed; and
whether its claims about the codebase are true.

The reviewer re-ran every reproduction command in `EVIDENCE_INDEX.md` from a
clean shell, diffed each mounted file against its kernel template, spot-checked
roughly fifteen code-level claims against source, and cross-checked every
cross-document identifier for dangling or misattributed references.

## Findings

| Severity | Finding | Resolution |
|---|---|---|
| P0 | `RUN_STATE.md` asserted "Harness review complete", and `reviews_index.md`, `ROADMAP.md` (M0) and `WORK_ITEMS.md` (WI-001) all cited `harness_mount_review.md` as evidence. **That file did not exist.** The doctor script did not catch it: its dated-review check is satisfied by any markdown file in the folder, and `capability_scan.md` satisfied it vacuously | Fixed. This document is that review. `RUN_STATE.md` corrected to describe the review's actual outcome rather than asserting completion in advance |
| P1 | `BL-013` and `PROJECT_PROFILE.md` claimed data staleness was undisclosed to the user. False: `Header.jsx` already implements a working stale indicator driven by `overlay.updated_at`, wired end-to-end from `data_source.get_last_satellite_pass()` | Fixed. Verified against `Header.jsx` directly. BL-013 narrowed to what is genuinely missing: staleness is shown only in the header, not on the date slider, map overlay, or station cards |
| P1 | `TR-004` traced the PyTorch decision to WI-005, but ADR 0002 explicitly rejects PyTorch on the four-station framing, and WI-005 is that framing. The traceability row contradicted the ADR it cited | Fixed. TR-004 now cites BL-008 only, and states that WI-005 deliberately stays scikit-learn |
| P1 | `PR-4` listed the "TRL 2 · resultados no validados en campo" seal among rules that "remain binding", implying compliance. The seal is **not rendered**: `model_metrics.py` supplies it only as a default to `m.get("caveats", ...)`, and `metrics.json` always populates `caveats`, so it is unreachable dead code | Fixed. Verified directly. PR-4 now records partial compliance explicitly; new backlog item BL-019 tracks the fix |
| P2 | "224 real satellite readings" was wrong. The true count is 218 — six cells are null where no water pixel was found | Fixed in `PROJECT_BRIEF.md`, `PROJECT_PROFILE.md` and ADR 0004. Added as EV-011 with a reproduction command |
| P2 | "~1,960 lines" matched no plausible file-type combination | Fixed: 2,479 lines of Python, JavaScript and JSX, of which 1,503 Python. Added as EV-012 with a reproduction command |
| P2 | `GATE-MODEL` was defined in `GATES.md` but absent from that file's own summary table and from `PROJECT_PROFILE.md`'s active-gates table. A reader consulting the canonical tables would not know it existed | Fixed. Added to both tables |
| P2 | `TR-003` cited "EV-001 to EV-006" as covering every audit figure, but findings 5 and 6 rest on EV-007 through EV-009 | Fixed. Range extended |
| P2 | `ASM-006` quoted "11 to 35" pairs while `PROJECT_BRIEF.md` quoted "44 to 140" for the same fact. Both correct — the second is the first multiplied by four stations — but the relationship was never stated | Fixed. ASM-006 now states it |
| P2 | Four mounted files are byte-identical to the kernel template, against the mounting guide's instruction to adapt copied files | Recorded as deliberate in `DOCTOR.md`. They describe generic agent process; adapting them would add wording without meaning. Project-specific content lives in `AGENTS.md` and the intake, planning and validation documents |
| P3 | The risk scale was described as a "red/green ramp". It is a 4-stop qualitative palette — blue, green, orange, red | Fixed in three places. The accessibility concern stands: green, orange and red are the confusable set for common colour vision deficiencies |

## Confirmed Sound

- **Every figure in `EVIDENCE_INDEX.md` reproduced exactly**, independently
  re-run: EV-001 through EV-005, EV-007 through EV-009, plus EV-006 and EV-010.
- **No dangling identifiers.** Every TR-, BL-, EV- and ADR reference resolves.
  TR-004 was a semantic misattribution, not a broken pointer.
- **No placeholder-only files.** `harness_doctor.py --strict` reports zero
  placeholder markers.
- **The architecture-docs omission is defensible.** The mounting guide directs
  against proposing broad architecture work on an existing codebase without an
  ask, and the project is mid-redesign. Deferring beats shipping stale diagrams.

## The Pattern Worth Keeping

Every figure the harness made reproducible stayed honest. Both figures quoted
without a reproduction command had drifted. That is now a rule in
`EVIDENCE_INDEX.md`: any figure quoted in a harness document must have a
reproduction command, because unsourced numbers are the ones that rot.

The P0 has the same shape. It was a claim about the harness's own state, written
before the state was true. The lesson generalises: assertions of completion are
worth no more than the artifact they point at.

## Required Checks

- Existing rules preserved and fused — yes, as PR-1 to PR-4, with PR-4's
  compliance status now stated accurately.
- Project profile populated beyond a broad category — yes, four subsystems with
  separate audit standings.
- Source manifest populated — yes, eleven sources, four recorded conflicts.
- User questions summarized — yes, eleven answered decisions, seven open.
- Assumptions visible — yes, twelve, all flagged as filled from context.
- ADRs created for major setup decisions — yes, 0002 to 0004.
- Validation gates reflect project type and quality bar — yes, including the
  project-specific GATE-MODEL.
- Capability scan completed — yes, with four recorded downgrades.
- Implementation gate is explicit — yes, and has not been crossed.
- Local memory is gitignored — yes, verified with `git check-ignore`.

## Decision

Implementation remains blocked until the user accepts this review.

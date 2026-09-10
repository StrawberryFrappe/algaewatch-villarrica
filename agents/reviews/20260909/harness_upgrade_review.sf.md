# Harness Upgrade Review

**Date:** 2026-09-09
**Reviewer:** independent subagent, delegated per `agents/execution/REVIEW_PROTOCOL.md`
**Minted by:** `sf`
**Scope:** kernel upgrade `a5f428d` → `5dee2cf`, the two-contributor mount, and
the i18n mount.

## Verdict

**APPROVE WITH FIXES.** Eight findings, all resolved. No P0.

Seven came from the delegated review. The eighth was found afterwards by
`agents/check_translations.py`, in its own filename matching — recorded here
rather than fixed silently, because a checker that mis-parses is worth more
attention than one that merely passes.

This review matters more than its severity suggests: the output is about to be
handed to a second person, which is the point at which a wrong harness claim
stops being self-inflicted.

## Method

Adversarial, and instructed to verify against files rather than accept prose —
the predecessor mount review returned HOLD on a P0 and found two harness claims
about code state that were simply false, and that standard was set as the bar.

The reviewer was given a clean kernel clone to diff against, and was told which
doctor blockers were expected (the three forward references to this document,
which did not yet exist) so that any *other* blocker would stand out as a real
finding.

## Findings

| Severity | Finding | Resolution |
|---|---|---|
| P1 | WI-006 and BL-020 were marked **done** citing this review file as evidence — a file that did not exist. That is the predecessor's P0 pattern recurring: a completion claim written ahead of the artifact it names, and it violates `WORK_ITEMS.md`'s own rule that nothing is done until verification evidence is recorded | Fixed. This document is that evidence, and it now exists. The doctor's referential-integrity check is what surfaced it, in the same session that vendored the doctor |
| P2 | Finding 3's headline figure — CV AUC 0.99 against temporal holdout AUC 0.90 — was quoted in `PROJECT_BRIEF.md` and `HANDOFF.md` with **no reproduction command** in `EVIDENCE_INDEX.md`. Every other cited figure had one. This is precisely the omission the index's own closing rule exists to prevent | Fixed. Added as **EV-013**, with the command and the reproduced values (0.9925 / 0.9003). `PROJECT_BRIEF.md` now cites EV-013 inline, and the handoff's range was widened to EV-001…EV-013 in both languages |
| P2 | `QUESTIONS_SUMMARY.md`'s Grill Checklist still read "solo-first, upstream-compatible", contradicting the Answered Decisions table 39 lines above it, which had struck that through as superseded the same day | Fixed. The checklist line now records both the original answer and its supersession, and points at ADR-sf-0005 |
| P2 | `HANDOFF.es.md` rendered "with no embargo" as "**sin embargo**", which a Spanish reader parses as "however" rather than "without an embargo period" — collapsing the finding into nonsense in the one document the second contributor is most likely to read. The glossary's `embargo → embargo` entry exists to prevent exactly this | Fixed: "sin ningún período de embargo entre medio". Verified the term is used correctly elsewhere (MI-2 in `AGENTS.es.md`), so this was a local construction bug, not a systemic glossary failure |
| P2 | `LOCAL_SETUP.es.md` rendered "and believe them" as "y **les** crea" — wrong object pronoun, which inverts the sentence | Fixed: "y que las crea", agreeing with feminine *instrucciones* and with the subjunctive *lea* that governs it |
| P3 | `ROADMAP.md`'s M4 outcome listed three of `lq`'s five assigned items, omitting BL-019 and BL-021, while WI-009 — which M4 maps to — listed all five | Fixed. M4 now names all five and cross-references WI-009 |
| P3 | `.gitattributes` is untracked, so its LF pin is not in effect for any other clone until it is committed alongside the now-normalized markdown | Accepted, not fixed. Nothing in this session is committed; the file lands with everything else. Noted here so the ordering is deliberate rather than lucky |
| P2 | **Found after the review, by the checker itself.** `agents/check_translations.py` matched `FOO.<lang>.md` as any two lowercase letters — so `harness_upgrade_review.sf.md`, the file naming *this review*, was parsed as a translation into the language "sf" and reported as missing frontmatter. Author slugs and ISO 639-1 codes are the same shape, and the two naming schemes collide | Fixed. The checker now matches against a declared `LANGUAGES` set rather than any letter pair. The underlying hazard — a contributor whose slug happens to be a real language code, `es` or `en` — is recorded as a rule in ADR-sf-0005 so slug selection avoids it rather than the checker papering over it |

## Confirmed Sound

Each item below was checked against the files, not accepted from a document.

- **Both checks pass.** `agents/harness_doctor.py --strict` reported only the
  three expected forward references to this document; `agents/check_translations.py`
  reported 5 of 5 current, 0 problems.
- **PR-1…PR-4 and MI-1…MI-3 preserved verbatim.** `git diff AGENTS.md` shows the
  hunk ending before the Preserved Project Rules section.
- **The code claims are true.** The 4-stop blue/green/orange/red palette is in
  `risk.js`; `Header.jsx` implements staleness via `overlayUpdatedAt` /
  `STALE_DAYS_THRESHOLD` while the stations, map and model views have no such
  logic; `model_metrics.py`'s `m.get("caveats", "TRL 2…")` default is confirmed
  unreachable because `metrics.json` always populates `caveats` with a different
  string.
- **The capability downgrades are real.** PyTorch raises `ModuleNotFoundError`;
  `gh` is absent from PATH. Both verified by execution, not assumption.
- **No application code modified.** `git status --porcelain` is confined to
  `agents/`, `AGENTS.md`, `AGENTS.es.md` and `.gitattributes`.
- **GATE-LOCAL and GATE-I18N appear in both canonical tables** — `GATES.md` and
  `PROJECT_PROFILE.md`. The predecessor's P2 (a gate defined but missing from the
  tables a reader consults) does not recur.
- **All six audit figures reproduced exactly** by independent re-execution:
  bloom rates sur 0.979 / pucon 0.501 / norte 0.000 / tolten 0.000; 1,356 rows,
  363 unique, 85.3% duplicated lags; seam date 2026-06-09; 90.0% present-reading
  match; EV-011's 218 readings; EV-012's 2,479 lines of which 1,503 Python.
- **The five translations** carry correct frontmatter, are current by hash, and —
  the two flagged sentences aside — are faithful, complete and glossary-compliant:
  FAI kept as an acronym, "relleno hacia adelante", "filtración" rather than
  "fuga", "antigüedad del dato" rather than "obsolescencia".
- **The line-ending mechanism was tested, not assumed.** Tracked files *outside*
  the pinned scope (`README.md`, `App.jsx`) do check out CRLF on this machine
  under `core.autocrlf=true`, while `git check-attr` confirms `eol=lf` is honored
  for every file the pattern covers. The pin is necessary and it works.
- **No stale claims that the doctor lives under the project's `scripts/`
  directory remain.** Every reference names `agents/harness_doctor.py`.
- **The handoff's tone is fair.** It frames the six findings explicitly as "not a
  verdict on you", ties each to a reproducible command, and the Spanish carries
  that framing intact.

## Scope Discipline

Harness-only, as stated. No application-code changes. The diff is the harness
tree, `AGENTS.md`, its Spanish sibling, and `.gitattributes`.

## The Pattern Worth Keeping

Both P1-or-worse findings across two reviews of this harness have the same shape:
**a claim written slightly ahead of the artifact it names.** The predecessor found
`RUN_STATE.md` asserting a review that did not exist. This one found WI-006 marked
done citing a review that did not exist.

The difference is that this time the doctor caught it, because kernel `798f1b3`
taught it to follow citations — a change written in response to the predecessor's
P0, on this very project. The check found four more instances during the upgrade
itself, including two of the reviewer's own forward references.

The rule generalises and is worth stating plainly: **write the artifact, then the
claim.** A citation is cheap to write and that is exactly why it outruns the
thing it points at.

## Required Checks

- Kernel delta reviewed commit by commit — yes, four commits.
- Existing rules preserved — yes, PR-1…PR-4 and MI-1…MI-3, verified by diff.
- Local half mounted and gitignored — yes, verified with `git check-ignore`.
- Gates reflect the project — yes, including GATE-LOCAL and GATE-I18N in both
  canonical tables.
- Translations current — yes, by hash, with a negative test confirming the
  checker actually fails when a source moves.
- Implementation gate not crossed — yes. No application code touched.
- Second contributor's needs met — yes: handoff in both languages, local-setup
  instructions, both checks runnable without kernel access.

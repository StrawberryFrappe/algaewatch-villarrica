# Validation Gates

## Required Gates

| Gate | Applies When | Pass Criteria | Evidence |
|---|---|---|---|
| GATE-HM Harness Mounted | Always | Harness accepted by user after review | Harness mount review |
| GATE-LOCAL Local Mount | Always | `agents/local/CAPABILITIES.md` exists and is current | The file itself |
| GATE-DR Doctor | Always | No unresolved hard blockers | `agents/validation/DOCTOR.md` |
| GATE-TEST Tests | Active — code project with a confirmed leakage history | Baseline-comparison checks run and pass; no training path consumes fabricated rows | Test output in `EVIDENCE_INDEX.md` |
| GATE-DEPLOY Deployment | Inactive — deployment out of scope | Not applicable before the pitch | Not applicable |
| GATE-PQ Portfolio Quality | Active — owner intends this as a portfolio piece | Visible output is credible, polished, and demonstrable | Screenshots / review |
| GATE-MODEL Model Integrity | Active — project-specific, added after the 2026-09-09 audit | Rules MI-1 to MI-3 and PR-3 all pass. Defined in full below | Baseline comparisons in `EVIDENCE_INDEX.md` |
| GATE-I18N Translation Currency | Active — two working languages, English canonical | Every translated file's `source_sha` matches the current hash of the canonical file it names | `python agents/check_translations.py` |

## Local Mount Gate

Implementation work requires the local half of the harness to exist. A harness
that does not know what its agent can do will either plan work the environment
cannot perform, or quietly downgrade a review to a single-agent pass without
saying so.

Because `agents/local/` never travels with the repository, every clone lands
without it and is forced through the setup. That is how the harness re-adapts to
each machine rather than arriving pre-loaded with its author's environment.

Reading documents and making trivial corrections are not blocked. The doctor
reports the absence as a warning, and as a hard blocker under `--strict`.

Setup instructions are in `agents/LOCAL_SETUP.md`, which is committed precisely
because the directory it describes is not.

## Translation Currency Gate

This project carries English and Spanish. English is canonical; the scope of what
is translated, and why it stops where it does, is ADR-sf-0006.

The gate is one question per translated file: does its recorded `source_sha`
still match the hash of the canonical file it names? A mismatch says the source
moved and the translation has not caught up. It says nothing about whether the
translation is *good* — only that it is not stale.

`agents/harness_doctor.py` does **not** check this; the kernel ships no i18n
check. `agents/check_translations.py` is what makes this gate an artifact rather
than a promise, per the evidence rule at the foot of this file.

Line endings are pinned in `.gitattributes` for `AGENTS.md` and `agents/**/*.md`.
Without that, `git hash-object --no-filters` answers differently on machines with
different `core.autocrlf`, and the gate reports drift on files nobody touched —
which is worse than reporting none.

## Portfolio Quality Gate

For user-facing products, the project fails this gate if it looks technically
present but embarrassing to show:

- scaffold or route-list UI;
- weak copy that describes implementation instead of product behavior;
- missing important states such as loading, empty, error, or success;
- controls that do not map to tested behavior;
- screenshots that do not prove real workflows.

### Project-specific GATE-PQ criteria

This project additionally fails GATE-PQ if:

- the risk scale in `frontend/src/utils/risk.js` is not perceptually ordered —
  originally this named the 4-stop qualitative palette (blue, green, orange,
  red) whose green/orange/red stops are the confusable set for the commonest
  colour vision deficiencies (BL-009). The criterion is the *mechanism*, not the
  hues: an ordered risk ramp must carry its order in lightness, so it survives
  loss of hue discrimination.

  Current state, 2026-09-10: the ramp is blue → teal → green with lightness
  rising monotonically toward high risk (owner request; supersedes the
  peach→terracotta magma ramp of ADR-lq-0008). It satisfies the lightness
  mechanism and stays off the red/green axis, but **two caveats are open and
  should be settled before this gate is called passed**: it was hand-picked and
  has *not* been re-validated with the dataviz `validate_palette` tool the magma
  ramp was checked against; and high risk is the *bright green* end, which
  inverts the near-universal "green means safe" reading and may be misjudged by
  a demo audience;
- the risk overlay is painted over land rather than clipped to the lake
  surface (BL-010);
- the interface presents a forward-filled value as a current reading without
  disclosing how old the underlying satellite pass is (BL-013);
- any displayed metric appears without the baseline it is being compared
  against (rule MI-1).

The "TRL 2 · resultados no validados en campo" seal is **no longer required** in
the UI — withdrawn by owner decision 2026-09-10, ADR-lq-0010, which amends PR-4.
A neutral research-prototype note replaces it. The AI-panel disclaimer is
unaffected and still mandatory. Absence of the seal is not a GATE-PQ failure;
presenting model output as an operational alert still is.

## GATE-MODEL Model Integrity

A project-specific gate added after the 2026-09-09 audit. It applies to any
change touching `src/model/`, `src/features/build_dataset.py`, or the model
artifacts.

| Check | Pass Criteria |
|---|---|
| MI-1 Baselines | The reported model is accompanied by persistence and trivial-rule baselines. Losing to them is reported, not concealed |
| MI-2 Temporal validation | Splits are chronological. No shuffled k-fold over time-ordered rows. An embargo of at least the forecast horizon separates train from validation |
| MI-3 Threshold placement | No absolute alert threshold is baked into training labels. The model predicts a continuous quantity; thresholds are applied at serving time |
| PR-3 No fabrication | No training path consumes forward-filled or otherwise synthesised rows. Reported sample counts distinguish real observations from derived rows |

A model that fails any of these does not ship, regardless of how good its
headline metric looks. A good metric from a failing pipeline is the specific
failure mode this gate exists to catch.

## Rules

- Passing tests are not enough when the visible product is weak.
- Every gate names its evidence. A gate whose evidence is a claim rather than an
  artifact has not been passed.

Project addendum: a good metric is not enough when the pipeline that produced it
is not trustworthy. The audit that motivated this harness found metrics that
looked acceptable and were meaningless.

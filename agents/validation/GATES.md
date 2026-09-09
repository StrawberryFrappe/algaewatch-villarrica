# Validation Gates

## Required Gates

| Gate | Applies When | Pass Criteria | Evidence |
|---|---|---|---|
| GATE-HM Harness Mounted | Always | Harness accepted by user after review | Harness mount review |
| GATE-DR Doctor | Always | No unresolved hard blockers | `agents/validation/DOCTOR.md` |
| GATE-TEST Tests | Active — code project with a confirmed leakage history | Baseline-comparison checks run and pass; no training path consumes fabricated rows | Test output in `EVIDENCE_INDEX.md` |
| GATE-DEPLOY Deployment | Inactive — deployment out of scope | Not applicable before the pitch | Not applicable |
| GATE-PQ Portfolio Quality | Active — owner intends this as a portfolio piece | Visible output is credible, polished, and demonstrable | Screenshots / review |
| GATE-MODEL Model Integrity | Active — project-specific, added after the 2026-09-09 audit | Rules MI-1 to MI-3 and PR-3 all pass. Defined in full below | Baseline comparisons in `EVIDENCE_INDEX.md` |

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

- the risk scale remains the 4-stop qualitative palette in
  `frontend/src/utils/risk.js` (blue, green, orange, red), which is not
  perceptually uniform and whose green/orange/red stops are the confusable set
  for the commonest colour vision deficiencies (BL-009);
- the risk overlay is painted over land rather than clipped to the lake
  surface (BL-010);
- the interface presents a forward-filled value as a current reading without
  disclosing how old the underlying satellite pass is (BL-013);
- any displayed metric appears without the baseline it is being compared
  against (rule MI-1).

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

## Rule

Passing tests are not enough when the visible product is weak.

Project addendum: a good metric is not enough when the pipeline that produced it
is not trustworthy. The audit that motivated this harness found metrics that
looked acceptable and were meaningless.

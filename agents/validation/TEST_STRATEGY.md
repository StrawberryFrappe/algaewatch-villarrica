# Test Strategy

## Current Test Surface

None. The repository has no tests, no test runner configuration, and no CI.
This is the starting position, not the target.

The 2026-09-09 audit was performed with ad-hoc scripts. Their findings are
recorded in `EVIDENCE_INDEX.md` with reproduction commands, but ad-hoc analysis
is not a regression guard: nothing currently prevents the same leakage from being
reintroduced. Converting those checks into permanent tests is BL-002, and it is
sequenced before the retrain so the new model is measured against them from its
first run.

## Required Test Types

| Type | Applies When | Command / Method | Evidence |
|---|---|---|---|
| Model integrity | Any change under `src/model/` or to the dataset builder | Baseline-comparison and leakage checks, run as a test suite | Recorded output in `EVIDENCE_INDEX.md` |
| Unit | Feature engineering functions with a closed-form expected value | Direct assertions on the FAI formula and on window sampling | Test output |
| Integration | Backend routers against the data-access layer | Exercise the API with the committed CSVs, no network | Test output |
| UI / E2E | Deferred before the pitch | Manual walkthrough of the four views, with screenshots | Screenshots under GATE-PQ |
| Static / lint | Not yet configured | Deferred | Not applicable |
| Deployment smoke | Not applicable — deployment out of scope | Not applicable | Not applicable |

## Model Integrity Checks

These are the tests that matter most for this project, because they encode the
defects the audit actually found.

1. **Persistence baseline.** Compute the error of predicting no change over the
   horizon. Any shipped regressor is reported beside it. Currently the model
   loses: 0.00865 against 0.00603 (EV-003).
2. **Trivial-rule baseline.** Compute the score of a rule that uses location
   alone and no measurement. Any shipped classifier is reported beside it.
   Currently the model loses on every metric (EV-002).
3. **No fabricated rows.** Assert that the number of training rows equals the
   number of real observation pairs. A row whose lag features duplicate its
   current value is the signature of forward-fill (EV-004).
4. **Chronological splits.** Assert that no validation index precedes any
   training index, and that a gap of at least the forecast horizon separates
   them. The current pipeline shares a boundary date with no gap (EV-005).
5. **Label independence from location.** Assert that the positive rate does not
   stratify cleanly by station. A target whose positive rate is 0.98 at one
   location and 0.00 at another is measuring place (EV-001).
6. **No present-reading shortcut.** Assert that thresholding the current value
   does not reproduce the label. At present it does so on 90% of rows (EV-009).

Checks 3 through 6 are the ones that would have caught the audited defects before
they reached a metrics file.

## Rule

Do not invent test success. If tests cannot run, record why and what evidence
was used instead.

Project addendum: do not report a model metric without its baselines. Under rule
MI-1 such a metric is not a result, and it is not admissible in
`EVIDENCE_INDEX.md`.

# Test Strategy

## Current Test Surface

A pytest suite under `tests/`, added 2026-09-10 as BL-002. Configuration is
`pytest.ini` at the repository root; there is still no CI.

```bash
python -m pytest -q          # 36 passed, 7 xfailed  (EV-016)
```

Four files, each with a distinct job:

| File | What it holds | State |
|---|---|---|
| `test_evidence_index.py` | EV-001 to EV-011 pinned to their recorded values | passing |
| `test_baselines.py` | Unit tests for the splitter, persistence and the trivial rule | passing |
| `test_station_provenance.py` | The station-coordinate measurements behind EV-014 | passing |
| `test_model_integrity.py` | GATE-MODEL — the seven checks a shipped model must pass | 7 xfail(strict) |

The passing files pin **defects**, not quality. Their job is to stop the numbers
drifting unnoticed, which is what happened to the two figures that carried no
reproduction command before the mount review.

`test_model_integrity.py` is the gate, and every check in it currently fails, so
every one is marked `xfail(strict=True)`. The strictness is load-bearing: when
WI-005 makes a check pass, pytest reports XPASS as a **failure**, so the mark has
to be removed in the same change and the gate cannot be declared satisfied while
the marks remain. A test that asserted today's broken numbers instead would go
green and stay green straight through the fix.

Point the gate at a candidate table without editing anything:

```bash
ALGAEWATCH_DATASET=data/processed/candidate.csv python -m pytest tests/test_model_integrity.py
```

The checks live in `src/model/integrity.py` and the baselines they call in
`src/model/baselines.py`, so the retrain path and the test suite run the same
code rather than two implementations that can drift apart.

The 2026-09-09 audit was performed with ad-hoc scripts. Those findings remain in
`EVIDENCE_INDEX.md` with reproduction commands; what changed is that they are no
longer only commands somebody might run.

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

7. **Station points on water.** Assert that each declared station coordinate sits
   within 0.35 km of a water pixel, and that its reading falls inside the
   distribution of the scene it was drawn from. Two of four currently fail on
   both counts (EV-014, ADR-sf-0007). Added 2026-09-10; it is the only check
   here that examines where the numbers came from rather than what was done with
   them, and it is upstream of checks 1, 2 and 5.

Checks 3 through 7 are the ones that would have caught the audited defects before
they reached a metrics file.

## Rule

Do not invent test success. If tests cannot run, record why and what evidence
was used instead.

Project addendum: do not report a model metric without its baselines. Under rule
MI-1 such a metric is not a result, and it is not admissible in
`EVIDENCE_INDEX.md`.

# Implementation Review — WI-004 / BL-002

Date: 2026-09-10
Reviewer: delegated subagent (`cavecrew-reviewer`), not the implementing agent
Scope: `git diff 912376c..874befc` — the baselines module, the integrity checks,
the `tests/` suite, and the `train.py` patch
Verdict: **APPROVE WITH FIXES** — three findings, all resolved in `c49c9a5`

Subagents were available on this machine (`agents/local/CAPABILITIES.md`,
2026-09-10), so the review was delegated rather than self-performed. No
downgrade applies.

## Findings

| # | Severity | Finding | Status |
|---|---|---|---|
| 1 | P2 | `check_no_fabricated_rows` passed vacuously on an empty table | Fixed |
| 2 | P2 | The two MI-1 tests compared metrics and baselines from different partitions | Fixed |
| 3 | P1 | The baselines' partition was re-derived and could differ from the model's | Fixed |

### 1 — An empty table satisfied PR-3 trivially

With no rows, `n_rows == n_unique` holds and the duplicate-lag fraction is NaN,
so both assertions succeeded and the check reported a pass. A broken build would
have produced a clean gate, which is the specific failure this module exists to
prevent. Empty input is now an explicit failure, with a regression test.

### 2 — Comparison across two partitions

`metrics.json` is produced by `train.py`, which splits without an embargo. The
tests recomputed the baselines on the embargoed split. Since `trivial_rule`
selects its group from the training partition, a different training partition can
select a different group, and the numbers being compared would not be
like-for-like. Both tests now use the pipeline split.

### 3 — The partition was rebuilt, not handed over

The reviewer asked whether the rebuilt split matched what training actually used.
Checking it turned out worse than the question implied.

`train.py` sorts by date and slices positionally. `chronological_split` sorted
again to rebuild that partition — and `DataFrame.sort_values` defaults to
quicksort, which is not stable. This table carries four rows per date, one per
station, so re-sorting reorders ties. Verified on the committed data:

```
re-sort is a no-op under quicksort: False
quicksort holdout persistence MAE = 0.00603
stable    holdout persistence MAE = 0.00596
```

The baselines were therefore being scored on a partition that *could* differ from
the model's, and on this data happened not to. A baseline measured on a different
holdout than the model is not a baseline; that it agreed by luck is not a defence.

Fixed by removing the re-derivation rather than tightening it:
`baselines.split_from_frames` wraps a partition the caller already holds and
computes only its boundary facts, and `train.py` passes the exact frames it
fitted and scored on. `chronological_split` keeps a stable sort for the forward
path, where idempotence is what is wanted. `train.py`'s own sort was left exactly
as the audited pipeline had it, so the model's partition and every EV figure are
unchanged.

## Note On The Review Itself

The reviewer described the estimators as "xgboost/ridge"; they are
`GradientBoostingClassifier` and `GradientBoostingRegressor`. The misnaming did
not affect the finding, which was about partition reconstruction and was correct
and the most valuable of the three. Recorded because a review is evidence, and
evidence is worth more when its errors are visible too.

## Verification After Fixes

```bash
python -m pytest -q          # 36 passed, 7 xfailed
```

Model metrics reproduce exactly after the change: precision 0.8367, recall
0.4659, F1 0.5985, AUC 0.9003, MAE 0.00867, confusion matrix 41/8/47/175.

# Implementation review — per-pixel retrain + serving (`demoday`)

**Date:** 2026-09-10
**Scope:** full diff of `demoday` against `32a1af9` (the `wip/per-pixel-retrain` tip)
**Reviewer:** independent subagent, not the author
**Verdict:** **APPROVE WITH FIXES** — no Critical, no Important. Two risk-level
findings and one nit, all three applied on the same branch.

Satisfies Definition of Done §7 for this branch, which `RUN_STATE.md` had
recorded as an open blocker.

## Why this review mattered

The branch touches gate code — `src/model/baselines.py` and
`tests/test_model_integrity.py`. That is exactly the category that produced two
**false passes** in WI-005 (BL-029 to BL-032), so the reviewer was explicitly
asked to be adversarial about it and to argue both sides of the one relaxed test
assertion.

## Findings

### 🟡 1. `requirements.txt` — the pin's comment had become false

The comment asserted "quantile_mlp.pt holds a state_dict and **nothing loads it
yet**". True when written; falsified by a later commit **on the same branch**
that added `src/model/per_pixel_infer.py`, which does
`torch.load(..., weights_only=True)` on that file.

The best finding of the review. This repository's own rule is that unsourced or
stale claims are the ones that rot, and the author left one in a file whose whole
purpose is to explain a constraint.

**Applied.** The comment now gives both reasons — reproducibility of the reported
number *and* loading the artifact — and is explicit that the second is a weaker
constraint than the scikit-learn pin above, but a real one, because the safe
unpickler's allowlist and `state_dict` key compatibility are both
version-dependent.

### 🟡 2. `model_candidate()` could 500 where it promised 404

The handler built its response by raw `m["key"]` indexing, including nested
`m["metrics"][k]`, `m["cv"]["scheme"]` and `m["cv"]["folds"]`. A `metrics.json`
from an older or hand-edited schema raises an uncaught `KeyError` → unhandled
500, contradicting the endpoint's own documented contract that a client can
"hide the panel rather than render an empty one".

The reviewer correctly noted this mirrors existing house style in
`model_metrics()` above it, so it is not a new pattern — but that it undercuts a
guarantee this endpoint specifically makes.

**Applied.** The body moved to `_candidate_response()` and the handler wraps it
in `except KeyError -> 404`, naming the missing key in the detail. Covered by
`test_candidate_endpoint_404s_on_a_schema_it_cannot_read`.

### 🔵 3. `scripts/train_per_pixel.py` — inconsistent encoding fix

`json.dumps(..., indent=2)` without `ensure_ascii=False`, unlike the matching fix
applied to `src/model/train.py` **in this same branch** for the same defect
class. Functionally harmless — `json.loads` decodes `\uXXXX` correctly — but an
inconsistent fix for a bug the branch is explicitly fixing.

**Applied.** Both writers now agree.

## What the reviewer checked and cleared

- **Early stopping does not leak (the central claim).** `_inner_split` carves the
  inner hold-out strictly from the `train` argument's own index by date cutoff.
  For fold models `train` already excludes the held-out spatial block and any row
  whose target lands on or after the outer validation start, so the inner
  hold-out **cannot** overlap outer validation rows. Verified in code and against
  `test_inner_split_is_temporal_and_disjoint`. `final_model` legitimately differs
  by training on the full frame — it is the deployed artifact, and the reported
  cross-validated MAE is computed before it is fit.
- **The relaxed gate assertion is a correction, not a weakening.**
  `check_label_not_stratified_by_station` was **not modified** in this branch; it
  already short-circuits to `applicable=False` when the label column is absent,
  independent of group count. Only the test's own predicate changed, to match
  that pre-existing behaviour for a continuous-target fixture (1,866 groups, no
  `bloom_7d`). The reviewer argued both sides and landed on legitimate.
- **`trivial_rule`'s guard is purely additive.** For tables carrying both columns
  `missing` is empty and behaviour is unchanged. It replaces a crash with an
  honest `available: False`; it does not mask a real failure.
- **Inference matches training.** Feature order comes from the artifact's own
  stored list, not the module constant, so an order mismatch cannot silently
  corrupt predictions. The back-transform is identical to
  `per_pixel.predict_quantiles`, cross-checked numerically by
  `test_back_transform_matches_the_training_path`. `weights_only=True` is
  sufficient for what is stored.
- **The reported numbers recompute.** Fold and aggregate MAE recompute from
  `metrics.json`; `beats_baselines` is consistent with them; and the UI's
  "gana en 2 de 4 folds" claim matches the underlying fold data.
- **`HeatLayer` cleanup leaks nothing**, including the path where `attach()`
  never fires.
- **Nothing wires the candidate into `/risk` or `/forecast`.** `serving: False`
  is hardcoded and honest.
- Full suite green at review time: 92 passed, 8 xfailed, 0 failures.

## Not in scope, still open

**BL-037** — `check_no_fabricated_rows` misfires on the per-pixel table
(inflation 1.011, a quantisation artifact). Deliberately left unfixed by the
candidate's author and not delegated to this reviewer either, since the fix is a
judgement call about a gate check rather than a defect in this diff.

# ADR-sf-0010: Decisions taken on the per-pixel handoff

## Status

Accepted 2026-09-10. Resolves the two questions `PARA_JUN.md` §3 left open for
the reviewer, records three further decisions taken while making the prototype
runnable, and records what the handoff got wrong about its own environment.

Minted by `sf`. Numbering continues from the highest existing ADR regardless of
slug (ADR-sf-0005 §2).

## Context

`PARA_JUN.md` (commit `32a1af9`, branch `wip/per-pixel-retrain`) handed off a
mid-flight per-pixel retrain. It left two questions explicitly open for whoever
picked the work up, and the session that inherited it was working against a
demo deadline, which forced a decision on sequencing as well.

## Decision

### D1 — Pin `torch==2.14.0`, but not for the reason `scikit-learn` is pinned

`PARA_JUN.md` §3 proposed following the WI-005 precedent, where
`scikit-learn==1.7.2` is pinned because the committed `*.joblib` artifacts fail
to unpickle on a mismatched minor. **That reasoning does not transfer.**

Checked before deciding:

- There is no `torch.load` anywhere in the branch. `scripts/train_per_pixel.py`
  only writes; `src/model/per_pixel.py:252` saves a `state_dict` — a dict of
  tensors, not a pickled estimator. Nothing loads the artifact yet.
- So the unpickling failure mode cannot occur, and copying that comment would
  have put a false claim in a repository that audits its own claims.

The pin is still correct, for a different reason. `src/model/per_pixel.py:124`
calls `torch.manual_seed(SEED)` and `:131` builds a seeded `Generator` for the
DataLoader, and `metrics.json` publishes MAE as a reproducible claim.
Initialisation and optimiser internals shift across torch minors, so an
unpinned bump changes the reported number from an unchanged command. **The pin
protects the number, not the file**, and the comment in `requirements.txt` says
so.

### D2 — `data/processed/fai_grid_series.csv` stays committed as a plain file

Not actually an open question: `.gitignore` already records the policy —
`data/processed/` is committed *on purpose* so the repository is reproducible
without re-hitting the Sentinel-2/CDS APIs. The real question was whether 5 MB
breaks it. Measured:

| Quantity | Value |
|---|---|
| Raw size | 5,004,750 B |
| Compressed (zlib, git's own encoding) | ~772 KB |
| Pack size before | ~200 KiB |
| GitHub per-file warning threshold | 50 MB |

A CSV of floats compresses ~6.5×. The real cost is under 0.8 MB, three orders
of magnitude below any limit.

**Git LFS was rejected.** It makes `git-lfs` a hard prerequisite for every
contributor and for CI — anyone without it gets pointer files instead of data —
and `.gitattributes` is deliberately narrow-scoped (ADR-sf-0006: a repo-wide
rule would renormalise the original author's files). That friction is not worth
772 KB.

The one residual risk is churn: each regeneration costs another ~772 KB. The
table is append-only by date, not rewritten, so this is slow. Revisit if the
pack approaches ~50 MB.

### D3 — One branch, no BL-026 split

`PARA_JUN.md` §"Gaps" argued that BL-026 (baselines through the API + the
`ModelView.jsx` card) and the `integrity.py` hardening are separately
reviewable and are held hostage by an unreviewed per-pixel branch. Half right:

- The `integrity.py` hardening is **not** blocking anyone. Runbook step 0 checks
  out `wip/per-pixel-retrain`, so the work has it. Its tests co-evolved with
  `tests/conftest.py` and the per-pixel gate; splitting it buys a rebase and a
  second review cycle and unblocks nothing.
- BL-026 is a genuine candidate to split — it delivers value regardless of
  whether the retrain beats climatology.

**Split not performed.** The repository owner directed a single branch based on
the teammate's branch. Recorded here as an owner decision, not a technical
finding: if the per-pixel work is reworked, BL-026 is still worth extracting.

### D4 — The model disclaimer is Spanish, and no longer claims a stale blocker

`metrics.json.caveats` renders verbatim as the `ModelView` disclaimer in an
otherwise Spanish UI, and it was English. It also asserted "ERA5 pending CDS
licence acceptance", which stopped being true on 2026-09-10 when the CC-BY
licence was accepted.

Both the generator (`src/model/train.py`) and the committed artifact were
updated. **Only the `caveats` key changed**; every metric in the artifact is
byte-identical to `HEAD`, verified by key-wise comparison before committing.
This is a narrative field, not a measurement — the rule against hand-editing
artifacts is about figures.

### D5 — The handoff's environment claims did not hold; its test claim did

`PARA_JUN.md` §1 asserted a working `.venv` carrying `torch 2.14.0+cu130`, and
§2 asserted that `2025-09/10/11` were already downloaded to `data/raw/era5/`
and that the backfill would resume from there.

Scanning the main checkout and all five worktrees found **no `.venv`, no
`data/raw/era5/`, and no `frontend/node_modules` anywhere**. The environment was
rebuilt from scratch. The ERA5 backfill restarted from month zero.

What the handoff got right, once an environment existed: `pytest -q` reproduces
**78 passed, 8 xfailed** exactly as claimed.

`RUN_STATE.md` already notes "This is the second time a RUN_STATE claim has
outrun reality". This is the third, and the first where the claim was about the
environment rather than the repository. **A claim about local state that no
committed artifact can witness should be written as a command to re-run, not as
a fact.** The runbook's own step 0 is the right shape; §1's inventory is not.

Corollary: the documented install (`pip install -r requirements.txt`) yields
`torch 2.14.0+cpu` on this machine — neither the `+cu126` of EV-017 nor the
`+cu130` of `PARA_JUN.md`. Both of those describe a manually installed CUDA
wheel. CPU is sufficient for this model (an MLP over ~99k rows); anyone needing
CUDA must install it deliberately, and should expect their numbers to differ
from a CPU run.

### D6 — Early stopping on an inner temporal hold-out, not hyperparameter tuning

The per-pixel fit ran a fixed 80-epoch budget with no stopping criterion, which
is far past the point where the network starts memorising noise.

These figures were measured on the **real** `fai_grid_series.csv` (98,886 rows,
1,888 pixels, 56 passes) joined to **synthetic** weather, because the ERA5
backfill had not finished when the diagnosis was made. Random weather is noise
by construction, so it is a pessimistic stand-in and these numbers are a
*relative* comparison of the two fits, not the reported result. The reported
result is whatever `scripts/train_per_pixel.py` prints on the real joined
table.

| Configuration (real grid, synthetic weather) | MAE (FAI) | Climatology |
|---|---|---|
| 80 epochs, no stopping | 0.00307 | 0.00130 |
| Early stopping, same features | **0.00168** | 0.00130 |

An ablation over feature subsets showed *every* additional feature making the
unregularised fit worse — the signature of overfitting, not of a bad feature
set. A hypothesis that `lat`/`lng` were extrapolative under the BL-016
geographic hold-out was tested and **refuted**: once early stopping is in
place, dropping them makes the fit worse (0.00251 vs 0.00168). All features
stay. The hypothesis is recorded because it was wrong, not because it was
useful.

`fit_quantile_model` now carves the latest anchor **dates** off the training
partition, tracks pinball loss on them each epoch, keeps the best `state_dict`
and stops after `patience` epochs without improvement.

The split is by date rather than by row, so the inner set has the same shape as
the outer fold, and it comes entirely from the training partition. **The outer
validation rows are never touched**, so the stopping epoch cannot leak into the
reported number. This distinction matters: ADR 0004 and the `PARA_JUN.md`
runbook both forbid tuning toward the reported metric, and selecting an epoch
count on the reporting folds would be exactly that. Selecting it on training
data is a standard, leakage-free regularisation choice.

Two defects surfaced while building it:

- `QuantileMLP()` was constructed with no arguments, so it always used the
  `n_features` default bound at class-definition time — any change to
  `FEATURES` produced a shape error rather than a resized network.
- `_inner_split` now floors the hold-out at one date. `int(4 * 0.2) == 0` would
  have silently disabled early stopping on exactly the small folds where
  overfitting bites hardest.

## Consequences

- `requirements.txt` pins `torch==2.14.0` with a rationale that matches how the
  artifact is actually written.
- The per-pixel grid table stays a plain committed CSV; no LFS prerequisite is
  introduced.
- BL-026 ships inside the per-pixel branch. Extracting it stays an open option.
- The Modelo view no longer shows English text or a stale blocker.
- `EV-022` to `EV-024` record the reproduction commands for the figures above.

"""Baselines the model is measured against — rule MI-1.

A model metric reported on its own is not a result. `agents/validation/GATES.md`
requires every shipped figure to appear beside two references that use no
satellite measurement at all:

  - **persistence**: predict that the future equals the present;
  - **trivial rule**: predict from location alone.

The 2026-09-09 audit found the Gradient Boosting model losing to both (EV-002,
EV-003). This module makes that comparison a permanent, importable computation
instead of an ad-hoc script, so the retrain (WI-005) is measured against it from
its first run rather than compared retrospectively.

PR-1: this consumes an already-built feature table. It never computes FAI and
never imports from `src/features/`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.metrics import (
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
)

#: Forecast horizon in days. Also the minimum embargo between train and holdout
#: under rule MI-2 — a shorter gap lets a training row's target overlap the
#: validation window.
HORIZON_DAYS = 7


@dataclass(frozen=True)
class Split:
    """A chronological partition, plus the boundary facts MI-2 is asserted on."""

    train: pd.DataFrame
    holdout: pd.DataFrame
    embargo_days: int
    last_train_date: str | None
    first_holdout_date: str | None
    gap_days: int | None
    n_embargoed: int
    #: The table's own longest forecast horizon, when it carries a per-row
    #: horizon column. `None` for a fixed-horizon table with no such column, in
    #: which case `check_chronological_split` falls back to `HORIZON_DAYS`. This
    #: is what BL-029 turns on: the audited check compared the gap against the
    #: constant 7 even where the real pass cadence runs to 8 or 9 days.
    max_horizon_days: int | None = None
    #: The latest *target* date among the kept training rows, when a per-row
    #: embargo was applied. `check_chronological_split` asserts this is strictly
    #: before the first holdout date — the realised boundary the embargo
    #: enforced. `gap_days` alone cannot express it: on a dense variable-horizon
    #: table the last kept row usually carries a short horizon, so `gap_days`
    #: tracks the minimum kept horizon, not the maximum (review issue, 2026-09-10).
    max_kept_target_date: str | None = None

    def summary(self) -> dict:
        """Boundary facts only — the frames themselves are not serialisable."""
        return {
            "embargo_days": self.embargo_days,
            "last_train_date": self.last_train_date,
            "first_holdout_date": self.first_holdout_date,
            "gap_days": self.gap_days,
            "n_train": len(self.train),
            "n_holdout": len(self.holdout),
            "n_embargoed": self.n_embargoed,
            "max_horizon_days": self.max_horizon_days,
            "max_kept_target_date": self.max_kept_target_date,
        }


def split_from_frames(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    embargo_days: int = 0,
    date_col: str = "date",
) -> Split:
    """Wrap a partition a caller already has, computing only its boundary facts.

    This exists so a training routine can hand over **the exact frames it fitted
    and scored on** instead of asking this module to re-derive them. Re-deriving
    is not safe: `DataFrame.sort_values` defaults to quicksort, which is not
    stable, so sorting an already-sorted frame can permute rows that share a date
    — and this table has four rows per date, one per station. Verified on the
    committed table: re-sorting changes the ordering, which moves rows across the
    80% boundary and changes the holdout the baselines would be scored on.

    A baseline measured on a different holdout than the model is not a baseline.
    """
    if train.empty or holdout.empty:
        return Split(train, holdout, embargo_days, None, None, None, 0)

    first_holdout = pd.to_datetime(holdout[date_col]).min()
    last_train = pd.to_datetime(train[date_col]).max()
    return Split(
        train=train,
        holdout=holdout,
        embargo_days=embargo_days,
        last_train_date=last_train.date().isoformat(),
        first_holdout_date=first_holdout.date().isoformat(),
        gap_days=int((first_holdout - last_train).days),
        n_embargoed=0,
    )


def chronological_split(
    df: pd.DataFrame,
    holdout_frac: float = 0.2,
    embargo_days: int = HORIZON_DAYS,
    date_col: str = "date",
    horizon_col: str | None = None,
) -> Split:
    """Splits by time, then removes the embargo band from the training side.

    The audited pipeline cut the sorted frame in two and stopped there, which
    left the last training date and the first holdout date identical (EV-005):
    a row trained on 2026-06-09 has a target reaching 2026-06-16, well inside
    the validation window. Dropping every training row within `embargo_days` of
    the holdout boundary is what makes the two partitions independent.

    Rows are removed from the *training* side only. Shrinking the holdout
    instead would move the boundary and quietly change what is being measured.

    **BL-029.** With a fixed 7-day horizon, embargoing the feature date by 7 days
    and embargoing the target date are the same cut. WI-005's lake-anomaly table
    (ADR-sf-0008) has neither: its honest pairs span 5 to 9 days (EV-019), so a
    row 7 days before the holdout with an 8-day horizon still lands its target
    inside the validation window. When `horizon_col` names a per-row horizon,
    the embargo is applied to each row's **target** date — `date + horizon` — and
    the split records the table's longest horizon so the gate check can require
    a gap of at least that, rather than the constant `HORIZON_DAYS`.
    """
    # `kind="stable"` is load-bearing, not tidiness. `train.py` sorts by date and
    # then slices positionally; rebuilding the same partition here means sorting
    # an already-sorted frame, and pandas' default quicksort may permute rows
    # that share a date. Many rows share a date — one per station — so an
    # unstable sort could hand the baselines a different holdout than the model
    # was scored on, and the comparison would quietly stop being like-for-like.
    ordered = df.sort_values(date_col, kind="stable").reset_index(drop=True)
    n_holdout = max(1, int(len(ordered) * holdout_frac))
    cut = len(ordered) - n_holdout

    train_all = ordered.iloc[:cut]
    holdout = ordered.iloc[cut:]

    max_horizon_days = (
        int(ordered[horizon_col].max())
        if horizon_col is not None and horizon_col in ordered.columns
        else None
    )

    if holdout.empty or train_all.empty:
        return Split(train_all, holdout, embargo_days, None, None, None, 0, max_horizon_days)

    first_holdout = pd.to_datetime(holdout[date_col]).min()
    train_dates = pd.to_datetime(train_all[date_col])

    max_kept_target_date = None
    if max_horizon_days is not None:
        # Embargo each row's *target* date, not its feature date. Strict `<`:
        # a training target that lands *on* the first holdout date is the same
        # observation the first holdout row carries as a feature — a seam leak.
        # The single-split and CV paths agree on this (see `lake_anomaly`).
        target_dates = train_dates + pd.to_timedelta(train_all[horizon_col], unit="D")
        keep = target_dates < first_holdout
        applied_embargo = max_horizon_days
        if keep.any():
            max_kept_target_date = target_dates[keep].max().date().isoformat()
    else:
        keep = train_dates <= first_holdout - pd.Timedelta(days=embargo_days)
        applied_embargo = embargo_days
    train = train_all[keep]

    last_train = pd.to_datetime(train[date_col]).max() if len(train) else None
    gap = int((first_holdout - last_train).days) if last_train is not None else None

    return Split(
        train=train,
        holdout=holdout,
        embargo_days=applied_embargo,
        last_train_date=None if last_train is None else last_train.date().isoformat(),
        first_holdout_date=first_holdout.date().isoformat(),
        gap_days=gap,
        n_embargoed=int((~keep).sum()),
        max_horizon_days=max_horizon_days,
        max_kept_target_date=max_kept_target_date,
    )


def persistence_mae(
    frame: pd.DataFrame,
    now_col: str = "fai_now",
    future_col: str = "fai_future",
) -> float:
    """MAE of "the future equals the present" — EV-003.

    Any regressor predicting `fai_future` is reported beside this. One that does
    not beat it has learned nothing a copy of today's value does not already
    provide.
    """
    valid = frame[[now_col, future_col]].dropna()
    if valid.empty:
        return float("nan")
    return float(mean_absolute_error(valid[future_col], valid[now_col]))


def trivial_rule(
    train: pd.DataFrame,
    holdout: pd.DataFrame,
    label_col: str = "bloom_7d",
    group_col: str = "station_id",
) -> dict:
    """Predict from location alone, fitted honestly — EV-002.

    The audit hardcoded `sur` because it already knew which station carried the
    positives. A permanent check must not encode that hindsight: the rule picks
    its group from the **training** partition, exactly as a model would, and is
    then scored on the holdout. If the label really carries bloom information
    rather than place, this rule has nothing to find.

    The ranking score for AUC is each group's training positive rate, so the
    rule is scored as a probabilistic predictor rather than only at its own
    operating point.

    BL-030: on a table with fewer than two groups the location rule degenerates
    to "always predict positive". There it is replaced by climatology — predict
    the training-window mean label, using no measurement — which is what rule
    MI-1 asks of a trivial rule (ADR-sf-0008 D2). The location form is kept
    wherever there are real groups, because it is what reproduces EV-002.
    """
    if train.empty or holdout.empty:
        return {"available": False, "reason": "empty partition"}

    # BL-035: a continuous-target candidate table carries no `bloom_7d`. The
    # integrity checks already return applicable=False for that case, but this
    # function is reached through `compute()` before any of them run, so an
    # unguarded groupby raised KeyError and took the whole gate down -- a gate
    # that crashes reports nothing, which is worse than an honest failure.
    # Same defect shape as BL-030/BL-031: the guard existed one layer up only.
    missing = [c for c in (label_col, group_col) if c not in train.columns or c not in holdout.columns]
    if missing:
        return {
            "available": False,
            "reason": f"no {'/'.join(missing)} column: continuous target, trivial location rule inapplicable",
        }

    rates = train.groupby(group_col)[label_col].mean()
    if rates.empty:
        return {"available": False, "reason": "no groups in training partition"}

    if len(rates) < 2:
        base_rate = float(train[label_col].mean())
        majority = int(round(base_rate))
        y_true = holdout[label_col].to_numpy()
        y_pred = np.full(len(holdout), majority)
        y_score = np.full(len(holdout), base_rate, dtype=float)
        single_class = len(np.unique(y_true)) < 2
        return {
            "available": True,
            "kind": "climatology",
            "rule": "predict training-window mean ({:.4f} -> class {})".format(base_rate, majority),
            "train_positive_rate": round(base_rate, 4),
            "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
            "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
            "auc_roc": None if single_class else round(float(roc_auc_score(y_true, y_score)), 4),
        }

    chosen = str(rates.idxmax())
    y_true = holdout[label_col].to_numpy()
    y_pred = (holdout[group_col] == chosen).astype(int).to_numpy()
    y_score = holdout[group_col].map(rates).fillna(0.0).to_numpy()

    single_class = len(np.unique(y_true)) < 2
    return {
        "available": True,
        "rule": "{} == {!r}".format(group_col, chosen),
        "chosen_group": chosen,
        "train_positive_rates": {str(k): round(float(v), 4) for k, v in rates.items()},
        "precision": round(float(precision_score(y_true, y_pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, y_pred, zero_division=0)), 4),
        "f1_score": round(float(f1_score(y_true, y_pred, zero_division=0)), 4),
        "auc_roc": None if single_class else round(float(roc_auc_score(y_true, y_score)), 4),
    }


def persistence_baseline(frame: pd.DataFrame) -> dict:
    """`persistence_mae` in the same reporting shape as `trivial_rule`."""
    mae = persistence_mae(frame)
    return {
        "available": not np.isnan(mae),
        "rule": "fai_future == fai_now",
        "mae_fai": None if np.isnan(mae) else round(float(mae), 5),
    }


def compute(split: Split) -> dict:
    """Both baselines over one split. This is what `train.py` records."""
    return {
        "split": split.summary(),
        "persistence": persistence_baseline(split.holdout),
        "trivial_rule": trivial_rule(split.train, split.holdout),
    }


def _better(model: float | None, baseline: float | None, lower_is_better: bool) -> bool | None:
    """None when either side is missing — an undecidable comparison is not a pass."""
    if model is None or baseline is None:
        return None
    return (model < baseline) if lower_is_better else (model > baseline)


def beats_baselines(model_metrics: dict, baselines: dict) -> dict:
    """Does the model beat each baseline? `None` means it could not be decided.

    Reported whatever the answer. Under MI-1 a loss is a result, not a defect to
    be hidden: the audited model loses to both, and the metrics file has to say
    so in its own words rather than leave a reader to infer it.
    """
    persistence = baselines.get("persistence", {})
    trivial = baselines.get("trivial_rule", {})
    return {
        "persistence": _better(
            model_metrics.get("mae_fai"), persistence.get("mae_fai"), lower_is_better=True
        ),
        "trivial_rule": _better(
            model_metrics.get("f1_score"), trivial.get("f1_score"), lower_is_better=False
        ),
    }


def report(model_metrics: dict, split: Split) -> dict:
    """Model figures beside their baselines, with the verdict spelled out."""
    baselines = compute(split)
    return {
        "model": model_metrics,
        "baselines": baselines,
        "beats_baselines": beats_baselines(model_metrics, baselines),
    }

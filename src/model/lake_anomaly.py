"""WI-005 — the interim lake-mean anomaly retrain (ADR-sf-0008, ADR-lq-0009).

Ridge regression on the *standardised* causal anomaly of `lake_mean_fai` at the
forecast horizon. Deliberately small: 34 honest pairs (EV-019 minus one
zero-history anchor), 2 features, no GradientBoosting.

What this buys, and what it does not (ADR-sf-0008 D1): an honest measurement of
whether anything beats the baselines on real lake-wide data, and a pipeline the
per-pixel table (ADR 0004 D3) can be poured into unchanged. It is **not** a
model worth shipping, and it does not fill the dashboard's four station cards —
a lake-wide model produces one number for the lake.

Reporting (ADR-sf-0008 D2, D4):

- `mae_fai` in raw FAI units, with its cross-validation spread, is the headline.
- It is reported beside **persistence** (predict today) *and* **climatology**
  (predict the causal baseline mean). Because `z_pred = 0` reproduces
  climatology exactly, a shrinkage model beats persistence almost by
  construction; climatology is the binding bar (EV-019: 0.000945 < 0.001333).
- precision / recall / F1 / AUC are `null`: under the uncalibrated station
  threshold `bloom_7d` is constant (EV-020), so they are not computable from it.

PR-1: this consumes the table `src/features/lake_anomaly.py` builds. It never
computes FAI and never imports from `src/features/` beyond that table's columns.
"""

from __future__ import annotations

from typing import Iterator

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

DEFAULT_FEATURES = ("anomaly_now", "horizon_days")
DEFAULT_ALPHA = 1.0
DEFAULT_N_FOLDS = 4
TARGET_COL = "anomaly_future"

CLASSIFICATION_REASON = (
    "precision/recall/F1/AUC are null: the recorded bloom threshold (0.025916) "
    "was calibrated on the contaminated station series and sits an order of "
    "magnitude above the lake-wide maximum (~0.002, EV-020), so bloom_7d is "
    "constant here and nothing is computable from it. Recalibrate the threshold "
    "on the lake-wide distribution before reporting a classification surface "
    "(ADR-sf-0008 D4, PR-3)."
)

CAVEATS = (
    "TRL 2 — not validated in the field. Interim lake-mean retrain on 34 honest "
    "pairs (ADR-sf-0008): an honest measurement, not a shippable model. z_pred=0 "
    "reproduces climatology, so the model is reported against both persistence "
    "and climatology and climatology is the bar that matters. 18 of the 35 "
    "pass dates serve as both an anchor and a target, so residuals are not "
    "independent across rows (BL-033). One anchor sits ~15 sigma from its causal "
    "baseline — a real heavy tail in the series, not a preprocessing artefact. "
    "Superseded by per-pixel sampling when BL-007 lands (ADR 0004 D3)."
)


def predict_fai(z_pred: np.ndarray, frame: pd.DataFrame) -> np.ndarray:
    """Back-transform a predicted standardised anomaly to a raw FAI value.

    `fai = baseline_mean + z * baseline_std`. `z = 0` is exactly climatology
    (predict the causal baseline mean); `z = 1` is one baseline sigma above it.
    """
    return (
        frame["baseline_mean"].to_numpy()
        + np.asarray(z_pred, dtype=float) * frame["baseline_std"].to_numpy()
    )


def _make_model(alpha: float = DEFAULT_ALPHA) -> Pipeline:
    """StandardScaler because the features live on unlike scales (anomaly ~ 1s,
    horizon ~ 5-8) and Ridge penalises raw coefficient size."""
    return Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])


def expanding_window_folds(
    pairs: pd.DataFrame,
    *,
    n_folds: int = DEFAULT_N_FOLDS,
    date_col: str = "date",
    horizon_col: str = "horizon_days",
) -> Iterator[tuple[pd.DataFrame, pd.DataFrame]]:
    """Chronological expanding-window folds with a per-row target-date embargo.

    The last `n_folds` equal blocks are validation, one per fold; everything
    before the block is candidate training, minus any row whose target date
    (`date + horizon_days`) reaches the validation block — EV-005's seam, the
    same cut `baselines.chronological_split` makes for the single 80/20 split.
    """
    d = pairs.sort_values(date_col).reset_index(drop=True)
    n = len(d)
    block = n // (n_folds + 1)
    if block < 1:
        raise ValueError(f"{n} rows is too few for {n_folds} expanding folds")

    dates = pd.to_datetime(d[date_col])
    targets = dates + pd.to_timedelta(d[horizon_col], unit="D")
    first_val_pos = n - n_folds * block

    for k in range(n_folds):
        val_lo = first_val_pos + k * block
        val_hi = n if k == n_folds - 1 else val_lo + block
        val = d.iloc[val_lo:val_hi]
        first_val_date = dates.iloc[val_lo]
        candidate = d.iloc[:val_lo]
        keep = targets.iloc[:val_lo] < first_val_date
        yield candidate[keep.to_numpy()], val


def _fold_maes(pairs: pd.DataFrame, features, alpha: float, n_folds: int) -> dict:
    model_maes, persistence_maes, climatology_maes, train_sizes = [], [], [], []
    for train, val in expanding_window_folds(pairs, n_folds=n_folds):
        model = _make_model(alpha)
        model.fit(train[list(features)], train[TARGET_COL])
        z_pred = model.predict(val[list(features)])
        fai_pred = predict_fai(z_pred, val)

        model_maes.append(float(mean_absolute_error(val["fai_future"], fai_pred)))
        persistence_maes.append(float(mean_absolute_error(val["fai_future"], val["fai_now"])))
        climatology_maes.append(float(mean_absolute_error(val["fai_future"], val["baseline_mean"])))
        train_sizes.append(len(train))
    return {
        "model": model_maes,
        "persistence": persistence_maes,
        "climatology": climatology_maes,
        "train_sizes": train_sizes,
    }


def fit_and_evaluate(
    pairs: pd.DataFrame,
    *,
    features: tuple[str, ...] = DEFAULT_FEATURES,
    alpha: float = DEFAULT_ALPHA,
    n_folds: int = DEFAULT_N_FOLDS,
    bloom_threshold: float | None = None,
) -> dict:
    """Cross-validate, then fit on every pair for the persisted artifact.

    Returns ``{"model": <fitted Pipeline>, "metrics": <dict>}``. The metrics
    dict mirrors the shape of `src/model/artifacts/metrics.json` where it can,
    so a reader who knows the station model can read this one.
    """
    features = tuple(features)
    folds = _fold_maes(pairs, features, alpha, n_folds)

    mae_fai = float(np.mean(folds["model"]))
    mae_cv_std = float(np.std(folds["model"]))
    persistence_mae = float(np.mean(folds["persistence"]))
    climatology_mae = float(np.mean(folds["climatology"]))

    final_model = _make_model(alpha)
    final_model.fit(pairs[list(features)], pairs[TARGET_COL])

    dates = pd.to_datetime(pairs["date"])
    metrics = {
        "version": "wi005-lake-anomaly-v1",
        "signal": "lake_mean_fai",
        "target": "standardised causal anomaly of lake_mean_fai at the horizon",
        "target_kind": "continuous",
        # Carried, not calibrated: the station-series threshold (EV-020), an
        # order of magnitude above the lake-wide maximum. The gate reads it to
        # show `bloom_7d` is constant here; nothing trains on it.
        "fai_alert_threshold": bloom_threshold,
        "n_pairs": len(pairs),
        "date_range": {"start": dates.min().date().isoformat(), "end": dates.max().date().isoformat()},
        "horizons": {int(k): int(v) for k, v in sorted(pairs["horizon_days"].value_counts().items())},
        "features_used": list(features),
        "alpha": alpha,
        "cv": {
            "scheme": "expanding-window chronological, per-row target-date embargo",
            "n_folds": n_folds,
            "fold_mae_fai": [round(x, 6) for x in folds["model"]],
            "fold_train_sizes": folds["train_sizes"],
        },
        "metrics": {
            "mae_fai": round(mae_fai, 6),
            "mae_fai_cv_std": round(mae_cv_std, 6),
            "precision": None,
            "recall": None,
            "f1_score": None,
            "auc_roc": None,
        },
        "baselines": {
            "persistence": {"rule": "fai_future == fai_now", "mae_fai": round(persistence_mae, 6)},
            "climatology": {
                "rule": "fai_future == causal baseline mean",
                "mae_fai": round(climatology_mae, 6),
            },
        },
        "beats_baselines": {
            "persistence": bool(mae_fai < persistence_mae),
            "climatology": bool(mae_fai < climatology_mae),
        },
        "classification_reason": CLASSIFICATION_REASON,
        "caveats": CAVEATS,
    }
    return {"model": final_model, "metrics": metrics}

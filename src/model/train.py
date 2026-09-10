"""Trains the Gradient Boosting bloom-risk model. This is THE model — the only
place training happens. It consumes the feature table build_dataset.py
produces; it must never compute FAI or call Sentinel-2/CDS APIs itself.

Two models are trained on the same feature table:
  - a classifier for bloom_7d (risk classification, matches the confusion
    matrix / precision / recall / F1 / AUC-ROC in the design's Model view)
  - a regressor for fai_future (gives the MAE-FAI metric)

Validation: 5-fold cross-validation on the training partition, plus a
temporal hold-out (the most recent slice, never seen during CV) — matching
"Validación cruzada 5-fold + hold-out temporal" in the design handoff.
"""

import json
from datetime import date
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold

from .baselines import beats_baselines, split_from_frames
from .baselines import compute as compute_baselines

ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"

FEATURE_CANDIDATES = [
    "fai_now", "fai_lag_1d", "fai_lag_3d", "fai_lag_7d",
    "temp_c", "wind_kmh", "precip_mm",
    "water_temp_c", "ph", "dissolved_oxygen_mgl",
]


def _usable_features(df: pd.DataFrame) -> list[str]:
    """Drops feature columns that are entirely NaN (e.g. ERA5/in-situ before
    those sources are wired in) instead of silently feeding NaN to the model.
    """
    usable = [c for c in FEATURE_CANDIDATES if c in df.columns and df[c].notna().any()]
    dropped = [c for c in FEATURE_CANDIDATES if c in df.columns and c not in usable]
    if dropped:
        print(f"  [warn] dropping all-NaN feature columns (source not wired in yet): {dropped}")
    return usable


def train(df: pd.DataFrame, bloom_threshold: float, holdout_frac: float = 0.2, n_folds: int = 5) -> dict:
    df = df.dropna(subset=["bloom_7d", "fai_future"]).sort_values("date").reset_index(drop=True)
    features = _usable_features(df)
    if not features:
        raise ValueError("No usable (non-NaN) feature columns — need at least FAI history.")

    X = df[features].fillna(df[features].median())
    y_cls = df["bloom_7d"].to_numpy()
    y_reg = df["fai_future"].to_numpy()

    n_holdout = max(1, int(len(df) * holdout_frac))
    train_idx = slice(0, len(df) - n_holdout)
    holdout_idx = slice(len(df) - n_holdout, len(df))

    X_train, y_train_cls, y_train_reg = X.iloc[train_idx], y_cls[train_idx], y_reg[train_idx]
    X_hold, y_hold_cls, y_hold_reg = X.iloc[holdout_idx], y_cls[holdout_idx], y_reg[holdout_idx]

    # 5-fold CV on the training partition (skipped gracefully if too small or single-class).
    cv_scores = []
    n_classes_train = len(np.unique(y_train_cls))
    if len(X_train) >= n_folds and n_classes_train > 1:
        skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=0)
        for fold, (tr, va) in enumerate(skf.split(X_train, y_train_cls)):
            clf = GradientBoostingClassifier(random_state=0)
            clf.fit(X_train.iloc[tr], y_train_cls[tr])
            if len(np.unique(y_train_cls[va])) > 1:
                proba = clf.predict_proba(X_train.iloc[va])[:, 1]
                cv_scores.append(roc_auc_score(y_train_cls[va], proba))
    else:
        print(f"  [warn] skipping 5-fold CV: {len(X_train)} training rows, "
              f"{n_classes_train} class(es) present")

    classifier = GradientBoostingClassifier(random_state=0)
    classifier.fit(X_train, y_train_cls)

    regressor = GradientBoostingRegressor(random_state=0)
    regressor.fit(X_train, y_train_reg)

    if len(X_hold) and len(np.unique(y_hold_cls)) > 1:
        hold_pred = classifier.predict(X_hold)
        hold_proba = classifier.predict_proba(X_hold)[:, 1]
        cm = confusion_matrix(y_hold_cls, hold_pred, labels=[0, 1])
        tn, fp, fn, tp = cm.ravel()
        precision = precision_score(y_hold_cls, hold_pred, zero_division=0)
        recall = recall_score(y_hold_cls, hold_pred, zero_division=0)
        f1 = f1_score(y_hold_cls, hold_pred, zero_division=0)
        auc = roc_auc_score(y_hold_cls, hold_proba)
    else:
        print("  [warn] hold-out has a single class or is empty — classification "
              "metrics are not meaningful with this sample; reporting raw counts only")
        tn = fp = fn = tp = 0
        precision = recall = f1 = auc = float("nan")

    mae_fai = mean_absolute_error(y_hold_reg, regressor.predict(X_hold)) if len(X_hold) else float("nan")

    importances = dict(zip(features, classifier.feature_importances_.tolist()))

    # Rule MI-1: no metric ships without the baselines it is compared against.
    # The partition is handed over rather than re-derived, so the baselines are
    # scored on exactly the rows the model was scored on. `embargo_days=0`
    # records the truth about this split: it has no embargo, which is the EV-005
    # defect. It is reported rather than quietly corrected here, because giving
    # training an embargo changes what the model learns and that is BL-006.
    model_scores = {
        "precision": None if np.isnan(precision) else round(float(precision), 4),
        "recall": None if np.isnan(recall) else round(float(recall), 4),
        "f1_score": None if np.isnan(f1) else round(float(f1), 4),
        "auc_roc": None if np.isnan(auc) else round(float(auc), 4),
        "mae_fai": None if np.isnan(mae_fai) else round(float(mae_fai), 5),
    }
    split = split_from_frames(df.iloc[train_idx], df.iloc[holdout_idx], embargo_days=0)
    baselines = compute_baselines(split)
    verdict = beats_baselines(model_scores, baselines)

    metrics = {
        "version": "v0.1.0-real-smoke",
        "fai_alert_threshold": bloom_threshold,
        "features_used": features,
        "n_observations": len(df),
        "date_range": {"start": df["date"].min(), "end": df["date"].max()},
        "n_train": len(X_train),
        "n_holdout": len(X_hold),
        "cv_auc_scores": cv_scores,
        "confusion_matrix": {
            "true_positives": int(tp), "false_positives": int(fp),
            "false_negatives": int(fn), "true_negatives": int(tn),
        },
        "feature_importance": importances,
        "metrics": model_scores,
        "baselines": baselines,
        "beats_baselines": verdict,
        "retrained_at": date.today().isoformat(),
        # Rendered verbatim in the Spanish UI (ModelView disclaimer), so it is
        # written in Spanish. The ERA5 note tracks the backfill, not the licence:
        # CDS licence acceptance cleared on 2026-09-10.
        "caveats": (
            "Corrida real a escala de smoke test: variables solo de FAI (ERA5-Land pendient"
            "e de backfill; in situ pendiente de los CSV de SNIA). El tamaño de muestra y e"
            "l conjunto de variables todavía no alcanzan para métricas de producción. TRL 2"
            " — no validado en campo. Estas cifras no superan a sus baselines: ver 'baselin"
            "es' y 'beats_baselines' en este archivo (regla MI-1)."
        ),
    }
    return {"classifier": classifier, "regressor": regressor, "metrics": metrics}


def save_artifacts(result: dict, out_dir: Path = ARTIFACTS_DIR) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["classifier"], out_dir / "classifier.joblib")
    joblib.dump(result["regressor"], out_dir / "regressor.joblib")
    with open(out_dir / "metrics.json", "w") as f:
        json.dump(result["metrics"], f, indent=2)

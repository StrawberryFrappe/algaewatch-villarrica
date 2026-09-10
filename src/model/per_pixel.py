"""Per-pixel PyTorch quantile model for ADR 0004 D1-D4 / BL-008.

Consumes an already-built table. Temporal folds embargo each training target;
each fold also holds out one fixed lake region, so neighbouring pixels from the
validation region never appear in training (MI-2 + BL-016).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import mean_absolute_error
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

FEATURES = (
    "anomaly_now",
    "horizon_days",
    "baseline_mean",
    "baseline_std",
    "temp_c",
    "precip_mm",
    "wind_kmh",
    "lat",
    "lng",
    "doy_sin",
    "doy_cos",
)
TARGET = "anomaly_future"
QUANTILES = (0.1, 0.5, 0.9)
SEED = 20260910


@dataclass(frozen=True)
class FeatureScaler:
    mean: np.ndarray
    scale: np.ndarray

    @classmethod
    def fit(cls, values: np.ndarray) -> "FeatureScaler":
        mean = values.mean(axis=0)
        scale = values.std(axis=0)
        scale[scale == 0] = 1.0
        return cls(mean=mean, scale=scale)

    def transform(self, values: np.ndarray) -> np.ndarray:
        return (values - self.mean) / self.scale


class QuantileMLP(nn.Module):
    def __init__(self, n_features: int = len(FEATURES), hidden: int = 64):
        super().__init__()
        self.network = nn.Sequential(
            nn.Linear(n_features, hidden),
            nn.ReLU(),
            nn.Linear(hidden, hidden // 2),
            nn.ReLU(),
            nn.Linear(hidden // 2, len(QUANTILES)),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        # Sorting makes q10 <= q50 <= q90 by construction. torch.sort remains
        # differentiable for the selected values and prevents quantile crossing.
        return torch.sort(self.network(inputs), dim=1).values


def pinball_loss(prediction: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    quantiles = prediction.new_tensor(QUANTILES).reshape(1, -1)
    error = target.reshape(-1, 1) - prediction
    return torch.maximum(quantiles * error, (quantiles - 1) * error).mean()


def spatiotemporal_folds(
    frame: pd.DataFrame, *, n_folds: int = 4
) -> Iterator[tuple[pd.DataFrame, pd.DataFrame, dict]]:
    """Expanding-date folds with target embargo and rotating spatial holdout."""
    dates = pd.Index(sorted(pd.to_datetime(frame["date"]).dt.normalize().unique()))
    block_size = len(dates) // (n_folds + 1)
    if block_size < 1:
        raise ValueError(f"{len(dates)} unique dates are too few for {n_folds} folds")
    spatial_blocks = sorted(frame["spatial_block"].unique().tolist())
    if len(spatial_blocks) < n_folds:
        raise ValueError("Need at least one distinct spatial block per fold")

    row_dates = pd.to_datetime(frame["date"]).dt.normalize()
    target_dates = row_dates + pd.to_timedelta(frame["horizon_days"], unit="D")
    first_val_pos = len(dates) - n_folds * block_size

    for fold in range(n_folds):
        lo = first_val_pos + fold * block_size
        hi = len(dates) if fold == n_folds - 1 else lo + block_size
        val_dates = dates[lo:hi]
        first_val = pd.Timestamp(val_dates[0])
        held_block = spatial_blocks[fold]
        train_mask = (target_dates < first_val) & (frame["spatial_block"] != held_block)
        val_mask = row_dates.isin(val_dates) & (frame["spatial_block"] == held_block)
        train = frame.loc[train_mask].copy()
        val = frame.loc[val_mask].copy()
        if train.empty or val.empty:
            raise ValueError(f"Fold {fold} produced an empty train/validation partition")
        meta = {
            "fold": fold + 1,
            "held_spatial_block": int(held_block),
            "first_validation_date": first_val.date().isoformat(),
            "last_validation_date": pd.Timestamp(val_dates[-1]).date().isoformat(),
            "max_training_target_date": target_dates.loc[train.index].max().date().isoformat(),
            "n_train": len(train),
            "n_validation": len(val),
        }
        yield train, val, meta


def _inner_split(train: pd.DataFrame, holdout_fraction: float) -> tuple[pd.Index, pd.Index]:
    """Carve the latest training anchor dates off as an inner validation set.

    Split by date, not by row, so the inner set is a temporal hold-out of the
    same shape as the outer fold. It is taken entirely from the training
    partition, so the outer validation rows stay untouched and early stopping
    cannot leak the reported number (ADR-sf-0010 D6).
    """
    dates = pd.Index(sorted(pd.to_datetime(train["date"]).dt.normalize().unique()))
    if len(dates) < 3:
        # Too few anchors to hold any back and still have something to fit on.
        # Caller falls back to a fixed epoch budget.
        return train.index, pd.Index([])
    # Floor of one date: int(4 * 0.2) == 0 would silently disable early stopping
    # on the small folds, which is where overfitting bites hardest.
    n_holdout = max(1, int(len(dates) * holdout_fraction))
    cutoff = dates[len(dates) - n_holdout]
    row_dates = pd.to_datetime(train["date"]).dt.normalize()
    return train.index[row_dates < cutoff], train.index[row_dates >= cutoff]


def fit_quantile_model(
    train: pd.DataFrame,
    *,
    epochs: int = 80,
    batch_size: int = 2048,
    learning_rate: float = 1e-3,
    patience: int = 8,
    inner_holdout_fraction: float = 0.2,
) -> tuple[QuantileMLP, FeatureScaler]:
    """Fit the quantile MLP, early-stopping on an inner temporal hold-out.

    The signal in this table is weak enough that an unregularised fit is worse
    than predicting the climatological mean: every additional epoch past the
    inner-loss minimum buys memorised noise. Early stopping is chosen on data
    the outer fold never sees, so the reported MAE stays an honest hold-out
    number rather than a tuned one.
    """
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    fit_index, inner_index = _inner_split(train, inner_holdout_fraction)

    values = train.loc[fit_index, list(FEATURES)].to_numpy(dtype=np.float32)
    scaler = FeatureScaler.fit(values)
    inputs = torch.from_numpy(scaler.transform(values).astype(np.float32))
    target = torch.from_numpy(train.loc[fit_index, TARGET].to_numpy(dtype=np.float32))
    dataset = TensorDataset(inputs, target)
    generator = torch.Generator().manual_seed(SEED)
    loader = DataLoader(
        dataset,
        batch_size=min(batch_size, len(dataset)),
        shuffle=True,
        generator=generator,
    )

    if len(inner_index):
        inner_values = train.loc[inner_index, list(FEATURES)].to_numpy(dtype=np.float32)
        inner_inputs = torch.from_numpy(scaler.transform(inner_values).astype(np.float32))
        inner_target = torch.from_numpy(
            train.loc[inner_index, TARGET].to_numpy(dtype=np.float32)
        )
    else:
        inner_inputs = inner_target = None

    model = QuantileMLP(n_features=len(FEATURES))
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)

    best_loss = float("inf")
    best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
    since_improved = 0

    for _ in range(epochs):
        model.train()
        for batch_inputs, batch_target in loader:
            optimizer.zero_grad()
            loss = pinball_loss(model(batch_inputs), batch_target)
            loss.backward()
            optimizer.step()

        if inner_inputs is None:
            continue
        model.eval()
        with torch.no_grad():
            inner_loss = float(pinball_loss(model(inner_inputs), inner_target))
        if inner_loss < best_loss - 1e-9:
            best_loss = inner_loss
            best_state = {k: v.detach().clone() for k, v in model.state_dict().items()}
            since_improved = 0
        else:
            since_improved += 1
            if since_improved >= patience:
                break

    if inner_inputs is not None:
        model.load_state_dict(best_state)
    return model.eval(), scaler


def predict_quantiles(
    model: QuantileMLP, scaler: FeatureScaler, frame: pd.DataFrame
) -> np.ndarray:
    values = frame[list(FEATURES)].to_numpy(dtype=np.float32)
    inputs = torch.from_numpy(scaler.transform(values).astype(np.float32))
    with torch.no_grad():
        anomaly_quantiles = model(inputs).numpy()
    baseline = frame["baseline_mean"].to_numpy(dtype=float).reshape(-1, 1)
    spread = frame["baseline_std"].to_numpy(dtype=float).reshape(-1, 1)
    return baseline + anomaly_quantiles * spread


def fit_and_evaluate(
    frame: pd.DataFrame,
    *,
    epochs: int = 80,
    n_folds: int = 4,
) -> dict:
    """Evaluate like-for-like against persistence and causal climatology."""
    fold_records = []
    all_model, all_persistence, all_climatology = [], [], []
    coverages, widths = [], []
    for train, val, meta in spatiotemporal_folds(frame, n_folds=n_folds):
        model, scaler = fit_quantile_model(train, epochs=epochs)
        predictions = predict_quantiles(model, scaler, val)
        actual = val["fai_future"].to_numpy(dtype=float)
        median = predictions[:, 1]
        model_mae = float(mean_absolute_error(actual, median))
        persistence_mae = float(mean_absolute_error(actual, val["fai_now"]))
        climatology_mae = float(mean_absolute_error(actual, val["baseline_mean"]))
        coverage = float(((actual >= predictions[:, 0]) & (actual <= predictions[:, 2])).mean())
        width = float(np.mean(predictions[:, 2] - predictions[:, 0]))
        all_model.append(model_mae)
        all_persistence.append(persistence_mae)
        all_climatology.append(climatology_mae)
        coverages.append(coverage)
        widths.append(width)
        fold_records.append(
            {
                **meta,
                "mae_fai": round(model_mae, 6),
                "persistence_mae_fai": round(persistence_mae, 6),
                "climatology_mae_fai": round(climatology_mae, 6),
                "q10_q90_coverage": round(coverage, 4),
            }
        )

    mae = float(np.mean(all_model))
    persistence = float(np.mean(all_persistence))
    climatology = float(np.mean(all_climatology))
    final_model, final_scaler = fit_quantile_model(frame, epochs=epochs)
    dates = pd.to_datetime(frame["date"])
    metrics = {
        "version": "per-pixel-quantile-mlp-v1",
        "signal": "per-pixel FAI with ERA5-Land change drivers",
        "target": "standardised causal anomaly of per-pixel FAI at the horizon",
        "target_kind": "continuous",
        "fai_alert_threshold": None,
        "classification": None,
        # Rendered verbatim in the Spanish UI (ModelView candidate panel).
        "classification_reason": (
            "No se hornea ningún umbral de alerta en el entrenamiento; el umbral "
            "de política queda aguas abajo (MI-3)."
        ),
        "n_pairs": len(frame),
        "n_pixels": int(frame["pixel_id"].nunique()),
        "n_anchor_dates": int(frame["date"].nunique()),
        "date_range": {"start": dates.min().date().isoformat(), "end": dates.max().date().isoformat()},
        "features_used": list(FEATURES),
        "quantiles": list(QUANTILES),
        "training": {"framework": "PyTorch", "epochs": epochs, "seed": SEED},
        "cv": {
            "scheme": "expanding-window target-date embargo + rotating 2x2 spatial holdout",
            "n_folds": n_folds,
            "folds": fold_records,
        },
        "metrics": {
            "mae_fai": round(mae, 6),
            "mae_fai_cv_std": round(float(np.std(all_model)), 6),
            "q10_q90_coverage": round(float(np.mean(coverages)), 4),
            "mean_interval_width_fai": round(float(np.mean(widths)), 6),
            "precision": None,
            "recall": None,
            "f1_score": None,
            "auc_roc": None,
        },
        "baselines": {
            "persistence": {"rule": "fai_future == fai_now", "mae_fai": round(persistence, 6)},
            "climatology": {
                "rule": "fai_future == causal per-pixel baseline mean",
                "mae_fai": round(climatology, 6),
            },
        },
        "beats_baselines": {
            "persistence": bool(mae < persistence),
            "climatology": bool(mae < climatology),
        },
        # Rendered verbatim in the Spanish UI (ModelView candidate panel), so it
        # is written in Spanish -- same rule as classification_reason above.
        "caveats": (
            "TRL 2 — no validado en campo. Las filas de píxeles están "
            "autocorrelacionadas espacialmente y no son muestras independientes. Las "
            "métricas usan embargo por fecha objetivo y regiones 2x2 del lago dejadas "
            "afuera. ERA5-Land es una media gruesa sobre el bounding box, y las fechas "
            "ancla/objetivo superpuestas todavía inducen dependencia residual temporal "
            "(BL-033)."
        ),
    }
    artifact = {
        "state_dict": final_model.state_dict(),
        # Tensors, not the scaler's numpy arrays. torch.load defaults to
        # weights_only=True from 2.6 on, and that unpickler rejects numpy
        # arrays -- which would force every reader to opt back into arbitrary
        # code execution just to read our own scaler. Storing tensors keeps the
        # artifact loadable under the safe default. See per_pixel_infer.py.
        "feature_mean": torch.as_tensor(final_scaler.mean, dtype=torch.float64),
        "feature_scale": torch.as_tensor(final_scaler.scale, dtype=torch.float64),
        "features": list(FEATURES),
        "quantiles": list(QUANTILES),
    }
    return {"model": final_model, "scaler": final_scaler, "artifact": artifact, "metrics": metrics}

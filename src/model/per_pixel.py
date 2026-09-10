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


def fit_quantile_model(
    train: pd.DataFrame,
    *,
    epochs: int = 80,
    batch_size: int = 2048,
    learning_rate: float = 1e-3,
) -> tuple[QuantileMLP, FeatureScaler]:
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    values = train[list(FEATURES)].to_numpy(dtype=np.float32)
    scaler = FeatureScaler.fit(values)
    inputs = torch.from_numpy(scaler.transform(values).astype(np.float32))
    target = torch.from_numpy(train[TARGET].to_numpy(dtype=np.float32))
    dataset = TensorDataset(inputs, target)
    generator = torch.Generator().manual_seed(SEED)
    loader = DataLoader(
        dataset,
        batch_size=min(batch_size, len(dataset)),
        shuffle=True,
        generator=generator,
    )

    model = QuantileMLP()
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    model.train()
    for _ in range(epochs):
        for batch_inputs, batch_target in loader:
            optimizer.zero_grad()
            loss = pinball_loss(model(batch_inputs), batch_target)
            loss.backward()
            optimizer.step()
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
        "classification_reason": "No alert threshold is baked into training; policy threshold remains downstream (MI-3).",
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
        "caveats": (
            "TRL 2 — not validated in the field. Pixel rows are spatially autocorrelated and are not "
            "independent samples. Metrics use target-date embargo and held-out 2x2 lake regions. "
            "ERA5-Land is a coarse bbox mean, and overlapping anchor/target dates still induce "
            "temporal residual dependence (BL-033)."
        ),
    }
    artifact = {
        "state_dict": final_model.state_dict(),
        "feature_mean": final_scaler.mean,
        "feature_scale": final_scaler.scale,
        "features": list(FEATURES),
        "quantiles": list(QUANTILES),
    }
    return {"model": final_model, "scaler": final_scaler, "artifact": artifact, "metrics": metrics}

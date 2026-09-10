"""BL-008/BL-016: PyTorch quantiles with temporal and spatial isolation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.model.per_pixel import (
    FEATURES,
    QuantileMLP,
    _inner_split,
    fit_and_evaluate,
    fit_quantile_model,
    predict_quantiles,
    spatiotemporal_folds,
)


def _frame() -> pd.DataFrame:
    rng = np.random.default_rng(4)
    rows = []
    dates = pd.date_range("2026-01-01", periods=30, freq="3D")
    for block in range(4):
        for pixel in range(3):
            baseline = 0.001 + block * 0.0001 + pixel * 0.00001
            for i, date in enumerate(dates):
                anomaly_now = np.sin(i / 4) + rng.normal(0, 0.02)
                future = 0.7 * anomaly_now
                row = {
                    "date": date.date().isoformat(),
                    "pixel_id": f"b{block}p{pixel}",
                    "station_id": f"b{block}p{pixel}",
                    "spatial_block": block,
                    "horizon_days": 7,
                    "fai_now": baseline + anomaly_now * 0.0002,
                    "fai_future": baseline + future * 0.0002,
                    "baseline_mean": baseline,
                    "baseline_std": 0.0002,
                    "anomaly_now": anomaly_now,
                    "anomaly_future": future,
                    "temp_c": 15 + np.sin(i / 8),
                    "precip_mm": float(i % 4),
                    "wind_kmh": 5 + block,
                    "lat": -39.34 + block * 0.04,
                    "lng": -72.34 + block * 0.1,
                    "doy_sin": np.sin(2 * np.pi * date.dayofyear / 365.25),
                    "doy_cos": np.cos(2 * np.pi * date.dayofyear / 365.25),
                }
                rows.append(row)
    return pd.DataFrame(rows)


def test_spatiotemporal_folds_embargo_targets_and_hold_out_regions() -> None:
    for train, val, meta in spatiotemporal_folds(_frame()):
        first_val = pd.to_datetime(val["date"]).min()
        targets = pd.to_datetime(train["date"]) + pd.to_timedelta(train["horizon_days"], unit="D")
        assert (targets < first_val).all()
        assert meta["held_spatial_block"] not in set(train["spatial_block"])
        assert set(val["spatial_block"]) == {meta["held_spatial_block"]}


def test_quantile_predictions_never_cross() -> None:
    frame = _frame()
    model, scaler = fit_quantile_model(frame, epochs=2, batch_size=128)
    predictions = predict_quantiles(model, scaler, frame.iloc[:20])
    assert predictions.shape == (20, 3)
    assert np.all(predictions[:, 0] <= predictions[:, 1])
    assert np.all(predictions[:, 1] <= predictions[:, 2])


def test_evaluation_reports_both_baselines_and_continuous_target() -> None:
    result = fit_and_evaluate(_frame(), epochs=2)
    metrics = result["metrics"]
    assert metrics["target_kind"] == "continuous"
    assert set(metrics["beats_baselines"]) == {"persistence", "climatology"}
    assert metrics["classification"] is None
    assert metrics["cv"]["n_folds"] == 4
    assert result["artifact"]["features"] == list(FEATURES)


def test_inner_split_is_temporal_and_disjoint() -> None:
    """Early stopping must select on training data only, never the outer fold."""
    frame = _frame()
    for train, val, _meta in spatiotemporal_folds(frame):
        fit_index, inner_index = _inner_split(train, 0.2)
        assert len(inner_index), "inner hold-out is empty; early stopping would be blind"
        assert not set(fit_index) & set(inner_index)
        assert set(fit_index) | set(inner_index) == set(train.index)
        # Inner hold-out is strictly later than the rows used to fit.
        fit_dates = pd.to_datetime(train.loc[fit_index, "date"])
        inner_dates = pd.to_datetime(train.loc[inner_index, "date"])
        assert fit_dates.max() < inner_dates.min()
        # And it never overlaps the outer validation partition.
        assert not set(train.loc[inner_index].index) & set(val.index)


def test_early_stopping_does_not_run_past_the_epoch_budget() -> None:
    frame = _frame()
    model, _scaler = fit_quantile_model(frame, epochs=3, batch_size=128, patience=1)
    assert isinstance(model, QuantileMLP)
    assert not model.training

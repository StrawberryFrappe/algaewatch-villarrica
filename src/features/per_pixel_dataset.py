"""Build the honest per-pixel anomaly table adopted by ADR 0004 D1-D4."""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import LAKE_BBOX
from .lake_anomaly import DEFAULT_MIN_PRIOR, build_anomaly_pairs


def add_spatial_blocks(frame: pd.DataFrame) -> pd.DataFrame:
    """Assign fixed 2x2 lake regions for spatial hold-out validation."""
    min_lon, min_lat, max_lon, max_lat = LAKE_BBOX
    lon_mid = (min_lon + max_lon) / 2
    lat_mid = (min_lat + max_lat) / 2
    out = frame.copy()
    east = (out["lng"] >= lon_mid).astype(int)
    north = (out["lat"] >= lat_mid).astype(int)
    out["spatial_block"] = (north * 2 + east).astype(int)
    return out


def build_per_pixel_dataset(
    grid: pd.DataFrame,
    weather: pd.DataFrame,
    *,
    min_prior: int = DEFAULT_MIN_PRIOR,
) -> pd.DataFrame:
    """Pair real pixel passes, attach causal baselines and observed weather.

    No row is interpolated or forward-filled. Weather is joined only on the
    real anchor pass date; a missing measurement aborts the build.
    """
    required_grid = {"date", "pixel_id", "lat", "lng", "fai"}
    required_weather = {"date", "temp_c", "precip_mm", "wind_kmh"}
    if missing := required_grid - set(grid.columns):
        raise ValueError(f"Grid missing columns: {sorted(missing)}")
    if missing := required_weather - set(weather.columns):
        raise ValueError(f"Weather missing columns: {sorted(missing)}")

    coordinate_counts = grid.groupby("pixel_id")[["lat", "lng"]].nunique()
    if (coordinate_counts > 1).any().any():
        raise ValueError("pixel_id coordinates are not stable across passes")

    pairs = build_anomaly_pairs(
        grid,
        value_col="fai",
        unit_col="pixel_id",
        min_prior=min_prior,
    ).rename(columns={"station_id": "pixel_id"})
    pairs["station_id"] = pairs["pixel_id"]  # gate-compatible spatial unit

    coords = grid[["pixel_id", "lat", "lng"]].drop_duplicates("pixel_id")
    out = pairs.merge(coords, on="pixel_id", how="left", validate="many_to_one")
    weather_clean = weather[list(required_weather)].drop_duplicates("date")
    out = out.merge(weather_clean, on="date", how="left", validate="many_to_one")

    dates = pd.to_datetime(out["date"])
    angle = 2 * np.pi * dates.dt.dayofyear / 365.25
    out["doy_sin"] = np.sin(angle)
    out["doy_cos"] = np.cos(angle)
    out = add_spatial_blocks(out)

    required_values = [
        "fai_now",
        "fai_future",
        "baseline_mean",
        "baseline_std",
        "anomaly_now",
        "anomaly_future",
        "lat",
        "lng",
        "temp_c",
        "precip_mm",
        "wind_kmh",
    ]
    if out[required_values].isna().any().any():
        missing_rows = int(out[required_values].isna().any(axis=1).sum())
        raise ValueError(f"Per-pixel table has {missing_rows} rows with missing measurements")
    return out.sort_values(["date", "pixel_id"], kind="stable").reset_index(drop=True)

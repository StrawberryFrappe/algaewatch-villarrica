"""Focused tests for the per-pixel and ERA5 backfill seams."""

from __future__ import annotations

import zipfile

import numpy as np
import pandas as pd
import pytest
import xarray as xr

from src.features.era5 import _precip_path, load_daily_means, load_era5_dates
from src.features.fai import FaiRaster
from src.features.per_pixel_dataset import build_per_pixel_dataset


def test_sample_grid_pixel_ids_are_stable_raster_coordinates() -> None:
    fai = np.arange(16, dtype=float).reshape(4, 4) / 1000
    water = np.ones((4, 4), dtype=bool)
    raster = FaiRaster(fai, water, (-72.0, -39.0, -71.0, -38.0), 4, 4)

    first = raster.sample_grid(stride_px=2, include_pixel_id=True)
    second = raster.sample_grid(stride_px=2, include_pixel_id=True)

    assert [p["pixel_id"] for p in first] == [
        "r0000_c0000",
        "r0000_c0002",
        "r0002_c0000",
        "r0002_c0002",
    ]
    assert first == second


def test_load_daily_means_combines_daily_fields_and_hourly_precipitation(tmp_path) -> None:
    daily_zip = tmp_path / "era5_land_2026-08-22_daily_mean.zip"
    nc_dir = tmp_path / "nc"
    nc_dir.mkdir()

    fields = {
        "temperature.nc": ("t2m", np.full((1, 2, 2), 280.0)),
        "u.nc": ("u10", np.full((1, 2, 2), 3.0)),
        "v.nc": ("v10", np.full((1, 2, 2), 4.0)),
    }
    for filename, (name, values) in fields.items():
        xr.Dataset(
            {name: (("valid_time", "latitude", "longitude"), values)},
            coords={"valid_time": [0], "latitude": [0, 1], "longitude": [0, 1]},
        ).to_netcdf(nc_dir / filename)
    with zipfile.ZipFile(daily_zip, "w") as archive:
        for path in nc_dir.glob("*.nc"):
            archive.write(path, path.name)

    # Four hourly steps at 0.1 mm each after converting metres to mm.
    xr.Dataset(
        {
            "tp": (
                ("valid_time", "latitude", "longitude"),
                np.full((4, 2, 2), 0.0001),
            )
        },
        coords={"valid_time": range(4), "latitude": [0, 1], "longitude": [0, 1]},
    ).to_netcdf(_precip_path(daily_zip))

    values = load_daily_means(daily_zip)

    assert values["temp_c"] == pytest.approx(6.85)
    assert values["wind_kmh"] == pytest.approx(18.0)
    assert values["precip_mm"] == pytest.approx(0.4)


def test_hourly_era5_file_is_aggregated_by_utc_day(tmp_path) -> None:
    hourly = tmp_path / "era5_land_2026-08_hourly.nc"
    times = pd.date_range("2026-08-21", periods=49, freq="h")
    shape = (len(times), 2, 2)
    cumulative_precip = np.zeros(shape)
    cumulative_precip[24] = 0.0024
    cumulative_precip[48] = 0.0048
    xr.Dataset(
        {
            "t2m": (("valid_time", "latitude", "longitude"), np.full(shape, 280.0)),
            "u10": (("valid_time", "latitude", "longitude"), np.full(shape, 3.0)),
            "v10": (("valid_time", "latitude", "longitude"), np.full(shape, 4.0)),
            "tp": (("valid_time", "latitude", "longitude"), cumulative_precip),
        },
        coords={"valid_time": times, "latitude": [0, 1], "longitude": [0, 1]},
    ).to_netcdf(hourly)

    frame = load_era5_dates(hourly)

    assert frame["date"].tolist() == ["2026-08-21", "2026-08-22"]
    assert frame["temp_c"].tolist() == pytest.approx([6.85, 6.85])
    assert frame["wind_kmh"].tolist() == pytest.approx([18.0, 18.0])
    assert frame["precip_mm"].tolist() == pytest.approx([2.4, 4.8])


def test_per_pixel_dataset_uses_real_pairs_and_joins_weather() -> None:
    dates = pd.date_range("2026-01-01", periods=16, freq="3D")
    grid_rows = []
    for pixel_id, lat, lng, offset in (
        ("p1", -39.21, -72.34, 0.0),
        ("p2", -39.34, -71.96, 0.001),
    ):
        for i, date in enumerate(dates):
            grid_rows.append(
                {
                    "date": date.date().isoformat(),
                    "pixel_id": pixel_id,
                    "lat": lat,
                    "lng": lng,
                    "fai": offset + i * 0.0001,
                }
            )
    weather = pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in dates],
            "temp_c": np.linspace(10, 15, len(dates)),
            "precip_mm": np.linspace(0, 2, len(dates)),
            "wind_kmh": np.linspace(4, 8, len(dates)),
        }
    )

    out = build_per_pixel_dataset(pd.DataFrame(grid_rows), weather, min_prior=3)

    assert set(out["pixel_id"]) == {"p1", "p2"}
    assert (out["station_id"] == out["pixel_id"]).all()
    assert out[["temp_c", "precip_mm", "wind_kmh"]].notna().all().all()
    assert set(out["spatial_block"]) == {1, 2}
    assert len(out.drop_duplicates(["pixel_id", "fai_now", "fai_future"])) == len(out)

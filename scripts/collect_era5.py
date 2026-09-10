"""Backfill ERA5-Land features for every real Sentinel-2 pass date.

Run from the project root:
    .venv/bin/python scripts/collect_era5.py

Raw NetCDF/zip downloads are resumable and ignored by Git. The compact daily
table is committed so model evaluation remains credential-free.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.era5 import collect_era5_days  # noqa: E402

FAI_SERIES = ROOT / "data" / "processed" / "fai_series_raw.csv"
OUT_PATH = ROOT / "data" / "processed" / "era5_daily.csv"


def main() -> int:
    fai = pd.read_csv(FAI_SERIES)
    dates = sorted(pd.to_datetime(fai["date"]).dt.date.astype(str).unique())
    print(f"Fetching ERA5-Land for {len(dates)} real Sentinel-2 pass dates...")
    weather = collect_era5_days(dates)
    if len(weather) != len(dates) or weather.isna().any().any():
        raise RuntimeError("ERA5 backfill is incomplete; refusing to write a partial table")
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    weather.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(weather)} rows to {OUT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

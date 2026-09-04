"""Fetches the most recent clear Sentinel-2 scene and saves a downsampled FAI
grid across the whole lake surface, for the map's real heatmap overlay
(replacing the 4-station-point interpolation placeholder).

This grid reflects ONE satellite pass (the latest available), not a time
series — re-run this script whenever a newer clear pass should replace it
(Sentinel-2 revisits the lake roughly every 5 days).

Run from the project root: .venv/bin/python scripts/collect_fai_grid.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.features.build_dataset import find_clear_dates
from src.features.fai import fetch_fai_raster

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "fai_grid_latest.csv"

if __name__ == "__main__":
    dates = find_clear_dates("2026-06-01", "2026-09-04", max_cloud_cover=15)
    if not dates:
        print("No clear dates found in the fallback window — widen the search range.")
        sys.exit(1)
    latest = dates[-1]
    print(f"Using latest clear date: {latest}")

    raster = fetch_fai_raster(latest)
    points = raster.sample_grid(stride_px=15)
    print(f"Sampled {len(points)} water-pixel grid points")

    df = pd.DataFrame(points)
    df["date"] = latest
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved to {OUT_PATH}")

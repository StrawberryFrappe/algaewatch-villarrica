"""One-off collection script: fetches real FAI for the clear-sky dates found
in the last year and saves the raw series to data/processed/. Run from the
project root: .venv/bin/python scripts/collect_fai.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.features.build_dataset import collect_fai_series, find_clear_dates

OUT_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "fai_series_raw.csv"

if __name__ == "__main__":
    dates = find_clear_dates("2025-09-01", "2026-09-04", max_cloud_cover=15)
    print(f"{len(dates)} clear dates found, fetching FAI for each...")
    df = collect_fai_series(dates)
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_PATH, index=False)
    print(f"Saved {len(df)} rows to {OUT_PATH}")

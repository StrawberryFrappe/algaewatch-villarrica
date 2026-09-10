"""Backfill a stable per-pixel FAI grid across all committed pass dates.

Run from the project root:
    .venv/bin/python scripts/collect_fai_grid_series.py

No temporal interpolation or forward-fill is performed. Each output row is a
real water-pixel measurement from one Sentinel-2 pass (PR-3).
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.fai import fetch_fai_raster  # noqa: E402

FAI_SERIES = ROOT / "data" / "processed" / "fai_series_raw.csv"
OUT_PATH = ROOT / "data" / "processed" / "fai_grid_series.csv"


def main() -> int:
    pass_dates = sorted(
        pd.to_datetime(pd.read_csv(FAI_SERIES)["date"]).dt.date.astype(str).unique()
    )
    existing = pd.read_csv(OUT_PATH) if OUT_PATH.exists() else pd.DataFrame()
    completed = set(existing["date"].astype(str)) if not existing.empty else set()
    frames = [existing] if not existing.empty else []

    for pos, date_iso in enumerate(pass_dates, start=1):
        if date_iso in completed:
            print(f"  [cached {pos}/{len(pass_dates)}] {date_iso}")
            continue
        raster = fetch_fai_raster(date_iso)
        frame = pd.DataFrame(raster.sample_grid(stride_px=15, include_pixel_id=True))
        frame["date"] = date_iso
        frames.append(frame)
        # Checkpoint after every remote request so a quota/network interruption
        # never discards earlier real measurements.
        combined = pd.concat(frames, ignore_index=True)
        combined = combined.drop_duplicates(["date", "pixel_id"]).sort_values(
            ["date", "pixel_id"], kind="stable"
        )
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        combined.to_csv(OUT_PATH, index=False)
        print(f"  [ok {pos}/{len(pass_dates)}] {date_iso}: {len(frame)} water pixels")

    final = pd.read_csv(OUT_PATH)
    missing = sorted(set(pass_dates) - set(final["date"].astype(str)))
    if missing:
        raise RuntimeError(f"Grid backfill incomplete; missing {len(missing)} dates")
    print(
        f"Saved {len(final)} real pixel-pass rows across "
        f"{final['date'].nunique()} dates to {OUT_PATH.relative_to(ROOT)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

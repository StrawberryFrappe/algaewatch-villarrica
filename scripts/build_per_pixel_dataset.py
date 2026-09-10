"""Build the credential-free per-pixel training table from collected inputs."""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.per_pixel_dataset import build_per_pixel_dataset  # noqa: E402

GRID = ROOT / "data" / "processed" / "fai_grid_series.csv"
WEATHER = ROOT / "data" / "processed" / "era5_daily.csv"
OUT = ROOT / "data" / "processed" / "per_pixel_anomaly_dataset.csv"


def main() -> int:
    frame = build_per_pixel_dataset(pd.read_csv(GRID), pd.read_csv(WEATHER))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(OUT, index=False)
    print(
        f"Saved {len(frame)} honest pairs from {frame['pixel_id'].nunique()} pixels "
        f"and {frame['date'].nunique()} anchors to {OUT.relative_to(ROOT)}"
    )
    print("Spatial blocks:", frame.groupby("spatial_block").size().to_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

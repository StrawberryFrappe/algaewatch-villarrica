"""Run the trained per-pixel quantile model over the latest anchor date and
persist a compact per-station forecast table for the backend.

This is the serving counterpart to `train_per_pixel.py`. It keeps model code off
the request path: the backend reads the small CSV this writes, exactly as it
already reads `fai_series_raw.csv` and `fai_grid_latest.csv`, rather than loading
PyTorch and scoring ~1,800 pixels inside a request.

The candidate is a *forecast* model with no present-state reading, and its newest
anchor date is fixed by the dataset (2026-08-17 at the time of writing). So the
table it writes is a single projection — "the latest candidate forecast" — not a
per-date series. `/risk` and `/risk/grid`, which drive the map, are untouched by
this and stay on the legacy path.

Aggregation is presentation only: per-pixel FAI quantiles are averaged over the
`NEAREST_PIXELS` water pixels closest to each dashboard station, so a station card
reads "the water around this station" rather than a quarter of the lake. Note the
dataset's own `station_id` column is the per-pixel training unit (it equals
`pixel_id` under ADR 0004 D3) and is *not* a dashboard station, so the assignment
is done here from coordinates against `src/features/stations.py`.

Two of the four station coordinates are admitted placeholders sitting off the
water (BL-027 / ADR-sf-0007); their nearest water pixels are therefore
shoreline-adjacent. That limitation is inherited from the station catalog, not
introduced here.

No retraining, no relabelling. The candidate still loses to its baselines (MI-1)
and the dashboard still says so.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.stations import STATIONS  # noqa: E402
from src.model import per_pixel_infer  # noqa: E402

DATASET = ROOT / "data" / "processed" / "per_pixel_anomaly_dataset.csv"
OUTPUT = ROOT / "data" / "processed" / "per_pixel_forecast_latest.csv"

# How many nearest water pixels represent a station. Small enough to stay local
# to the station, large enough that one noisy pixel cannot swing the card.
NEAREST_PIXELS = 25

COLUMNS = [
    "station_id",
    "anchor_date",
    "target_date",
    "horizon_days",
    "fai_q10",
    "fai_q50",
    "fai_q90",
    "n_pixels",
]


def _nearest_pixels(rows: pd.DataFrame, lat: float, lng: float, k: int) -> pd.DataFrame:
    """The k rows closest to (lat, lng).

    Equirectangular approximation — over a 30 km lake at 39°S the error against a
    great-circle distance is far below the 300 m pixel grid, and only the
    *ordering* matters here.
    """
    dlat = rows["lat"].to_numpy() - lat
    dlng = (rows["lng"].to_numpy() - lng) * np.cos(np.radians(lat))
    order = np.argsort(dlat * dlat + dlng * dlng)[:k]
    return rows.iloc[order]


def build_forecast(frame: pd.DataFrame) -> pd.DataFrame:
    """Predict the latest anchor date and aggregate onto the dashboard stations.

    Returns one row per station plus a `lake` row over every predicted pixel.
    """
    anchor = frame["date"].max()
    rows = frame[frame["date"] == anchor].copy()
    if rows.empty:
        raise ValueError(f"No rows for anchor date {anchor}")

    quantiles = per_pixel_infer.predict_fai_quantiles(rows)
    rows[["fai_q10", "fai_q50", "fai_q90"]] = quantiles

    # horizon_days can vary row to row; the median describes the batch honestly.
    horizon = int(rows["horizon_days"].median())
    target = (pd.Timestamp(anchor) + pd.Timedelta(days=horizon)).date().isoformat()

    records = []
    for station in STATIONS:
        near = _nearest_pixels(rows, station.lat, station.lng, NEAREST_PIXELS)
        records.append({
            "station_id": station.id,
            "fai_q10": float(near["fai_q10"].mean()),
            "fai_q50": float(near["fai_q50"].mean()),
            "fai_q90": float(near["fai_q90"].mean()),
            "n_pixels": int(near["pixel_id"].nunique()),
        })

    records.append({
        "station_id": "lake",
        "fai_q10": float(rows["fai_q10"].mean()),
        "fai_q50": float(rows["fai_q50"].mean()),
        "fai_q90": float(rows["fai_q90"].mean()),
        "n_pixels": int(rows["pixel_id"].nunique()),
    })

    out = pd.DataFrame(records)
    out["anchor_date"] = anchor
    out["target_date"] = target
    out["horizon_days"] = horizon
    return out[COLUMNS]


def main() -> int:
    if not DATASET.exists():
        print(f"{DATASET} not found — run scripts/build_per_pixel_dataset.py first.")
        return 1

    frame = pd.read_csv(DATASET)
    try:
        out = build_forecast(frame)
    except per_pixel_infer.PerPixelNotTrainedError as exc:
        print(exc)
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUTPUT, index=False)

    anchor = out["anchor_date"].iloc[0]
    target = out["target_date"].iloc[0]
    print(f"Anchor {anchor} -> target {target} ({out['horizon_days'].iloc[0]} d)")
    for row in out.itertuples():
        print(
            f"  {row.station_id:<8} q50 {row.fai_q50: .6f}  "
            f"[q10 {row.fai_q10: .6f}, q90 {row.fai_q90: .6f}]  "
            f"{row.n_pixels} px"
        )
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")
    print(
        "Reminder: this candidate does not beat persistence or climatology "
        "(rule MI-1). It is served beside that verdict, never instead of it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

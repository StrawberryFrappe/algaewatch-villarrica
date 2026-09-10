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
    "alert_threshold",
]

# Percentile of the observed per-pixel water FAI distribution used as the
# candidate's alert threshold.
#
# The legacy `fai_alert_threshold` (0.025916) cannot be reused here. It was
# calibrated on station-point FAI, and two of the four station coordinates sit
# off the water on shoreline vegetation (BL-027), whose FAI is naturally an
# order of magnitude higher than open water. Against real per-pixel water values
# — p50 0.000, p95 0.0021, p99 0.0038 — that constant sits ~6.6x above the p99,
# so every prediction collapses to the bottom of the risk scale and the entire
# risk surface goes vacuous. ADR-sf-0008 recorded this in advance.
#
# p99 flags roughly 1% of water-pixel observations. The dates where the largest
# share of the lake exceeds it are all austral summer (19 Jan, 8 Mar, 5 Mar,
# 25 Dec), which is when cyanobacteria actually bloom here — a sanity check that
# it tracks the phenomenon rather than sensor noise.
#
# This is a DISTRIBUTIONAL threshold, not a validated bloom threshold. There is
# no in-situ data to calibrate against (PR-3). It says "in the top 1% of FAI
# observed on this lake", not "above a concentration known to be harmful", and
# the API and UI must not present it as the latter. Applied at serving time
# only, never in training, per rule MI-3.
ALERT_PERCENTILE = 99.0


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
    """Predict every anchor date and aggregate onto the dashboard stations.

    Returns one row per (anchor date, station) plus a `lake` row per anchor.

    Every anchor is emitted, not only the newest, so the backend can serve the
    projection appropriate to the date the user has selected. Emitting only the
    latest anchor pinned the whole dashboard to 2026-08-17 — austral winter, when
    predicted FAI is near zero at any threshold — which made the risk scale look
    broken rather than seasonal.
    """
    rows = frame.copy()
    quantiles = per_pixel_infer.predict_fai_quantiles(rows)
    rows[["fai_q10", "fai_q50", "fai_q90"]] = quantiles

    threshold = float(np.percentile(frame["fai_future"].dropna(), ALERT_PERCENTILE))

    records = []
    for anchor, group in rows.groupby("date", sort=True):
        # horizon_days varies row to row (the real gap between Sentinel-2
        # passes); the median describes the batch honestly.
        horizon = int(group["horizon_days"].median())
        target = (pd.Timestamp(anchor) + pd.Timedelta(days=horizon)).date().isoformat()
        common = {"anchor_date": anchor, "target_date": target, "horizon_days": horizon}

        for station in STATIONS:
            near = _nearest_pixels(group, station.lat, station.lng, NEAREST_PIXELS)
            records.append({
                **common,
                "station_id": station.id,
                "fai_q10": float(near["fai_q10"].mean()),
                "fai_q50": float(near["fai_q50"].mean()),
                "fai_q90": float(near["fai_q90"].mean()),
                "n_pixels": int(near["pixel_id"].nunique()),
            })

        records.append({
            **common,
            "station_id": "lake",
            "fai_q10": float(group["fai_q10"].mean()),
            "fai_q50": float(group["fai_q50"].mean()),
            "fai_q90": float(group["fai_q90"].mean()),
            "n_pixels": int(group["pixel_id"].nunique()),
        })

    out = pd.DataFrame(records)
    out["alert_threshold"] = threshold
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

    threshold = out["alert_threshold"].iloc[0]
    anchors = out["anchor_date"].nunique()
    print(f"{anchors} anchor dates, {len(out)} rows")
    print(f"Alert threshold (p{ALERT_PERCENTILE:g} of observed water FAI): {threshold:.6f}")
    print("Distributional, not a validated bloom threshold -- no in-situ data exists (PR-3).")
    print()

    lake = out[out["station_id"] == "lake"].sort_values("fai_q50", ascending=False)
    print("Highest predicted lake-mean FAI by anchor:")
    for row in lake.head(5).itertuples():
        ratio = row.fai_q50 / threshold if threshold else 0
        print(
            f"  {row.anchor_date} -> {row.target_date}  q50 {row.fai_q50: .6f}  "
            f"({ratio * 100:5.1f}% of threshold)"
        )
    print(f"\nWrote {OUTPUT.relative_to(ROOT)}")
    print(
        "Reminder: this candidate does not beat persistence or climatology "
        "(rule MI-1). It is served beside that verdict, never instead of it."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

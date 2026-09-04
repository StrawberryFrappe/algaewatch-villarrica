"""Orchestrates the unified, per-date feature table: FAI history + ERA5-Land +
in-situ -> target (bloom risk 7 days ahead). Pure feature engineering — this
module builds the training TABLE; it must never import from src/model.

Each data source is optional at call time so the pipeline degrades instead of
crashing while a source is unavailable (ERA5 pending CDS licence acceptance;
in-situ pending real SNIA CSVs — see era5.py and insitu.py for why).
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd
from sentinelhub import BBox, CRS, SentinelHubCatalog

from .config import LAKE_BBOX, sentinelhub_config
from .fai import fetch_fai_raster
from .stations import STATION_IDS, STATIONS_BY_ID

STATION_COORDS = {s.id: (s.lat, s.lng) for s in STATIONS_BY_ID.values()}


def find_clear_dates(start_date: str, end_date: str, max_cloud_cover: float = 20.0) -> list[str]:
    """Calendar dates with a Sentinel-2 L2A pass over the lake at or below the
    given cloud cover, one entry per date (deduped across overlapping tiles).
    """
    config = sentinelhub_config()
    catalog = SentinelHubCatalog(config=config)
    bbox = BBox(LAKE_BBOX, crs=CRS.WGS84)

    results = catalog.search(
        "sentinel-2-l2a",
        bbox=bbox,
        time=(start_date, end_date),
        fields={"include": ["properties.datetime", "properties.eo:cloud_cover"], "exclude": []},
    )

    best_by_date: dict[str, float] = {}
    for item in results:
        day = item["properties"]["datetime"][:10]
        cc = item["properties"].get("eo:cloud_cover", 100.0)
        if day not in best_by_date or cc < best_by_date[day]:
            best_by_date[day] = cc

    return sorted(d for d, cc in best_by_date.items() if cc <= max_cloud_cover)


def collect_fai_series(dates: list[str]) -> pd.DataFrame:
    """Fetches + computes FAI for each date. One row per date, one column per
    station plus the lake-wide mean. Skips dates that fail (logs a warning)
    instead of aborting the whole collection.
    """
    rows = []
    for d in dates:
        try:
            raster = fetch_fai_raster(d)
        except Exception as exc:  # noqa: BLE001 — collection continues past bad scenes
            print(f"  [warn] skipping {d}: {exc}")
            continue
        row = {"date": d, "lake_mean_fai": raster.lake_mean()}
        for station_id, (lat, lon) in STATION_COORDS.items():
            row[f"fai_{station_id}"] = raster.at_latlon(lat, lon)
        rows.append(row)
        print(f"  [ok] {d}: lake_mean_fai={row['lake_mean_fai']:.4f}")
    return pd.DataFrame(rows)


def calibrate_bloom_threshold(fai_values: np.ndarray, fallback: float = 0.05) -> float:
    """Calibrates the bloom-alert FAI threshold from the histogram of observed
    values (2-component Gaussian mixture midpoint), per the project's
    requirement to calibrate on real lake data rather than copy a literature
    value. Falls back to a conservative default when the sample is too small
    or too homogeneous for a reliable bimodal fit (logged, never silent).
    """
    valid = fai_values[~np.isnan(fai_values)]
    if valid.size < 30:
        print(f"  [warn] only {valid.size} FAI observations — too few to calibrate a "
              f"bimodal threshold reliably; using fallback={fallback}")
        return fallback

    from sklearn.mixture import GaussianMixture

    gmm = GaussianMixture(n_components=2, random_state=0).fit(valid.reshape(-1, 1))
    means = sorted(gmm.means_.flatten())
    threshold = float(np.mean(means))
    print(f"  [ok] calibrated bloom threshold from {valid.size} observations: {threshold:.4f}")
    return threshold


def build_daily_series(fai_df: pd.DataFrame, end_date: str | None = None) -> dict[str, pd.Series]:
    """Forward-fills each station's sparse FAI observations onto a daily grid
    (the last known FAI holds until the next Sentinel-2 pass — a standard
    assumption for satellite-derived indices, ~5-day revisit cadence).

    end_date extends the grid past the last observed pass (e.g. to "today"),
    still holding the last known value — used by the backend to serve current
    state without needing a live satellite fetch on every request.

    Returns {station_id: pd.Series indexed by daily pd.Timestamp}, plus a
    "lake" key for the lake-wide mean if that column is present.
    """
    fai_df = fai_df.copy()
    fai_df["date"] = pd.to_datetime(fai_df["date"])
    fai_df = fai_df.sort_values("date").set_index("date")

    start = fai_df.index.min()
    end = pd.to_datetime(end_date) if end_date else fai_df.index.max()
    all_days = pd.date_range(start, max(end, fai_df.index.max()), freq="D")

    series = {}
    for station_id in STATION_IDS:
        col = f"fai_{station_id}"
        if col in fai_df.columns:
            series[station_id] = fai_df[col].reindex(all_days).ffill()
    if "lake_mean_fai" in fai_df.columns:
        series["lake"] = fai_df["lake_mean_fai"].reindex(all_days).ffill()
    return series


def build_unified_dataset(
    fai_df: pd.DataFrame,
    horizon_days: int = 7,
    lookback_days: tuple[int, ...] = (1, 3, 7),
    bloom_threshold: float | None = None,
) -> tuple[pd.DataFrame, float]:
    """Builds the per-station, per-day training table.

    FAI is sparse (one Sentinel-2 pass every ~5 days); this forward-fills each
    station's series onto a daily grid (the last known FAI holds until the
    next pass — a standard assumption for satellite-derived indices) before
    computing lag/window features and the horizon_days-ahead target.
    """
    daily_series = build_daily_series(fai_df)
    all_days = next(iter(daily_series.values())).index

    station_frames = []
    all_fai_values = []
    for station_id in STATION_IDS:
        if station_id not in daily_series:
            continue
        series = daily_series[station_id]
        all_fai_values.append(series.dropna().to_numpy())
        station_frames.append((station_id, series))

    if bloom_threshold is None:
        bloom_threshold = calibrate_bloom_threshold(np.concatenate(all_fai_values))

    rows = []
    for station_id, series in station_frames:
        for current_day in all_days:
            future_day = current_day + timedelta(days=horizon_days)
            if future_day not in series.index or pd.isna(series.get(future_day)):
                continue
            row = {"date": current_day.date().isoformat(), "station_id": station_id}
            valid_lookback = True
            for lb in lookback_days:
                past_day = current_day - timedelta(days=lb)
                val = series.get(past_day)
                if pd.isna(val):
                    valid_lookback = False
                    break
                row[f"fai_lag_{lb}d"] = val
            if not valid_lookback or pd.isna(series.get(current_day)):
                continue
            row["fai_now"] = series[current_day]
            row["fai_future"] = series[future_day]
            row["bloom_7d"] = int(series[future_day] >= bloom_threshold)
            # Placeholders — filled in once ERA5 licence is accepted / SNIA CSVs land.
            row["temp_c"] = np.nan
            row["wind_kmh"] = np.nan
            row["precip_mm"] = np.nan
            row["water_temp_c"] = np.nan
            row["ph"] = np.nan
            row["dissolved_oxygen_mgl"] = np.nan
            rows.append(row)

    return pd.DataFrame(rows), bloom_threshold

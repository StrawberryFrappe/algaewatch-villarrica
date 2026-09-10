"""Real-data access layer for the backend. Loads the collected FAI series and
the trained model once at import time, and exposes the read/predict
operations the routers need. This is the ONLY module in backend/ that reaches
into src/features and src/model — routers call this, not the pipeline
directly, so the pipeline's internals can change without touching routers.
"""

import math
import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.features.build_dataset import build_daily_series  # noqa: E402
from src.features.stations import STATION_IDS, STATIONS, STATIONS_BY_ID  # noqa: E402
from src.model import infer  # noqa: E402
from src.model import per_pixel_infer  # noqa: E402

FAI_CSV = PROJECT_ROOT / "data" / "processed" / "fai_series_raw.csv"
GRID_CSV = PROJECT_ROOT / "data" / "processed" / "fai_grid_latest.csv"
CANDIDATE_FORECAST_CSV = (
    PROJECT_ROOT / "data" / "processed" / "per_pixel_forecast_latest.csv"
)

LOOKBACK_DAYS = (1, 3, 7)
HORIZON_DAYS = 7


class DataNotReadyError(RuntimeError):
    pass


def _load():
    if not FAI_CSV.exists():
        raise DataNotReadyError(
            f"{FAI_CSV} not found — run scripts/collect_fai.py first."
        )
    fai_df = pd.read_csv(FAI_CSV)
    daily_series = build_daily_series(fai_df, end_date=date.today().isoformat())
    try:
        artifacts = infer.load_artifacts()
    except infer.ModelNotTrainedError as exc:
        raise DataNotReadyError(str(exc)) from exc
    return daily_series, artifacts


_daily_series, _artifacts = _load()
_dates_index = next(iter(_daily_series.values())).index
DATES: list[str] = [d.date().isoformat() for d in _dates_index]
MIN_DATE, MAX_DATE = DATES[0], DATES[-1]

THRESHOLD = _artifacts["metrics"]["fai_alert_threshold"]


def get_stations():
    return STATIONS


def _series_value(station_id: str, iso_date: str) -> float | None:
    series = _daily_series.get(station_id)
    if series is None:
        return None
    ts = pd.Timestamp(iso_date)
    val = series.get(ts)
    return float(val) if val is not None and pd.notna(val) else None


def get_fai(station_id: str, iso_date: str) -> float | None:
    value = _series_value(station_id, iso_date)
    if value is not None:
        return value
    # Fallback: the station's placeholder coordinate found no nearby water
    # pixel for this pass (see fai.py's at_latlon) — use the lake-wide mean
    # rather than silently reporting no data.
    return _series_value("lake", iso_date)


def get_observations(station_id: str | None, from_date: str, to_date: str) -> list[dict]:
    station_ids = [station_id] if station_id else list(STATIONS_BY_ID.keys())
    start, end = pd.Timestamp(from_date), pd.Timestamp(to_date)
    rows = []
    for sid in station_ids:
        series = _daily_series.get(sid)
        if series is None:
            continue
        window = series[(series.index >= start) & (series.index <= end)]
        for ts, fai in window.items():
            if pd.isna(fai):
                continue
            rows.append({
                "date": ts.date().isoformat(),
                "station_id": sid,
                "fai": float(fai),
                # Real in-situ sensor data (temp/pH/O2) isn't wired in yet —
                # see src/features/insitu.py — never fabricated here.
                "water_temp_c": None,
                "ph": None,
                "dissolved_oxygen_mgl": None,
                "wind_speed_kmh": None,
            })
    return rows


def fai_to_risk(fai: float, threshold: float = THRESHOLD) -> int:
    """Maps a raw FAI value to a 0-100 "current state" risk score, centered so
    that risk=50 at the calibrated bloom threshold (see calibrate_bloom_threshold
    in build_dataset.py) and saturating away from it. This is NOT the model —
    it is a direct, deterministic reading of the present FAI, matching the
    project's FAI-describes-the-present / model-predicts-the-future split.
    """
    if threshold <= 0:
        return 0
    ratio = fai / threshold
    score = 100 / (1 + math.exp(-3 * (ratio - 1)))
    return round(max(0, min(100, score)))


def risk_level(risk: int) -> str:
    if risk < 25:
        return "MUY_BAJO"
    if risk < 45:
        return "BAJO"
    if risk < 68:
        return "MEDIO"
    return "ALTO"


def get_risk(iso_date: str) -> dict:
    stations_out = []
    for s in STATIONS:
        fai = get_fai(s.id, iso_date)
        risk = fai_to_risk(fai) if fai is not None else 0
        stations_out.append({"station_id": s.id, "risk": risk, "level": risk_level(risk)})
    lake_mean = round(sum(s["risk"] for s in stations_out) / len(stations_out))
    return {"stations": stations_out, "lake_mean_risk": lake_mean}


def _load_grid_df():
    if not GRID_CSV.exists():
        raise DataNotReadyError(f"{GRID_CSV} not found — run scripts/collect_fai_grid.py first.")
    return pd.read_csv(GRID_CSV)


def get_risk_grid() -> dict:
    df = _load_grid_df()
    points = [
        {"lat": row.lat, "lng": row.lng, "risk": fai_to_risk(row.fai)}
        for row in df.itertuples()
    ]
    return {"date": df["date"].iloc[0], "points": points}


def get_last_satellite_pass() -> str | None:
    """The real date of the most recent Sentinel-2 pass used anywhere in the
    pipeline (the grid CSV) — as opposed to MAX_DATE, which is forward-filled
    up to "today" for the UI's date slider and is NOT a real pass date.
    """
    try:
        return str(_load_grid_df()["date"].iloc[0])
    except (DataNotReadyError, IndexError):
        return None


def _feature_row(station_id: str, iso_date: str) -> dict:
    d = date.fromisoformat(iso_date)
    row = {"fai_now": get_fai(station_id, iso_date)}
    for lb in LOOKBACK_DAYS:
        row[f"fai_lag_{lb}d"] = get_fai(station_id, (d - timedelta(days=lb)).isoformat())
    return row


def get_forecast(iso_date: str) -> dict:
    current = {s["station_id"]: s["risk"] for s in get_risk(iso_date)["stations"]}
    stations_out = []
    for s in STATIONS:
        features = _feature_row(s.id, iso_date)
        prediction = infer.predict_risk(_artifacts, features)
        stations_out.append({
            "station_id": s.id,
            "risk_7d": prediction["risk"],
            "level_7d": risk_level(prediction["risk"]),
            "fai_7d": prediction["fai_7d"],
            "delta_vs_previous_week": prediction["risk"] - current.get(s.id, 0),
            # Confidence is NOT the same number as risk: risk_7d already IS the
            # classifier's bloom probability (0-100). Confidence instead asks
            # "how far is that probability from a coin flip (50%)?" — a
            # probability near 0 or 1 means the model is sure either way; near
            # 50 means it's guessing. This is the standard way to read
            # confidence out of a probabilistic binary classifier.
            "confidence_pct": round(200 * abs(prediction["bloom_probability"] - 0.5)),
        })
    lake_mean_7d = round(sum(s["risk_7d"] for s in stations_out) / len(stations_out))
    alerts = sum(1 for s in stations_out if s["risk_7d"] >= 45)
    return {"stations": stations_out, "lake_mean_risk_7d": lake_mean_7d, "stations_in_alert": alerts}


def _interval_confidence(q10: float, q90: float) -> int:
    """Turn a q10-q90 prediction interval into a 0-100 confidence figure.

    Deliberately NOT the same quantity as the legacy model's `confidence_pct`,
    which measures a classifier probability's distance from a coin flip. This is
    a quantile regressor: it states nothing about a bloom probability, but it does
    state how wide it believes the outcome could be.

    The band is measured against the *decision* scale — twice the calibrated
    alert threshold — rather than against the predicted value. Scaling by the
    value itself collapses to 0 whenever the prediction sits near zero, which is
    most of this lake most of the time, and would report a well-calibrated
    interval (measured coverage 0.81 against 0.80 nominal) as no confidence at
    all. What a reader wants to know is whether the band is tight enough to
    separate "below the alert threshold" from "above it".
    """
    width = max(0.0, q90 - q10)
    scale = 2 * THRESHOLD
    if scale <= 0:
        return 0
    return round(100 * max(0.0, min(1.0, 1.0 - width / scale)))


def _load_candidate_forecast_df():
    if not CANDIDATE_FORECAST_CSV.exists():
        raise DataNotReadyError(
            f"{CANDIDATE_FORECAST_CSV} not found — run "
            "scripts/predict_per_pixel_forecast.py first."
        )
    return pd.read_csv(CANDIDATE_FORECAST_CSV)


def get_candidate_forecast(iso_date: str) -> dict:
    """The per-pixel candidate's projection, shaped like `get_forecast`.

    Read lazily and never at import, for the same reason `get_per_pixel_metrics`
    is: the candidate is optional, and a checkout that has not run
    `scripts/predict_per_pixel_forecast.py` must still serve the dashboard.

    `iso_date` sets the comparison baseline (`delta_vs_previous_week` against the
    present risk on that date) but does NOT select the projection. The candidate's
    newest anchor is fixed by the dataset, so there is exactly one projection —
    the same arrangement `/risk/grid` already has. The anchor and target dates
    ride along in the payload rather than being implied by the request.
    """
    df = _load_candidate_forecast_df()
    by_station = {row.station_id: row for row in df.itertuples()}
    current = {s["station_id"]: s["risk"] for s in get_risk(iso_date)["stations"]}

    stations_out = []
    for s in STATIONS:
        row = by_station.get(s.id)
        if row is None:
            continue
        risk = fai_to_risk(float(row.fai_q50))
        stations_out.append({
            "station_id": s.id,
            "risk_7d": risk,
            "level_7d": risk_level(risk),
            "fai_7d": float(row.fai_q50),
            "delta_vs_previous_week": risk - current.get(s.id, 0),
            "confidence_pct": _interval_confidence(
                float(row.fai_q10), float(row.fai_q90)
            ),
        })

    if not stations_out:
        raise DataNotReadyError(
            f"{CANDIDATE_FORECAST_CSV} holds no dashboard stations — regenerate it."
        )

    lake_mean_7d = round(sum(s["risk_7d"] for s in stations_out) / len(stations_out))
    alerts = sum(1 for s in stations_out if s["risk_7d"] >= 45)
    first = df.iloc[0]
    return {
        "stations": stations_out,
        "lake_mean_risk_7d": lake_mean_7d,
        "stations_in_alert": alerts,
        "anchor_date": str(first["anchor_date"]),
        "target_date": str(first["target_date"]),
        "horizon_days": int(first["horizon_days"]),
    }


def get_model_metrics() -> dict:
    return _artifacts["metrics"]


def get_per_pixel_metrics() -> dict | None:
    """Metrics for the per-pixel candidate, or None when it has not been trained.

    Returns None rather than raising: the candidate is optional. A checkout that
    has never run `scripts/train_per_pixel.py` must still serve the dashboard,
    so the router turns None into a 404 and the client hides the panel. This is
    deliberately NOT loaded at import time like the legacy artifacts -- the
    candidate does not drive any prediction path, and making the whole backend
    refuse to start over an optional model would be a bad trade.
    """
    try:
        return per_pixel_infer.load_metrics()
    except per_pixel_infer.PerPixelNotTrainedError:
        return None

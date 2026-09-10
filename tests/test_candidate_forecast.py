"""The per-pixel candidate serving /forecast behind a model switch (ADR-lq-0011).

These tests read the committed prediction table and the committed artifacts. They
do not retrain, do not hit the network, and do not assert that the candidate is
any *good* — it loses to its baselines, and rule MI-1 says that is reported, not
concealed. What they pin is that the switch works, that both paths return the
same shape, and that the legacy path is unchanged by the addition.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FORECAST_TABLE = REPO_ROOT / "data" / "processed" / "per_pixel_forecast_latest.csv"

EXPECTED_COLUMNS = {
    "station_id",
    "anchor_date",
    "target_date",
    "horizon_days",
    "fai_q10",
    "fai_q50",
    "fai_q90",
    "n_pixels",
}


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(scope="module")
def forecast_table() -> pd.DataFrame:
    if not FORECAST_TABLE.exists():
        pytest.skip("no committed candidate forecast table in this checkout")
    return pd.read_csv(FORECAST_TABLE)


def test_forecast_table_has_the_four_stations_and_a_lake_row(forecast_table) -> None:
    from src.features.stations import STATION_IDS

    assert EXPECTED_COLUMNS <= set(forecast_table.columns)
    assert set(forecast_table["station_id"]) == {*STATION_IDS, "lake"}


def test_forecast_table_quantiles_are_ordered_and_finite(forecast_table) -> None:
    """q10 <= q50 <= q90 is the one property a quantile head must not violate."""
    for row in forecast_table.itertuples():
        assert pd.notna(row.fai_q10) and pd.notna(row.fai_q50) and pd.notna(row.fai_q90)
        assert row.fai_q10 <= row.fai_q50 <= row.fai_q90
        assert row.n_pixels > 0


def test_candidate_forecast_matches_the_legacy_response_shape(forecast_table) -> None:
    from backend.app.data_source import MAX_DATE, get_candidate_forecast, get_forecast

    candidate = get_candidate_forecast(MAX_DATE)
    legacy = get_forecast(MAX_DATE)

    assert set(legacy) <= set(candidate)  # candidate adds anchor/target/horizon
    assert len(candidate["stations"]) == len(legacy["stations"])

    station_keys = set(legacy["stations"][0])
    for station in candidate["stations"]:
        assert set(station) == station_keys
        assert 0 <= station["risk_7d"] <= 100
        assert 0 <= station["confidence_pct"] <= 100


def test_forecast_endpoint_serves_the_candidate_when_asked() -> None:
    from backend.app.data_source import MAX_DATE
    from backend.app.routers.forecast import forecast

    response = _run(forecast(date_=MAX_DATE, model="candidate"))

    assert response.model_used == "candidate"
    assert response.anchor_date and response.target_date
    assert len(response.stations) == 4
    for station in response.stations:
        assert 0 <= station.risk_7d <= 100


def test_forecast_endpoint_defaults_to_legacy_and_is_unchanged() -> None:
    """Adding the switch must not move the numbers on the default path."""
    from backend.app.data_source import MAX_DATE, get_forecast
    from backend.app.routers.forecast import forecast

    response = _run(forecast(date_=MAX_DATE))
    direct = get_forecast(MAX_DATE)

    assert response.model_used == "legacy"
    # Date-independence belongs to the candidate; the legacy path says nothing.
    assert response.anchor_date is None and response.target_date is None
    assert response.lake_mean_risk_7d == direct["lake_mean_risk_7d"]
    assert [s.risk_7d for s in response.stations] == [
        s["risk_7d"] for s in direct["stations"]
    ]


def test_forecast_endpoint_404s_when_the_candidate_table_is_missing(monkeypatch) -> None:
    """A checkout that never ran the prediction script must still serve the
    dashboard: the router 404s and the client falls back to legacy."""
    from fastapi import HTTPException

    from backend.app import data_source
    from backend.app.data_source import MAX_DATE
    from backend.app.routers import forecast as router_module

    monkeypatch.setattr(
        data_source, "CANDIDATE_FORECAST_CSV", REPO_ROOT / "data" / "processed" / "nope.csv"
    )
    with pytest.raises(HTTPException) as excinfo:
        _run(router_module.forecast(date_=MAX_DATE, model="candidate"))
    assert excinfo.value.status_code == 404


def test_candidate_threshold_is_on_the_water_scale_not_the_station_scale() -> None:
    """BL-039. The legacy threshold was calibrated on station points sitting on
    shoreline vegetation and is ~7x the p99 of real water FAI. Reusing it for the
    candidate flattens every prediction to the bottom of the risk scale, which is
    what ADR-sf-0008 warned about. This pins the two apart."""
    import pandas as pd

    from backend.app.data_source import THRESHOLD, MAX_DATE, get_candidate_forecast

    result = get_candidate_forecast(MAX_DATE)
    candidate_threshold = result["alert_threshold"]

    assert candidate_threshold < THRESHOLD / 2, (
        "candidate threshold has drifted back toward the station-scale constant"
    )

    dataset = REPO_ROOT / "data" / "processed" / "per_pixel_anomaly_dataset.csv"
    if dataset.exists():
        water = pd.read_csv(dataset)["fai_future"].dropna()
        # It must sit inside the distribution it is meant to describe, not above it.
        assert water.quantile(0.90) < candidate_threshold < water.max()


def test_candidate_risk_varies_across_anchors() -> None:
    """A threshold on the wrong scale collapses every station to the same floor.
    The recalibrated one must produce an actual spread, otherwise the switch
    demos as 'the new model says nothing ever happens'."""
    from backend.app.data_source import get_candidate_forecast

    risks = []
    for date in ("2026-01-18", "2026-02-05", "2026-09-10"):
        risks.extend(s["risk_7d"] for s in get_candidate_forecast(date)["stations"])

    assert max(risks) - min(risks) >= 10, f"risk barely varies: {sorted(set(risks))}"


def test_candidate_anchor_never_follows_the_requested_date(forecast_table) -> None:
    """The candidate can only project from a real satellite pass, so it must
    select an anchor at or before the requested date - never a later one, which
    would be showing the user a projection made from data from their future.

    The pre-first-anchor case is the one that matters: MIN_DATE on the slider is
    2025-09-04 and the earliest anchor is 2025-11-25, so roughly three months of
    the timeline fall into that gap and are reachable by dragging.
    """
    from backend.app.data_source import DataNotReadyError, get_candidate_forecast

    for date in ("2026-02-05", "2026-05-01", "2026-09-10"):
        assert get_candidate_forecast(date)["anchor_date"] <= date

    earliest = min(forecast_table["anchor_date"].astype(str))
    before = (pd.Timestamp(earliest) - pd.Timedelta(days=1)).date().isoformat()
    with pytest.raises(DataNotReadyError):
        get_candidate_forecast(before)


def test_interval_confidence_is_bounded_and_monotonic() -> None:
    """A wider band must never report more confidence than a narrower one, and
    the figure has to stay on the 0-100 scale whatever the interval does."""
    from backend.app.data_source import _interval_confidence

    tight = _interval_confidence(-0.001, 0.001)
    loose = _interval_confidence(-0.5, 0.5)
    assert 0 <= loose <= tight <= 100
    assert _interval_confidence(0.0, 0.0) == 100

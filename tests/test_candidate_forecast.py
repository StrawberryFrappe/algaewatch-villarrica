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


def test_interval_confidence_is_bounded_and_monotonic() -> None:
    """A wider band must never report more confidence than a narrower one, and
    the figure has to stay on the 0-100 scale whatever the interval does."""
    from backend.app.data_source import _interval_confidence

    tight = _interval_confidence(-0.001, 0.001)
    loose = _interval_confidence(-0.5, 0.5)
    assert 0 <= loose <= tight <= 100
    assert _interval_confidence(0.0, 0.0) == 100

"""Where the station readings actually come from.

Found 2026-09-10, upstream of every modelling defect in the audit. Two of the
four station coordinates in `src/features/stations.py` are not on the lake. That
file says so itself — the coordinates are placeholders pending the GPS that
arrives with the SNIA CSVs — but nothing downstream refused to train on them.

`src/features/fai.py::at_latlon` expands its search window up to
`max_radius_px=60`, which is 1.2 km at 20 m resolution, and averages the water
pixels it eventually reaches. For a point off the water those are shoreline
mixed pixels, and vegetation reads strongly positive in FAI. The result is a
station series whose values sit in the extreme tail of the raster they were
drawn from, a pooled bloom threshold calibrated on that tail, and a label that
is close to "is this station sur or pucon".

These tests pin the measurement. They do not assert the situation is acceptable
— `tests/test_model_integrity.py` is where that verdict lives.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.model.integrity import _haversine_km, check_station_points_on_water


@pytest.fixture(scope="module")
def distances(stations, fai_grid) -> dict:
    """Kilometres from each declared coordinate to the nearest sampled water pixel.

    The grid is a 15-pixel-stride sample at 20 m, so ~300 m spacing: a station
    genuinely on the water still reads up to ~0.2 km here. Only distances well
    past that are evidence of anything.
    """
    return {
        station["id"]: min(
            _haversine_km(station["lat"], station["lng"], lat, lng)
            for lat, lng in zip(fai_grid.lat, fai_grid.lng)
        )
        for station in stations
    }


def test_two_stations_sit_on_the_water(distances: dict) -> None:
    assert distances["tolten"] == pytest.approx(0.07, abs=0.02)
    assert distances["norte"] == pytest.approx(0.15, abs=0.02)


def test_two_stations_do_not(distances: dict) -> None:
    assert distances["pucon"] == pytest.approx(0.77, abs=0.02)
    assert distances["sur"] == pytest.approx(0.98, abs=0.02)


def test_sur_lies_outside_the_lake_entirely(stations, fai_grid) -> None:
    """Not merely far from a sample point — south of every water pixel there is."""
    sur = next(s for s in stations if s["id"] == "sur")
    assert sur["lat"] < fai_grid.lat.min()


def test_off_lake_stations_read_in_the_tail_of_their_own_scene(fai_series, fai_grid) -> None:
    """Same date, same raster: the two off-lake points are extreme outliers.

    On 2026-08-22 the lake mean FAI is 0.000267 and 0.4% of 1,860 water pixels
    clear the 0.0259 bloom threshold, while sur and pucon each read above 0.056.
    A reading drawn from a raster cannot sit outside that raster's distribution
    unless it is sampling something else.
    """
    date = fai_grid.date.iloc[0]
    row = fai_series[fai_series.date == date].iloc[0]
    p99 = float(np.percentile(fai_grid.fai, 99))

    assert row.lake_mean_fai == pytest.approx(0.000267, abs=0.00001)
    assert row.fai_sur > p99
    assert row.fai_pucon > p99
    assert row.fai_sur == pytest.approx(0.0567, abs=0.001)
    assert row.fai_pucon == pytest.approx(0.0585, abs=0.001)

    on_water_fraction = float((fai_grid.fai >= 0.025916439519215278).mean())
    assert on_water_fraction == pytest.approx(0.0038, abs=0.0005)


def test_the_two_contaminated_stations_are_the_two_that_bloom(dataset, distances) -> None:
    """The provenance defect and the label defect are the same defect.

    Ranking stations by distance from the water reproduces the ranking by bloom
    rate. That is the connection between this file and EV-001.
    """
    rates = dataset.groupby("station_id").bloom_7d.mean()
    off_water = {s for s, km in distances.items() if km > 0.35}
    blooming = {s for s, rate in rates.items() if rate > 0.1}
    assert off_water == blooming == {"sur", "pucon"}


def test_check_reports_the_failure_with_its_numbers(stations, fai_grid, fai_series) -> None:
    """The check used by the gate agrees with the measurements above."""
    result = check_station_points_on_water(stations, fai_grid, fai_series)
    assert result.passed is False
    assert result.measured["stations"]["sur"]["distance_km"] == pytest.approx(0.98, abs=0.02)
    assert result.measured["stations"]["norte"]["distance_km"] < 0.35
    assert result.measured["stations"]["sur"]["above_scene_percentile"] is True
    assert result.measured["stations"]["norte"]["above_scene_percentile"] is False


def test_check_passes_when_points_are_genuinely_on_water(fai_grid) -> None:
    """The check is capable of passing — otherwise it proves nothing.

    Sample the station coordinates from the water grid itself and the same code
    returns a pass, so a future fix to `stations.py` will be recognised.
    """
    sampled = fai_grid.iloc[[10, 200, 900, 1500]]
    stations = [
        {"id": "s{}".format(i), "lat": row.lat, "lng": row.lng}
        for i, (_, row) in enumerate(sampled.iterrows())
    ]
    result = check_station_points_on_water(stations, fai_grid, station_series=None)
    assert result.passed is True

"""WI-005 — the lake-mean anomaly retrain (ADR-sf-0008, ADR-lq-0009).

Everything here reads the committed `fai_series_raw.csv` or synthetic frames.
No network, no credentials, no `sentinelhub` — `src/features/lake_anomaly.py`
is pure pandas/numpy so it runs on a machine without BL-028 resolved.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.features.lake_anomaly import build_anomaly_pairs, build_pairs

REPO_ROOT = Path(__file__).resolve().parents[1]
FAI_SERIES = REPO_ROOT / "data" / "processed" / "fai_series_raw.csv"


@pytest.fixture(scope="module")
def series() -> pd.DataFrame:
    return pd.read_csv(FAI_SERIES)


class TestBuildPairs:
    """`build_pairs` is pure pairing and must stay pinned to EV-019."""

    def test_reproduces_ev019_thirty_five_honest_pairs(self, series) -> None:
        pairs = build_pairs(series)
        assert len(pairs) == 35
        horizons = dict(sorted(pairs["horizon_days"].value_counts().items()))
        assert horizons == {5: 10, 6: 1, 7: 11, 8: 13}

    def test_one_row_per_anchor_no_duplicates(self, series) -> None:
        pairs = build_pairs(series)
        assert pairs["date"].is_unique
        assert len(pairs.drop_duplicates(["station_id", "fai_now", "fai_future"])) == len(pairs)

    def test_fai_columns_are_raw_units_so_persistence_matches_ev019(self, series) -> None:
        from src.model.baselines import persistence_mae

        assert persistence_mae(build_pairs(series)) == pytest.approx(0.001333, abs=5e-6)


class TestBuildAnomalyPairs:

    def test_baseline_uses_only_observations_strictly_before_the_anchor(self) -> None:
        """The causal baseline must equal the mean/std of passes before `t`, and
        never see the anchor's own value or anything after it."""
        dates = pd.date_range("2026-01-01", periods=40, freq="2D")
        rng = np.random.default_rng(0)
        vals = np.cumsum(rng.normal(0.0, 0.01, 40))  # non-constant random walk
        s = pd.DataFrame({"date": [d.date().isoformat() for d in dates], "lake_mean_fai": vals})
        pairs = build_anomaly_pairs(s, min_prior=3)
        s_sorted = s.sort_values("date").reset_index(drop=True)
        for _, row in pairs.iterrows():
            pos = int(s_sorted.index[s_sorted["date"] == row["date"]][0])
            prior = s_sorted["lake_mean_fai"].iloc[:pos]
            assert row["n_prior"] == len(prior)
            assert row["baseline_mean"] == pytest.approx(prior.mean())
            assert row["baseline_std"] == pytest.approx(prior.std(ddof=1))

    def test_min_prior_drops_the_earliest_anchors(self, series) -> None:
        loose = build_anomaly_pairs(series, min_prior=0)
        strict = build_anomaly_pairs(series, min_prior=8)
        assert len(strict) < len(loose)
        assert (strict["n_prior"] >= 8).all()
        # rows are dropped from the front — the earliest anchors have no history
        assert pd.to_datetime(strict["date"]).min() > pd.to_datetime(loose["date"]).min()

    def test_anomaly_is_the_standardised_deviation_from_the_causal_baseline(self, series) -> None:
        pairs = build_anomaly_pairs(series, min_prior=5)
        expected_now = (pairs["fai_now"] - pairs["baseline_mean"]) / pairs["baseline_std"]
        expected_future = (pairs["fai_future"] - pairs["baseline_mean"]) / pairs["baseline_std"]
        pd.testing.assert_series_equal(pairs["anomaly_now"], expected_now, check_names=False)
        pd.testing.assert_series_equal(pairs["anomaly_future"], expected_future, check_names=False)

    def test_spatial_unit_column_is_parameterised_for_adr0004_d3(self) -> None:
        """D3 substitutes `pixel_id` for the lake-wide sentinel without a rewrite."""
        dates = pd.date_range("2026-01-01", periods=30, freq="3D")
        rows = []
        for px in ("p1", "p2"):
            for i, d in enumerate(dates):
                rows.append({"date": d.date().isoformat(), "pixel_id": px, "fai": 0.001 * i})
        s = pd.DataFrame(rows)
        pairs = build_anomaly_pairs(s, value_col="fai", unit_col="pixel_id", min_prior=3)
        assert set(pairs["station_id"]) == {"p1", "p2"}
        assert (pairs.groupby("station_id").size() > 0).all()

    def test_lake_wide_table_has_one_spatial_unit(self, series) -> None:
        pairs = build_anomaly_pairs(series, min_prior=0)
        assert pairs["station_id"].nunique() == 1

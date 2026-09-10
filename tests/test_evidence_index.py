"""Pins the figures in `agents/validation/EVIDENCE_INDEX.md`.

These pass today. They are not model-quality assertions — every number below
describes a **defect** — they exist so the numbers cannot drift unnoticed. The
2026-09-09 mount review found that every figure carrying a reproduction command
reproduced exactly, while the two quoted without one had both drifted. This file
turns the index from a set of commands someone might run into a set that CI runs.

If one of these fails after the retrain, that is expected and good: update the
index in the same change, and say which evidence ID moved.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from src.model.baselines import persistence_mae, trivial_rule


def test_ev001_bloom_rate_by_station(dataset: pd.DataFrame) -> None:
    """The label encodes location: two stations always bloom, two never do."""
    rates = dataset.groupby("station_id").bloom_7d.mean().round(3)
    assert rates["sur"] == pytest.approx(0.979, abs=0.001)
    assert rates["pucon"] == pytest.approx(0.501, abs=0.001)
    assert rates["norte"] == pytest.approx(0.0, abs=0.001)
    assert rates["tolten"] == pytest.approx(0.0, abs=0.001)


def test_ev002_station_rule_beats_the_classifier(dataset, pipeline_split, metrics) -> None:
    """A rule reading only the station name outscores the trained model."""
    rule = trivial_rule(pipeline_split.train, pipeline_split.holdout)
    assert rule["chosen_group"] == "sur"
    assert rule["precision"] == pytest.approx(0.97, abs=0.01)
    assert rule["recall"] == pytest.approx(0.74, abs=0.01)
    assert rule["f1_score"] == pytest.approx(0.84, abs=0.01)
    assert rule["f1_score"] > metrics["metrics"]["f1_score"]


def test_ev003_persistence_beats_the_regressor(pipeline_split, metrics) -> None:
    """Predicting no change is 43% more accurate than the trained regressor."""
    baseline = persistence_mae(pipeline_split.holdout)
    assert baseline == pytest.approx(0.00603, abs=0.00001)
    assert baseline < metrics["metrics"]["mae_fai"]


def test_ev004_rows_were_fabricated_by_forward_fill(dataset: pd.DataFrame) -> None:
    """1,356 rows carry 363 real observations; 85% duplicate their own lag."""
    assert len(dataset) == 1356
    assert len(dataset.drop_duplicates(["station_id", "fai_now", "fai_future"])) == 363
    duplicate_lag = (dataset.fai_now == dataset.fai_lag_1d).mean()
    assert duplicate_lag == pytest.approx(0.853, abs=0.001)


def test_ev005_temporal_holdout_leaks_at_the_seam(pipeline_split) -> None:
    """Last training date and first holdout date are the same day."""
    assert pipeline_split.last_train_date == "2026-06-09"
    assert pipeline_split.first_holdout_date == "2026-06-09"
    assert pipeline_split.gap_days == 0


def test_ev007_real_observation_coverage(fai_series: pd.DataFrame) -> None:
    """56 pass dates over a year; only 11 exact seven-day pairs exist."""
    dates = set(pd.to_datetime(fai_series.date).dt.date)
    gaps = pd.to_datetime(fai_series.date).diff().dt.days.dropna()

    assert len(dates) == 56
    assert fai_series.date.min() == "2025-09-04"
    assert fai_series.date.max() == "2026-08-22"
    assert gaps.median() == 3
    assert gaps.max() == 32

    exact = sum(1 for d in dates if d + dt.timedelta(days=7) in dates)
    relaxed = sum(1 for d in dates if any(d + dt.timedelta(days=k) in dates for k in range(5, 10)))
    assert exact == 11
    assert relaxed == 35


def test_ev008_grid_sample_size(fai_grid: pd.DataFrame) -> None:
    """One pass yields 1,860 water pixels — the per-pixel redesign's premise."""
    assert len(fai_grid) == 1860


def test_ev009_classifier_re_reads_the_present(dataset, bloom_threshold) -> None:
    """Thresholding today's value reproduces the seven-day-ahead label."""
    agreement = ((dataset.fai_now >= bloom_threshold).astype(int) == dataset.bloom_7d).mean()
    assert agreement == pytest.approx(0.900, abs=0.001)
    assert dataset.fai_now.corr(dataset.fai_future) == pytest.approx(0.758, abs=0.001)


def test_ev011_real_reading_count(fai_series: pd.DataFrame) -> None:
    """218 real readings, not 56 x 4 — six cells found no water pixel."""
    columns = ["fai_pucon", "fai_norte", "fai_tolten", "fai_sur"]
    per_station = {c: int(fai_series[c].notna().sum()) for c in columns}
    assert per_station == {
        "fai_pucon": 54,
        "fai_norte": 56,
        "fai_tolten": 54,
        "fai_sur": 54,
    }
    assert sum(per_station.values()) == 218

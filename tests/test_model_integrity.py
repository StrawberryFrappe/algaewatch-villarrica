"""GATE-MODEL — the checks a shipped model has to pass.

Every check here **fails on the legacy dataset**, so every one is marked
`xfail(strict=True)`. That is deliberate, and the strictness is the point:

- the suite stays green, so a genuine regression elsewhere is still visible;
- the moment WI-005 makes one of these pass, pytest reports XPASS as a
  **failure**, forcing the mark to be removed in the same change;
- nobody can claim the gate is satisfied while the marks are still here.

A test that merely asserted the current broken numbers would go green and stay
green forever. These assert the requirement instead, and record how far off it
currently is.

Point the suite at a candidate table to judge a retrain by exactly these checks:

    ALGAEWATCH_DATASET=data/processed/candidate.csv pytest tests/test_model_integrity.py
"""

from __future__ import annotations

import pytest

from src.model.integrity import (
    CheckResult,
    check_beats_persistence,
    check_beats_trivial_rule,
    check_chronological_split,
    check_label_not_stratified_by_station,
    check_no_fabricated_rows,
    check_no_present_reading_shortcut,
    check_station_points_on_water,
    run_all,
)


@pytest.mark.xfail(
    strict=True,
    reason="MI-1: the regressor is 43% worse than persistence (EV-003). Fixed by BL-003/BL-005.",
)
def test_mi1_model_beats_persistence(metrics, pipeline_split) -> None:
    """Scored on the partition the recorded metrics came from.

    `metrics.json` is produced by `train.py`, which splits without an embargo.
    Recomputing the baseline on the embargoed split would compare the model's
    numbers against a baseline measured on different data — a like-for-like
    comparison is the whole point of MI-1. When BL-006 gives training the
    embargo, this fixture and that split become the same thing.
    """
    result = check_beats_persistence(metrics["metrics"], pipeline_split)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="MI-1: a station-name rule outscores the classifier (EV-002). Fixed by BL-004.",
)
def test_mi1_model_beats_trivial_rule(metrics, pipeline_split) -> None:
    """Same partition as the recorded metrics — see the note above.

    This one matters more than the persistence case: `trivial_rule` picks its
    group from the training partition, so a different training partition can in
    principle pick a different group and produce a different score.
    """
    result = check_beats_trivial_rule(metrics["metrics"], pipeline_split)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="PR-3: 1,356 rows forward-filled from 363 real observations (EV-004). Fixed by BL-005.",
)
def test_pr3_no_fabricated_rows(dataset) -> None:
    result = check_no_fabricated_rows(dataset)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="MI-2: the training path splits with no embargo, sharing a boundary date "
    "(EV-005). Fixed by BL-006 adopting baselines.chronological_split.",
)
def test_mi2_training_split_is_chronological_with_embargo(pipeline_split) -> None:
    """Asserted against the split `train.py` performs, not against the fixed one.

    Judging `chronological_split` with its own embargo applied would be the check
    grading its own homework: it would pass while the pipeline stayed broken.
    """
    result = check_chronological_split(pipeline_split)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="ADR 0004 D2: positive rate is 0.98 at sur and 0.00 at norte (EV-001). "
    "Fixed by BL-004, and blocked underneath by the station coordinates.",
)
def test_label_is_not_a_proxy_for_location(dataset) -> None:
    result = check_label_not_stratified_by_station(dataset)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="EV-009: thresholding fai_now reproduces the label on 90% of rows. "
    "Fixed by BL-003 (continuous target) and BL-004 (local anomaly).",
)
def test_forecast_is_not_a_re_reading_of_the_present(dataset, bloom_threshold) -> None:
    result = check_no_present_reading_shortcut(dataset, bloom_threshold)
    assert result.passed, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="Provenance: pucon and sur sample points are 0.77 km and 0.98 km off the "
    "water and read above their own scene's p99. Fixed by BL-027.",
)
def test_station_points_are_on_the_lake(stations, fai_grid, fai_series) -> None:
    result = check_station_points_on_water(stations, fai_grid, fai_series)
    assert result.passed, result.detail


def test_gate_runs_and_reports_every_check(
    dataset, embargoed_split, metrics, bloom_threshold, stations, fai_grid, fai_series
) -> None:
    """The gate mechanism itself, which must work regardless of the verdicts.

    Not xfailed: this asserts the harness plumbing, not the model. Each result
    carries its measured numbers, so a failing gate says how far off it is
    rather than only that it failed.
    """
    results = run_all(
        dataset,
        embargoed_split,
        metrics["metrics"],
        bloom_threshold,
        stations=stations,
        water_points=fai_grid,
        station_series=fai_series,
    )
    assert len(results) == 7
    assert all(isinstance(r, CheckResult) for r in results)
    assert all(r.detail and r.rule for r in results)
    assert all(r.measured for r in results)


def test_checks_are_omitted_not_passed_when_inputs_are_missing(
    dataset, embargoed_split, metrics, bloom_threshold
) -> None:
    """Absent provenance data must not silently count as a clean provenance check."""
    results = run_all(dataset, embargoed_split, metrics["metrics"], bloom_threshold)
    assert len(results) == 6
    assert "station_points_on_water" not in {r.name for r in results}


def test_empty_input_fails_rather_than_passing_vacuously(dataset) -> None:
    """An empty table satisfies "rows == unique rows" trivially.

    Reporting that as a pass would let a broken build produce a clean gate,
    which is the exact failure mode these checks exist to prevent.
    """
    result = check_no_fabricated_rows(dataset.iloc[:0])
    assert result.passed is False
    assert "empty" in result.detail.lower()

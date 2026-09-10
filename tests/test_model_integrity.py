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

import os
from pathlib import Path

import pandas as pd
import pytest

from src.model.baselines import Split, chronological_split
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

REPO_ROOT = Path(__file__).resolve().parents[1]

#: True when the suite is pointed at a candidate table via `ALGAEWATCH_DATASET`.
#: The GATE-MODEL xfail marks record how far the *legacy* four-station table is
#: from each requirement; a dataset-dependent one is lifted (or skipped) for a
#: candidate run so `ALGAEWATCH_DATASET=... pytest tests/test_model_integrity.py`
#: gives a real pass/fail verdict on the retrain instead of XPASS noise (ADR-lq-0009).
ON_CANDIDATE = bool(os.environ.get("ALGAEWATCH_DATASET"))


def _lake_wide(n_days: int = 80, horizon: int = 8) -> pd.DataFrame:
    """A single-spatial-unit daily table shaped like WI-005's (ADR-sf-0008)."""
    dates = pd.date_range("2026-01-01", periods=n_days, freq="D")
    return pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in dates],
            "station_id": "lake",
            "fai_now": 0.0,
            "fai_lag_1d": 0.0,
            "fai_future": 0.0,
            "bloom_7d": 0,
            "horizon_days": horizon,
        }
    )


class TestChronologicalCheckHorizon:
    """BL-029: the embargo and its check must use the table's real horizon."""

    def test_split_embargoes_the_target_date_when_given_a_horizon_column(self) -> None:
        split = chronological_split(_lake_wide(horizon=8), horizon_col="horizon_days")
        first_holdout = pd.to_datetime(split.holdout["date"]).min()
        targets = pd.to_datetime(split.train["date"]) + pd.to_timedelta(
            split.train["horizon_days"], unit="D"
        )
        assert (targets <= first_holdout).all()
        assert check_chronological_split(split).passed

    def test_check_fails_a_seven_day_gap_under_an_eight_day_horizon(self) -> None:
        """7 >= HORIZON_DAYS, so the audited check passed this leaking split."""
        naive = chronological_split(_lake_wide(horizon=8), embargo_days=7)
        assert naive.gap_days == 7
        leaking = Split(**{**naive.__dict__, "max_horizon_days": 8})
        result = check_chronological_split(leaking)
        assert not result.passed
        assert "8" in result.detail

    def test_legacy_fixed_horizon_split_still_judged_against_horizon_days(self) -> None:
        naive = chronological_split(_lake_wide(horizon=8), embargo_days=7)
        assert naive.max_horizon_days is None
        assert check_chronological_split(naive).passed  # gap 7 >= HORIZON_DAYS 7

    def test_check_passes_a_correctly_embargoed_dense_variable_horizon_split(self) -> None:
        """A dense daily table with mixed 5-8 day horizons — the per-pixel shape
        ADR 0004 D3 must flow through unchanged. The embargo is correct per row,
        so the check must pass; asserting `gap_days >= max_horizon` would false-fail
        it because the last kept row usually carries a *short* horizon."""
        dates = pd.date_range("2026-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "date": [d.date().isoformat() for d in dates],
                "station_id": "px1",
                "fai_now": 0.0,
                "fai_lag_1d": 0.0,
                "fai_future": 0.0,
                "bloom_7d": 0,
                "horizon_days": [5, 6, 7, 8] * 25,
            }
        )
        split = chronological_split(df, horizon_col="horizon_days")
        first_holdout = pd.to_datetime(split.holdout["date"]).min()
        kept_targets = pd.to_datetime(split.train["date"]) + pd.to_timedelta(
            split.train["horizon_days"], unit="D"
        )
        assert (kept_targets < first_holdout).all()          # embargo genuinely correct
        assert check_chronological_split(split).passed        # ...so the check must agree


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
    not ON_CANDIDATE,
    strict=True,
    reason="PR-3: 1,356 rows forward-filled from 363 real observations (EV-004). "
    "Fixed by BL-005 / WI-005 — a candidate table must actually pass this.",
)
def test_pr3_no_fabricated_rows(dataset) -> None:
    result = check_no_fabricated_rows(dataset)
    assert result.passed, result.detail


@pytest.mark.skipif(
    ON_CANDIDATE,
    reason="`pipeline_split` mirrors train.py's four-station no-embargo slice; "
    "WI-005's real split path is expanding_window_folds, covered by "
    "tests/test_lake_anomaly_model.py::TestExpandingWindowFolds.",
)
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
    not ON_CANDIDATE,
    strict=True,
    reason="ADR 0004 D2: positive rate is 0.98 at sur and 0.00 at norte (EV-001). "
    "Fixed by BL-004, and blocked underneath by the station coordinates. A "
    "single-unit candidate table satisfies this by being inapplicable (BL-031).",
)
def test_label_is_not_a_proxy_for_location(dataset) -> None:
    result = check_label_not_stratified_by_station(dataset)
    # An inapplicable check is omitted from the verdict, never a gate failure
    # (ADR-sf-0008 D3) — a one-unit lake table has nothing to stratify.
    assert result.passed or not result.applicable, result.detail


@pytest.mark.xfail(
    strict=True,
    reason="EV-009: thresholding fai_now reproduces the label on 90% of rows. "
    "Fixed by BL-003 (continuous target) and BL-004 (local anomaly). Stays xfail "
    "on the lake candidate too: `bloom_7d` is constant under the uncalibrated "
    "threshold (EV-020), so agreement is 1.0 vacuously — an honest outcome, not "
    "a fix (ADR-sf-0008 D4; owner decision 2026-09-10).",
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


#: Checks that `run_all` always produces, whatever the table's shape. BL-032:
#: plumbing tests assert against this and against omission *reasons* — never a
#: magic count that assumes the four-station shape and breaks on a lake-wide one.
CORE_CHECKS = {
    "beats_persistence",
    "beats_trivial_rule",
    "no_fabricated_rows",
    "chronological_split",
    "no_present_reading_shortcut",
}


def test_gate_runs_and_reports_every_check(
    dataset, embargoed_split, metrics, bloom_threshold, stations, fai_grid, fai_series
) -> None:
    """The gate mechanism itself, which must work regardless of the verdicts.

    Not xfailed: this asserts the harness plumbing, not the model. Shape-agnostic
    (BL-032): the stratification check appears iff the table has >= 2 spatial
    groups, the provenance check iff a station catalogue is supplied; everything
    returned is applicable and carries its measured numbers.
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
    names = {r.name for r in results}
    n_groups = dataset["station_id"].nunique()

    assert CORE_CHECKS <= names
    assert "station_points_on_water" in names
    assert ("label_not_stratified_by_station" in names) == (n_groups >= 2)
    assert all(isinstance(r, CheckResult) for r in results)
    assert all(r.detail and r.rule and r.measured for r in results)
    assert all(r.applicable for r in results)


def test_checks_are_omitted_not_passed_when_inputs_are_missing(
    dataset, embargoed_split, metrics, bloom_threshold
) -> None:
    """Absent provenance data must not silently count as a clean provenance check."""
    results = run_all(dataset, embargoed_split, metrics["metrics"], bloom_threshold)
    names = {r.name for r in results}
    assert CORE_CHECKS <= names
    assert "station_points_on_water" not in names
    assert all(r.applicable for r in results)


def test_gate_adapts_to_a_single_group_table_without_editing_assertions() -> None:
    """BL-031 / BL-032: a lake-wide table omits the stratification check by reason.

    The same `run_all` call that yields the stratification check on the
    four-station table must omit it here — one spatial unit makes the
    positive-rate spread 0.000 and the check vacuous — and every result it does
    return must be applicable, so the count is a consequence of the table's
    shape, not a number baked into a test.
    """
    df = _lake_wide()
    split = chronological_split(df, horizon_col="horizon_days")
    results = run_all(df, split, {"mae_fai": 0.001, "f1_score": 0.0}, threshold=0.02)
    names = {r.name for r in results}

    assert "label_not_stratified_by_station" not in names
    assert "beats_persistence" in names and "no_fabricated_rows" in names
    assert all(r.applicable for r in results)

    # And called directly — the path `tests/` uses — it declares itself, rather
    # than returning a 0.000-spread pass that XPASS-fails the xfail above.
    direct = check_label_not_stratified_by_station(df)
    assert direct.applicable is False
    assert direct.passed is False


def test_stratification_check_is_applicable_on_the_four_station_table() -> None:
    # The committed four-station table directly, not the overridable `dataset`
    # fixture — this asserts the >= 2-group branch regardless of ALGAEWATCH_DATASET.
    four_station = pd.read_csv(REPO_ROOT / "data" / "processed" / "training_dataset.csv")
    result = check_label_not_stratified_by_station(four_station)
    assert result.applicable is True


def test_empty_input_fails_rather_than_passing_vacuously(dataset) -> None:
    """An empty table satisfies "rows == unique rows" trivially.

    Reporting that as a pass would let a broken build produce a clean gate,
    which is the exact failure mode these checks exist to prevent.
    """
    result = check_no_fabricated_rows(dataset.iloc[:0])
    assert result.passed is False
    assert "empty" in result.detail.lower()

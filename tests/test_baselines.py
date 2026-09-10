"""Unit tests for `src/model/baselines.py`.

The baselines are what every future model is judged against, so they get tested
on their own terms rather than only through the dataset. A baseline that is
quietly wrong is worse than no baseline: it produces a comparison that looks
rigorous and is not.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.model.baselines import (
    HORIZON_DAYS,
    beats_baselines,
    chronological_split,
    persistence_mae,
    trivial_rule,
)


def _synthetic(n_days: int = 100, stations=("a", "b")) -> pd.DataFrame:
    """A table with the same columns as the real one and no built-in defect."""
    rng = np.random.default_rng(0)
    dates = pd.date_range("2026-01-01", periods=n_days, freq="D")
    rows = []
    for station in stations:
        for day in dates:
            now = float(rng.normal(0.0, 0.01))
            rows.append(
                {
                    "date": day.date().isoformat(),
                    "station_id": station,
                    "fai_lag_1d": float(rng.normal(0.0, 0.01)),
                    "fai_now": now,
                    "fai_future": now + float(rng.normal(0.0, 0.005)),
                    "bloom_7d": int(rng.random() < 0.3),
                }
            )
    return pd.DataFrame(rows)


class TestChronologicalSplit:
    def test_embargo_opens_a_gap_of_at_least_the_horizon(self) -> None:
        split = chronological_split(_synthetic())
        assert split.gap_days >= HORIZON_DAYS

    def test_zero_embargo_removes_nothing_and_leaves_no_gap(self) -> None:
        """Opting out must be possible, and must be visible in the summary.

        The gap is not asserted to be exactly zero: that depends on how many
        rows share the boundary date, which is a property of the table rather
        than of the splitter. Here two stations per date place the cut on a day
        boundary; the real table has four and lands mid-day, giving the shared
        date EV-005 records. What must hold either way is that no row was
        embargoed and the gap is shorter than the horizon.
        """
        split = chronological_split(_synthetic(), embargo_days=0)
        assert split.n_embargoed == 0
        assert split.gap_days < HORIZON_DAYS

    def test_rows_are_removed_from_training_not_holdout(self) -> None:
        """Shrinking the holdout would move the boundary being measured."""
        frame = _synthetic()
        naive = chronological_split(frame, embargo_days=0)
        embargoed = chronological_split(frame)
        assert len(embargoed.holdout) == len(naive.holdout)
        assert len(embargoed.train) < len(naive.train)
        assert embargoed.n_embargoed == len(naive.train) - len(embargoed.train)

    def test_no_holdout_row_precedes_a_training_row(self) -> None:
        split = chronological_split(_synthetic())
        assert pd.to_datetime(split.train.date).max() < pd.to_datetime(split.holdout.date).min()

    def test_degenerate_input_reports_rather_than_raises(self) -> None:
        empty = chronological_split(_synthetic().iloc[:0])
        assert empty.gap_days is None
        assert empty.summary()["n_holdout"] == 0


class TestPersistence:
    def test_perfect_persistence_scores_zero(self) -> None:
        frame = pd.DataFrame({"fai_now": [0.1, 0.2], "fai_future": [0.1, 0.2]})
        assert persistence_mae(frame) == 0.0

    def test_known_error_is_the_mean_absolute_difference(self) -> None:
        frame = pd.DataFrame({"fai_now": [0.0, 0.0], "fai_future": [0.1, 0.3]})
        assert persistence_mae(frame) == pytest.approx(0.2)

    def test_missing_values_are_dropped_not_imputed(self) -> None:
        frame = pd.DataFrame({"fai_now": [0.0, np.nan], "fai_future": [0.1, 0.9]})
        assert persistence_mae(frame) == pytest.approx(0.1)


class TestTrivialRule:
    def test_group_is_chosen_from_training_data_only(self) -> None:
        """The audit hardcoded `sur`. A permanent check must not encode hindsight."""
        train = pd.DataFrame(
            {"station_id": ["a"] * 10 + ["b"] * 10, "bloom_7d": [1] * 10 + [0] * 10}
        )
        holdout = pd.DataFrame(
            {"station_id": ["a"] * 5 + ["b"] * 5, "bloom_7d": [0] * 5 + [1] * 5}
        )
        rule = trivial_rule(train, holdout)
        # `b` carries every holdout positive, but training said `a` — so `a` is
        # chosen, and the rule scores badly. Choosing `b` here would be leakage.
        assert rule["chosen_group"] == "a"
        assert rule["recall"] == 0.0

    def test_a_label_that_tracks_location_is_caught(self) -> None:
        frame = pd.DataFrame(
            {"station_id": ["a"] * 20 + ["b"] * 20, "bloom_7d": [1] * 20 + [0] * 20}
        )
        rule = trivial_rule(frame, frame)
        assert rule["f1_score"] == pytest.approx(1.0)

    def test_empty_partition_is_reported_as_unavailable(self) -> None:
        frame = pd.DataFrame({"station_id": [], "bloom_7d": []})
        assert trivial_rule(frame, frame)["available"] is False


class TestBeatsBaselines:
    def test_a_loss_is_reported_as_a_loss(self) -> None:
        verdict = beats_baselines(
            {"mae_fai": 0.00865, "f1_score": 0.5985},
            {"persistence": {"mae_fai": 0.00603}, "trivial_rule": {"f1_score": 0.8387}},
        )
        assert verdict == {"persistence": False, "trivial_rule": False}

    def test_a_win_is_reported_as_a_win(self) -> None:
        verdict = beats_baselines(
            {"mae_fai": 0.001, "f1_score": 0.95},
            {"persistence": {"mae_fai": 0.00603}, "trivial_rule": {"f1_score": 0.8387}},
        )
        assert verdict == {"persistence": True, "trivial_rule": True}

    def test_an_undecidable_comparison_is_none_not_true(self) -> None:
        """A missing baseline must never read as a pass."""
        verdict = beats_baselines({"mae_fai": None, "f1_score": 0.9}, {"persistence": {}})
        assert verdict["persistence"] is None
        assert verdict["trivial_rule"] is None


def test_real_dataset_reproduces_both_audit_baselines(pipeline_split, metrics) -> None:
    """End to end on the committed table: EV-002 and EV-003 in one assertion."""
    verdict = beats_baselines(
        metrics["metrics"],
        {
            "persistence": {"mae_fai": persistence_mae(pipeline_split.holdout)},
            "trivial_rule": trivial_rule(pipeline_split.train, pipeline_split.holdout),
        },
    )
    assert verdict == {"persistence": False, "trivial_rule": False}


def test_resorting_a_sorted_frame_is_not_a_no_op(dataset) -> None:
    """Why `split_from_frames` exists rather than re-deriving the partition.

    `DataFrame.sort_values` defaults to quicksort, which is not stable. This
    table carries four rows per date, one per station, so sorting an
    already-sorted frame reorders ties — and on the committed data that moves
    rows across the 80% boundary, changing the holdout. A baseline scored on a
    different holdout than the model is not a baseline, so `train.py` hands over
    the frames it used instead of asking this module to rebuild them.
    """
    once = dataset.sort_values("date").reset_index(drop=True)
    twice = once.sort_values("date").reset_index(drop=True)
    assert not once.equals(twice)

    # Stable sorting is idempotent, which is why chronological_split uses it.
    stable_once = dataset.sort_values("date", kind="stable").reset_index(drop=True)
    stable_twice = stable_once.sort_values("date", kind="stable").reset_index(drop=True)
    assert stable_once.equals(stable_twice)


def test_pipeline_split_matches_train_py_partition(dataset, pipeline_split) -> None:
    """The fixture the MI-1 and MI-2 checks run on is train.py's own partition."""
    frame = (
        dataset.dropna(subset=["bloom_7d", "fai_future"])
        .sort_values("date")
        .reset_index(drop=True)
    )
    n_holdout = max(1, int(len(frame) * 0.2))
    cut = len(frame) - n_holdout

    assert len(pipeline_split.train) == cut
    assert len(pipeline_split.holdout) == n_holdout
    pd.testing.assert_frame_equal(
        pipeline_split.holdout.reset_index(drop=True), frame.iloc[cut:].reset_index(drop=True)
    )
    # And it reproduces the seam EV-005 records.
    assert pipeline_split.gap_days == 0

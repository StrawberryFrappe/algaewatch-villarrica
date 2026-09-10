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
    Split,
    beats_baselines,
    chronological_split,
    persistence_mae,
    split_from_frames,
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


def _variable_horizon(n_days: int = 80, horizon: int = 8) -> pd.DataFrame:
    """One lake-wide unit, dense daily dates, an explicit per-row horizon.

    Shaped like WI-005's lake-anomaly table (ADR-sf-0008): a single spatial
    unit and a `horizon_days` column, because the honest pairs span 5 to 9 days
    rather than a fixed 7 (EV-019).
    """
    dates = pd.date_range("2026-01-01", periods=n_days, freq="D")
    return pd.DataFrame(
        {
            "date": [d.date().isoformat() for d in dates],
            "unit": "lake",
            "fai_now": 0.0,
            "fai_future": 0.0,
            "bloom_7d": 0,
            "horizon_days": horizon,
        }
    )


class TestChronologicalSplitTargetEmbargo:
    """BL-029: the embargo must clear a row's *target* date, not its feature date.

    `chronological_split` filtered training rows on ``t <= first_holdout -
    embargo_days`` where ``t`` is the feature date. A row's target lands at
    ``t + horizon``; with the real 5-to-9-day pass cadence and a fixed 7-day
    embargo, a row at ``t = first_holdout - 7`` with an 8-day horizon has its
    target inside the validation window — EV-005's seam, through a new door.
    `check_chronological_split` compared the gap against the constant
    ``HORIZON_DAYS = 7``, so it reported a pass on that leaking split.
    """

    def test_kept_training_targets_never_reach_the_holdout(self) -> None:
        df = _variable_horizon(horizon=8)
        split = chronological_split(df, horizon_col="horizon_days")
        first_holdout = pd.to_datetime(split.holdout["date"]).min()
        targets = pd.to_datetime(split.train["date"]) + pd.to_timedelta(
            split.train["horizon_days"], unit="D"
        )
        assert (targets <= first_holdout).all()

    def test_split_records_the_tables_own_max_horizon(self) -> None:
        df = _variable_horizon(horizon=8)
        df.loc[df.index[:5], "horizon_days"] = 5  # a mix, max is still 8
        split = chronological_split(df, horizon_col="horizon_days")
        assert split.max_horizon_days == 8
        assert split.summary()["max_horizon_days"] == 8

    def test_a_split_can_carry_its_max_horizon_for_the_gate_to_read(self) -> None:
        """`check_chronological_split` needs the table's own horizon, not a constant.

        The gate-level assertion lives in `test_model_integrity.py`; here we only
        pin that the fact travels on the `Split`.
        """
        ordered = _variable_horizon(horizon=8).sort_values("date").reset_index(drop=True)
        naive = split_from_frames(
            ordered.iloc[: len(ordered) - 16], ordered.iloc[len(ordered) - 16 :], embargo_days=7
        )
        assert naive.max_horizon_days is None
        carried = Split(**{**naive.__dict__, "max_horizon_days": 8})
        assert carried.summary()["max_horizon_days"] == 8

    def test_fixed_horizon_table_without_the_column_is_unchanged(self) -> None:
        """The legacy station table has no horizon column: behaviour must not move."""
        split = chronological_split(_synthetic())
        assert split.max_horizon_days is None
        assert split.gap_days >= HORIZON_DAYS


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


class TestTrivialRuleSingleGroup:
    """BL-030: on one spatial unit the location rule is degenerate.

    `rates.idxmax()` picks the only group and `holdout[group] == chosen` is then
    `True` for every row — "always predict positive", which is neither the
    location rule it documents nor the climatology rule ADR-sf-0008 D2 requires.
    Where the table carries fewer than two groups the baseline becomes "predict
    the training-window mean", using no satellite measurement, which is what
    rule MI-1 actually asks of a trivial rule.
    """

    def test_single_group_predicts_the_prior_never_always_positive(self) -> None:
        train = pd.DataFrame(
            {"station_id": ["lake"] * 20, "bloom_7d": [0] * 16 + [1] * 4}  # base rate 0.20
        )
        holdout = pd.DataFrame(
            {"station_id": ["lake"] * 10, "bloom_7d": [0] * 7 + [1] * 3}
        )
        rule = trivial_rule(train, holdout)
        assert rule["available"] is True
        assert rule["kind"] == "climatology"
        # majority class of a 0.20 prior is 0 — the rule never fires, so it
        # cannot be the always-positive rule BL-030 describes.
        assert rule["recall"] == 0.0
        assert rule["precision"] == 0.0

    def test_single_group_with_a_high_prior_is_still_climatology(self) -> None:
        train = pd.DataFrame({"station_id": ["lake"] * 10, "bloom_7d": [1] * 8 + [0] * 2})
        holdout = pd.DataFrame({"station_id": ["lake"] * 5, "bloom_7d": [1] * 3 + [0] * 2})
        rule = trivial_rule(train, holdout)
        assert rule["kind"] == "climatology"
        assert "mean" in rule["rule"]

    def test_constant_label_single_group_reports_without_an_auc(self) -> None:
        """WI-005's lake table has `bloom_7d` all-zero until recalibration (EV-020)."""
        train = pd.DataFrame({"station_id": ["lake"] * 20, "bloom_7d": [0] * 20})
        holdout = pd.DataFrame({"station_id": ["lake"] * 8, "bloom_7d": [0] * 8})
        rule = trivial_rule(train, holdout)
        assert rule["kind"] == "climatology"
        assert rule["auc_roc"] is None

    def test_multi_group_table_keeps_the_location_rule(self) -> None:
        """EV-002 must still reproduce — the group form is retained for real groups."""
        frame = pd.DataFrame(
            {"station_id": ["a"] * 20 + ["b"] * 20, "bloom_7d": [1] * 20 + [0] * 20}
        )
        rule = trivial_rule(frame, frame)
        assert rule.get("kind") != "climatology"
        assert rule["chosen_group"] == "a"


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

"""WI-005 model layer — Ridge on the standardised lake anomaly (ADR-sf-0008 D1,
ADR-lq-0009).

`src/model/lake_anomaly.py` consumes the table `src/features/lake_anomaly.py`
builds; it never computes FAI (PR-1). No `sentinelhub`, no CUDA — Ridge on ~34
rows.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.features.lake_anomaly import build_anomaly_pairs
from src.model.lake_anomaly import expanding_window_folds, fit_and_evaluate, predict_fai

REPO_ROOT = Path(__file__).resolve().parents[1]
FAI_SERIES = REPO_ROOT / "data" / "processed" / "fai_series_raw.csv"
STATION_THRESHOLD = 0.025916439519215278  # the uncalibrated one, from metrics.json


@pytest.fixture(scope="module")
def pairs() -> pd.DataFrame:
    series = pd.read_csv(FAI_SERIES)
    return build_anomaly_pairs(series, min_prior=5, bloom_threshold=STATION_THRESHOLD)


class TestBackTransform:
    def test_z_zero_is_exactly_climatology(self) -> None:
        """`z_pred = 0` -> predict the causal baseline mean, nothing else."""
        df = pd.DataFrame({"baseline_mean": [0.01, -0.02], "baseline_std": [0.003, 0.004]})
        np.testing.assert_allclose(predict_fai(np.zeros(2), df), df["baseline_mean"])

    def test_z_one_is_one_sigma_above_baseline(self) -> None:
        df = pd.DataFrame({"baseline_mean": [0.01], "baseline_std": [0.003]})
        np.testing.assert_allclose(predict_fai(np.ones(1), df), [0.013])


class TestExpandingWindowFolds:
    def test_folds_are_chronological_and_never_leak_the_target(self, pairs) -> None:
        folds = list(expanding_window_folds(pairs, n_folds=4))
        assert len(folds) == 4
        for train, val in folds:
            first_val = pd.to_datetime(val["date"]).min()
            target_dates = pd.to_datetime(train["date"]) + pd.to_timedelta(
                train["horizon_days"], unit="D"
            )
            assert (target_dates < first_val).all()
            assert pd.to_datetime(train["date"]).max() < first_val

    def test_training_window_expands_each_fold(self, pairs) -> None:
        sizes = [len(train) for train, _ in expanding_window_folds(pairs, n_folds=4)]
        assert sizes == sorted(sizes)
        assert sizes[0] >= 8  # ADR-sf-0008: the smallest fold still trains on ~8+


class TestFitAndEvaluate:
    def test_reports_mae_fai_beside_both_persistence_and_climatology(self, pairs) -> None:
        out = fit_and_evaluate(pairs)
        m = out["metrics"]
        assert isinstance(m["metrics"]["mae_fai"], float) and m["metrics"]["mae_fai"] > 0
        assert m["baselines"]["persistence"]["mae_fai"] > 0
        assert m["baselines"]["climatology"]["mae_fai"] > 0
        assert set(m["beats_baselines"]) == {"persistence", "climatology"}

    def test_cv_reports_a_spread_not_a_single_fold_number(self, pairs) -> None:
        m = fit_and_evaluate(pairs)["metrics"]
        assert m["metrics"]["mae_fai_cv_std"] >= 0.0
        assert len(m["cv"]["fold_mae_fai"]) == m["cv"]["n_folds"]

    def test_classification_metrics_are_null_with_a_recorded_reason(self, pairs) -> None:
        m = fit_and_evaluate(pairs)["metrics"]
        for key in ("precision", "recall", "f1_score", "auc_roc"):
            assert m["metrics"][key] is None
        assert "threshold" in m["classification_reason"].lower()

    def test_a_shrinkage_model_is_reported_against_climatology_not_only_persistence(
        self, pairs
    ) -> None:
        """z_pred=0 reproduces climatology, so beating persistence is nearly free.

        The honest bar is climatology (EV-019: 0.000945 < persistence 0.001333).
        We don't assert the model wins — only that the verdict against climatology
        is actually computed and boolean.
        """
        v = fit_and_evaluate(pairs)["metrics"]["beats_baselines"]
        assert isinstance(v["climatology"], bool)

    def test_runs_end_to_end_on_the_committed_series(self, pairs) -> None:
        out = fit_and_evaluate(pairs)
        assert out["metrics"]["n_pairs"] == len(pairs) == 34
        assert hasattr(out["model"], "predict")


class TestCommittedArtifact:
    """The pickled `ridge.joblib` must not silently diverge from what
    `fit_and_evaluate` produces on the committed table (review recommendation)."""

    def test_committed_pickle_predicts_identically_to_a_fresh_fit(self, pairs) -> None:
        import joblib

        artifact = REPO_ROOT / "src" / "model" / "artifacts" / "lake_anomaly" / "ridge.joblib"
        committed = joblib.load(artifact)
        fresh = fit_and_evaluate(pairs)["model"]
        cols = ["anomaly_now", "horizon_days"]
        np.testing.assert_allclose(
            committed.predict(pairs[cols]), fresh.predict(pairs[cols]), rtol=1e-9, atol=1e-12
        )

    def test_committed_metrics_json_matches_a_fresh_evaluation(self, pairs) -> None:
        import json

        recorded = json.loads(
            (REPO_ROOT / "src" / "model" / "artifacts" / "lake_anomaly" / "metrics.json").read_text()
        )
        fresh = fit_and_evaluate(pairs, bloom_threshold=STATION_THRESHOLD)["metrics"]
        assert fresh["metrics"]["mae_fai"] == recorded["metrics"]["mae_fai"]
        assert fresh["baselines"] == recorded["baselines"]
        assert fresh["beats_baselines"] == recorded["beats_baselines"]

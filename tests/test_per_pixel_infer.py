"""The trained per-pixel artifact must be loadable, not just writable.

Before `src/model/per_pixel_infer.py` existed the artifact was write-only:
`scripts/train_per_pixel.py` saved it and nothing read it back, so a corrupted
or format-drifted artifact would only have been noticed when someone tried to
serve it. These tests exercise the round trip.
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pytest
import torch

from src.model import per_pixel_infer
from src.model.per_pixel import FEATURES, QUANTILES, fit_and_evaluate

from tests.test_per_pixel_model import _frame


@pytest.fixture(scope="module")
def artifact_dir(tmp_path_factory):
    """A real trained artifact, written the way the training script writes it."""
    out = tmp_path_factory.mktemp("per_pixel_artifacts")
    result = fit_and_evaluate(_frame(), epochs=2)
    torch.save(result["artifact"], out / "quantile_mlp.pt")
    (out / "metrics.json").write_text(
        json.dumps(result["metrics"], indent=2) + "\n", encoding="utf-8"
    )
    return out


def test_artifact_loads_under_the_safe_unpickler(artifact_dir):
    """weights_only=True must suffice.

    torch.load defaults to weights_only=True from 2.6 on. If the artifact ever
    carries a plain numpy array again, this fails -- and the only ways to "fix"
    that are to opt back into arbitrary code execution or to notice here.
    """
    loaded = torch.load(
        artifact_dir / "quantile_mlp.pt", map_location="cpu", weights_only=True
    )
    assert set(loaded) == {"state_dict", "feature_mean", "feature_scale", "features", "quantiles"}
    assert torch.is_tensor(loaded["feature_mean"])
    assert torch.is_tensor(loaded["feature_scale"])


def test_load_model_restores_shape_and_scaler(artifact_dir):
    model, scaler, features, quantiles = per_pixel_infer.load_model(
        artifact_dir / "quantile_mlp.pt"
    )
    assert features == list(FEATURES)
    assert quantiles == list(QUANTILES)
    assert not model.training
    assert scaler.mean.shape == (len(FEATURES),)
    assert scaler.scale.shape == (len(FEATURES),)
    assert np.all(scaler.scale != 0), "a zero scale would divide by zero at predict time"


def test_predictions_round_trip_and_stay_ordered(artifact_dir):
    frame = _frame()
    predictions = per_pixel_infer.predict_fai_quantiles(
        frame, path=artifact_dir / "quantile_mlp.pt"
    )
    assert predictions.shape == (len(frame), len(QUANTILES))
    assert np.all(np.isfinite(predictions))
    assert np.all(predictions[:, 0] <= predictions[:, 1])
    assert np.all(predictions[:, 1] <= predictions[:, 2])


def test_predictions_are_deterministic(artifact_dir):
    """Two loads of one artifact must agree, or a served number is not the
    number that was validated."""
    frame = _frame().head(40)
    first = per_pixel_infer.predict_fai_quantiles(frame, path=artifact_dir / "quantile_mlp.pt")
    second = per_pixel_infer.predict_fai_quantiles(frame, path=artifact_dir / "quantile_mlp.pt")
    np.testing.assert_array_equal(first, second)


def test_missing_columns_fail_loudly(artifact_dir):
    frame = _frame().drop(columns=["temp_c"])
    with pytest.raises(ValueError, match="temp_c"):
        per_pixel_infer.predict_fai_quantiles(frame, path=artifact_dir / "quantile_mlp.pt")


def test_missing_artifact_raises_its_own_error(tmp_path):
    """Not FileNotFoundError: callers degrade on this type specifically, and the
    backend turns it into a 404 rather than a 500."""
    with pytest.raises(per_pixel_infer.PerPixelNotTrainedError):
        per_pixel_infer.load_model(tmp_path / "absent.pt")
    with pytest.raises(per_pixel_infer.PerPixelNotTrainedError):
        per_pixel_infer.load_metrics(tmp_path / "absent.json")


def test_back_transform_matches_the_training_path(artifact_dir):
    """Inference must apply the same baseline_mean + z * baseline_std as
    training, or a served prediction is not comparable to the reported mae_fai.
    """
    from src.model.per_pixel import predict_quantiles

    frame = _frame().head(25)
    model, scaler, _features, _q = per_pixel_infer.load_model(artifact_dir / "quantile_mlp.pt")
    from_training_path = predict_quantiles(model, scaler, frame)
    from_inference_path = per_pixel_infer.predict_fai_quantiles(
        frame, path=artifact_dir / "quantile_mlp.pt"
    )
    np.testing.assert_allclose(from_training_path, from_inference_path, rtol=1e-6)


def test_metrics_json_survives_a_utf8_round_trip(artifact_dir):
    """The Spanish caveats are rendered verbatim in the UI. Reading them with
    the platform default encoding produced mojibake on Windows (cp1252)."""
    metrics = per_pixel_infer.load_metrics(artifact_dir / "metrics.json")
    for field in ("caveats", "classification_reason"):
        text = metrics[field]
        assert "Ã" not in text, f"{field} was decoded with the wrong codec"
        assert "�" not in text, f"{field} contains a replacement character"


def test_committed_artifact_is_loadable():
    """The artifact actually in the repository, not a fixture.

    Skipped where the candidate has not been trained, so a fresh clone that has
    not run the training script still gets a green suite.
    """
    try:
        model, _scaler, features, _q = per_pixel_infer.load_model()
        metrics = per_pixel_infer.load_metrics()
    except per_pixel_infer.PerPixelNotTrainedError:
        pytest.skip("no committed per-pixel artifact in this checkout")

    assert features == list(metrics["features_used"])
    assert not model.training
    assert metrics["target_kind"] == "continuous"
    assert metrics["classification"] is None


def test_committed_dataset_predicts_without_error():
    """End to end on the committed table: the artifact and the table agree on
    columns. A drift between them is exactly what would break the API."""
    from pathlib import Path

    dataset = Path("data/processed/per_pixel_anomaly_dataset.csv")
    if not dataset.exists():
        pytest.skip("no committed per-pixel dataset in this checkout")
    try:
        per_pixel_infer.load_model()
    except per_pixel_infer.PerPixelNotTrainedError:
        pytest.skip("no committed per-pixel artifact in this checkout")

    frame = pd.read_csv(dataset).head(200)
    predictions = per_pixel_infer.predict_fai_quantiles(frame)
    assert predictions.shape == (len(frame), 3)
    assert np.all(np.isfinite(predictions))

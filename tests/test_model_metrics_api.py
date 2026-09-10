"""BL-026: displayed metrics must carry their baselines through the API."""

from backend.app.routers.model_metrics import model_metrics


def test_model_metrics_response_exposes_both_baselines_and_verdicts() -> None:
    response = model_metrics()
    assert {"persistence", "trivial_rule"} <= set(response.baselines)
    assert set(response.beats_baselines) == {"persistence", "trivial_rule"}
    assert response.baselines["persistence"]["mae_fai"] is not None
    assert response.baselines["trivial_rule"]["f1_score"] is not None

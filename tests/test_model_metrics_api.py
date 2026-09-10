"""BL-026: displayed metrics must carry their baselines through the API."""

from backend.app.routers.model_metrics import model_metrics


def test_model_metrics_response_exposes_both_baselines_and_verdicts() -> None:
    response = model_metrics()
    assert {"persistence", "trivial_rule"} <= set(response.baselines)
    assert set(response.beats_baselines) == {"persistence", "trivial_rule"}
    assert response.baselines["persistence"]["mae_fai"] is not None
    assert response.baselines["trivial_rule"]["f1_score"] is not None


def test_candidate_endpoint_reports_the_per_pixel_model_and_its_baselines() -> None:
    """The candidate must travel with its baselines, like every other metric
    this project reports (rule MI-1)."""
    import pytest

    from backend.app.routers.model_metrics import model_candidate
    from src.model import per_pixel_infer

    try:
        per_pixel_infer.load_metrics()
    except per_pixel_infer.PerPixelNotTrainedError:
        pytest.skip("no committed per-pixel artifact in this checkout")

    response = model_candidate()

    assert {"persistence", "climatology"} <= set(response.baselines)
    assert set(response.beats_baselines) == {"persistence", "climatology"}
    assert response.baselines["persistence"]["mae_fai"] is not None
    assert response.baselines["climatology"]["mae_fai"] is not None

    # It is evaluated, not deployed. /risk and /forecast still run the legacy
    # artifacts, and the payload has to say so or the client will imply otherwise.
    assert response.serving is False

    # Continuous target: no classification surface may be invented (MI-3).
    assert response.target_kind == "continuous"
    assert response.classification is None
    assert response.classification_reason

    # The fold detail is the honest version of the result and must survive to
    # the client -- the unweighted mean hides that some folds beat climatology.
    assert len(response.folds) == 4
    for fold in response.folds:
        assert fold.n_train > 0 and fold.n_validation > 0
        assert fold.mae_fai > 0 and fold.climatology_mae_fai > 0
        assert 0.0 <= fold.q10_q90_coverage <= 1.0


def test_candidate_endpoint_404s_when_untrained(monkeypatch) -> None:
    """A checkout that never trained the candidate must still serve the
    dashboard: the router 404s and the client hides the panel."""
    from fastapi import HTTPException
    import pytest

    from backend.app.routers import model_metrics as router_module

    monkeypatch.setattr(router_module, "get_per_pixel_metrics", lambda: None)
    with pytest.raises(HTTPException) as excinfo:
        router_module.model_candidate()
    assert excinfo.value.status_code == 404

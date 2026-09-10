from fastapi import APIRouter, HTTPException

from ..data_source import get_model_metrics, get_per_pixel_metrics
from ..schemas import (
    CandidateFold,
    CandidateMetrics,
    CandidateModelResponse,
    ConfusionMatrix,
    FeatureImportance,
    ModelMetricsResponse,
    Validation,
    ValidationMetrics,
)

router = APIRouter(tags=["model"])


@router.get("/model/metrics", response_model=ModelMetricsResponse)
def model_metrics() -> ModelMetricsResponse:
    m = get_model_metrics()

    feature_importance = sorted(
        (
            FeatureImportance(feature=name, importance_pct=round(value * 100, 1))
            for name, value in m["feature_importance"].items()
        ),
        key=lambda f: f.importance_pct,
        reverse=True,
    )

    date_range = m.get("date_range", {})
    period = f"{date_range.get('start', '?')} a {date_range.get('end', '?')}"

    return ModelMetricsResponse(
        version=m["version"],
        fai_alert_threshold=m["fai_alert_threshold"],
        confusion_matrix=ConfusionMatrix(**m["confusion_matrix"]),
        feature_importance=feature_importance,
        metrics=ValidationMetrics(**m["metrics"]),
        baselines=m["baselines"],
        beats_baselines=m["beats_baselines"],
        validation=Validation(
            n_observations=m["n_observations"],
            period=period,
            method="Validación cruzada 5-fold + hold-out temporal",
            horizon_days=7,
            retrained_at=m["retrained_at"],
        ),
        disclaimer=m.get("caveats", "TRL 2 · resultados no validados en campo."),
        source="model",
    )


@router.get("/model/candidate", response_model=CandidateModelResponse)
def model_candidate() -> CandidateModelResponse:
    """The per-pixel quantile model, reported beside its baselines.

    404 when the candidate has not been trained in this checkout, so the client
    can hide the panel rather than render an empty one.
    """
    m = get_per_pixel_metrics()
    if m is None:
        raise HTTPException(
            status_code=404,
            detail="No per-pixel candidate in this checkout — run scripts/train_per_pixel.py.",
        )

    return CandidateModelResponse(
        version=m["version"],
        signal=m["signal"],
        target=m["target"],
        target_kind=m["target_kind"],
        # The candidate is evaluated, not deployed: /risk and /forecast still run
        # the legacy Gradient Boosting artifacts. Saying so in the payload keeps
        # the client from implying the map is running on this model.
        serving=False,
        n_pairs=m["n_pairs"],
        n_pixels=m["n_pixels"],
        n_anchor_dates=m["n_anchor_dates"],
        date_range=m["date_range"],
        features_used=m["features_used"],
        quantiles=m["quantiles"],
        metrics=CandidateMetrics(**{
            k: m["metrics"][k]
            for k in ("mae_fai", "mae_fai_cv_std", "q10_q90_coverage", "mean_interval_width_fai")
        }),
        baselines=m["baselines"],
        beats_baselines=m["beats_baselines"],
        cv_scheme=m["cv"]["scheme"],
        folds=[CandidateFold(**f) for f in m["cv"]["folds"]],
        classification=m["classification"],
        classification_reason=m["classification_reason"],
        disclaimer=m["caveats"],
    )

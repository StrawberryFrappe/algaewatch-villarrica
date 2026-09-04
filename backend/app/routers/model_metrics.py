from fastapi import APIRouter

from ..data_source import get_model_metrics
from ..schemas import (
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

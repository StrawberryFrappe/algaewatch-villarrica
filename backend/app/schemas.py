from typing import Any, Literal

from pydantic import BaseModel

RiskLevel = Literal["MUY_BAJO", "BAJO", "MEDIO", "ALTO"]


class Station(BaseModel):
    id: str
    code: str
    name: str
    sector: str
    lat: float
    lng: float


class Observation(BaseModel):
    date: str  # ISO 8601, YYYY-MM-DD
    station_id: str
    fai: float
    # In-situ sensor fields are None until src/features/insitu.py is wired to
    # real SNIA CSVs — never fabricated.
    water_temp_c: float | None
    ph: float | None
    dissolved_oxygen_mgl: float | None
    wind_speed_kmh: float | None


class StationRisk(BaseModel):
    station_id: str
    risk: int  # 0-100
    level: RiskLevel


class OverlayRef(BaseModel):
    type: Literal["geojson", "raster"]
    url: str
    updated_at: str
    source: Literal["mock", "sentinel2_fai"]


class RiskResponse(BaseModel):
    date: str
    lake_mean_risk: int
    stations: list[StationRisk]
    overlay: OverlayRef
    source: Literal["mock", "model"]


class RiskGridPoint(BaseModel):
    lat: float
    lng: float
    risk: int


class RiskGridResponse(BaseModel):
    date: str  # date of the satellite pass this grid was sampled from
    points: list[RiskGridPoint]
    source: Literal["mock", "model"]


class StationForecast(BaseModel):
    station_id: str
    risk_7d: int
    level_7d: RiskLevel
    delta_vs_previous_week: int
    fai_7d: float | None = None  # regressor's predicted FAI at the horizon date
    confidence_pct: int = 0  # how far the classifier's probability is from 50/50, not the risk itself


class TopStation(BaseModel):
    station_id: str
    name: str
    risk_7d: int
    level_7d: RiskLevel


class ForecastResponse(BaseModel):
    date: str
    horizon_days: int
    generated_at: str
    confidence_pct: int
    lake_mean_risk_7d: int
    stations_in_alert: int
    top_station: TopStation
    stations: list[StationForecast]
    summary: str
    recommendation: str
    ai_generated: bool  # True when summary/recommendation came from Gemini, False when from the template fallback
    disclaimer: str
    source: Literal["mock", "model"]


class ConfusionMatrix(BaseModel):
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


class FeatureImportance(BaseModel):
    feature: str
    importance_pct: float


class ValidationMetrics(BaseModel):
    # Optional: a degenerate hold-out (e.g. single class present) can't
    # produce a meaningful classification metric — reported as null, never
    # fabricated as 0 or 1.
    precision: float | None
    recall: float | None
    f1_score: float | None
    auc_roc: float | None
    mae_fai: float | None


class Validation(BaseModel):
    n_observations: int
    period: str
    method: str
    horizon_days: int
    retrained_at: str


class ModelMetricsResponse(BaseModel):
    version: str
    fai_alert_threshold: float
    confusion_matrix: ConfusionMatrix
    feature_importance: list[FeatureImportance]
    metrics: ValidationMetrics
    baselines: dict[str, Any]
    beats_baselines: dict[str, bool | None]
    validation: Validation
    disclaimer: str
    source: Literal["mock", "model"]


class CandidateFold(BaseModel):
    """One evaluation fold of the per-pixel candidate.

    Carried to the client because the fold detail is the honest version of the
    result: the unweighted mean hides that the model beats climatology on some
    regions and fails badly on the most volatile window.
    """

    fold: int
    held_spatial_block: int
    first_validation_date: str
    last_validation_date: str
    n_train: int
    n_validation: int
    mae_fai: float
    persistence_mae_fai: float
    climatology_mae_fai: float
    q10_q90_coverage: float


class CandidateMetrics(BaseModel):
    mae_fai: float
    mae_fai_cv_std: float
    q10_q90_coverage: float
    mean_interval_width_fai: float


class CandidateModelResponse(BaseModel):
    """The per-pixel quantile model.

    Reported separately from `/model/metrics` because it is a *candidate*: it is
    evaluated and honest, but it does not drive `/risk` or `/forecast`. Merging
    the two would imply the map is running on this model, which it is not.
    `serving` says so explicitly rather than leaving the client to assume.
    """

    version: str
    signal: str
    target: str
    target_kind: Literal["continuous"]
    serving: bool
    n_pairs: int
    n_pixels: int
    n_anchor_dates: int
    date_range: dict[str, str]
    features_used: list[str]
    quantiles: list[float]
    metrics: CandidateMetrics
    baselines: dict[str, Any]
    beats_baselines: dict[str, bool | None]
    cv_scheme: str
    folds: list[CandidateFold]
    classification: None
    classification_reason: str
    disclaimer: str

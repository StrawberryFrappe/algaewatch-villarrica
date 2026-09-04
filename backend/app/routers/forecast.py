from datetime import datetime, timezone

from fastapi import APIRouter, Query

from ..data_source import HORIZON_DAYS, THRESHOLD, get_forecast, get_stations
from ..gemini import generate_ai_summary
from ..schemas import ForecastResponse, StationForecast, TopStation
from .risk import validate_date

router = APIRouter(tags=["forecast"])

ALERT_THRESHOLD = 45  # matches the MEDIO cutoff in the risk scale


def _num_es(value: float, decimals: int) -> str:
    return f"{value:.{decimals}f}".replace(".", ",")


@router.get("/forecast", response_model=ForecastResponse)
async def forecast(date_: str = Query(..., alias="date")) -> ForecastResponse:
    iso_date = validate_date(date_)
    result = get_forecast(iso_date)
    stations_by_id = {s.id: s for s in get_stations()}

    forecasts = [StationForecast(**s) for s in result["stations"]]
    top = max(forecasts, key=lambda f: f.risk_7d)
    top_station = stations_by_id[top.station_id]
    ranked = sorted(forecasts, key=lambda f: f.risk_7d, reverse=True)
    second_station = stations_by_id[ranked[1].station_id]

    confidence = top.confidence_pct

    template_summary = (
        f"Riesgo {top.level_7d.replace('_', ' ').lower()} proyectado en {top_station.name} "
        f"para los próximos {HORIZON_DAYS} días ({top.risk_7d}/100, "
        f"{'+' if top.delta_vs_previous_week >= 0 else '−'}{abs(top.delta_vs_previous_week)} "
        f"vs. el estado actual). El índice FAI proyectado por el modelo es "
        f"{_num_es(top.fai_7d, 4) if top.fai_7d is not None else '—'} "
        f"(umbral de alerta calibrado: {_num_es(THRESHOLD, 4)})."
    )
    template_recommendation = (
        f"Recomendación: reforzar muestreo in situ en {top_station.name} y {second_station.name}; "
        f"activar aviso a la mesa de gestión del lago si el FAI supera {_num_es(THRESHOLD, 4)} "
        "en dos pasadas consecutivas."
    )

    ai_result = await generate_ai_summary({
        "top_station_name": top_station.name,
        "top_risk": top.risk_7d,
        "top_level": top.level_7d.replace("_", " ").capitalize(),
        "delta": top.delta_vs_previous_week,
        "water_temp_c": "sin dato in situ",
        "wind_kmh": "sin dato in situ",
        "fai": _num_es(top.fai_7d, 4) if top.fai_7d is not None else "sin dato",
        "ph": "sin dato in situ",
        "second_station_name": second_station.name,
        "lake_mean_risk_7d": result["lake_mean_risk_7d"],
        "stations_in_alert": result["stations_in_alert"],
    })

    summary = ai_result["summary"] if ai_result else template_summary
    recommendation = ai_result["recommendation"] if ai_result else template_recommendation

    return ForecastResponse(
        date=iso_date,
        horizon_days=HORIZON_DAYS,
        generated_at=datetime.now(timezone.utc).isoformat(),
        confidence_pct=confidence,
        lake_mean_risk_7d=result["lake_mean_risk_7d"],
        stations_in_alert=result["stations_in_alert"],
        top_station=TopStation(
            station_id=top_station.id, name=top_station.name,
            risk_7d=top.risk_7d, level_7d=top.level_7d,
        ),
        stations=forecasts,
        summary=summary,
        recommendation=recommendation,
        ai_generated=ai_result is not None,
        disclaimer="ALGAEWATCH-LM · SÍNTESIS SOBRE LA SALIDA DEL MODELO, NO VALIDADA EN CAMPO",
        source="model",
    )

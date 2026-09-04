from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..data_source import MAX_DATE, MIN_DATE, get_last_satellite_pass, get_risk, get_risk_grid
from ..schemas import OverlayRef, RiskGridPoint, RiskGridResponse, RiskResponse, StationRisk

router = APIRouter(tags=["risk"])


def validate_date(date_: str) -> str:
    try:
        d = date.fromisoformat(date_)
    except ValueError:
        raise HTTPException(422, "Invalid 'date': expected YYYY-MM-DD")
    if not (MIN_DATE <= d.isoformat() <= MAX_DATE):
        raise HTTPException(
            404,
            f"No hay dato satelital útil para {d.isoformat()} "
            f"(rango disponible: {MIN_DATE} a {MAX_DATE})",
        )
    return d.isoformat()


@router.get("/risk", response_model=RiskResponse)
def risk(date_: str = Query(..., alias="date")) -> RiskResponse:
    iso_date = validate_date(date_)
    result = get_risk(iso_date)

    return RiskResponse(
        date=iso_date,
        lake_mean_risk=result["lake_mean_risk"],
        stations=[StationRisk(**s) for s in result["stations"]],
        overlay=OverlayRef(
            type="geojson",
            url="/risk/grid",
            updated_at=get_last_satellite_pass() or iso_date,
            source="sentinel2_fai",
        ),
        source="model",
    )


@router.get("/risk/grid", response_model=RiskGridResponse)
def risk_grid() -> RiskGridResponse:
    """Real FAI grid sampled from the most recent clear Sentinel-2 pass — see
    scripts/collect_fai_grid.py. Not date-parameterized yet: it reflects
    whichever pass that script was last run against.
    """
    result = get_risk_grid()
    return RiskGridResponse(
        date=result["date"],
        points=[RiskGridPoint(**p) for p in result["points"]],
        source="model",
    )

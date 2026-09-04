from datetime import date

from fastapi import APIRouter, HTTPException, Query

from ..data_source import MAX_DATE, MIN_DATE, STATION_IDS, get_observations
from ..schemas import Observation

router = APIRouter(tags=["observations"])


def _parse_date(value: str, param: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise HTTPException(422, f"Invalid '{param}': expected YYYY-MM-DD")


@router.get("/observations", response_model=list[Observation])
def observations(
    from_: str | None = Query(None, alias="from"),
    to: str | None = Query(None),
    station: str | None = Query(None),
) -> list[Observation]:
    start = _parse_date(from_, "from").isoformat() if from_ else MIN_DATE
    end = _parse_date(to, "to").isoformat() if to else MAX_DATE

    if station is not None and station not in STATION_IDS:
        raise HTTPException(404, f"Unknown station '{station}'")

    rows = get_observations(station, start, end)
    return [Observation(**row) for row in rows]

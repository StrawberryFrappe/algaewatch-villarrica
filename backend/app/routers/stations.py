from fastapi import APIRouter

from ..data_source import get_stations
from ..schemas import Station

router = APIRouter(tags=["stations"])


@router.get("/stations", response_model=list[Station])
def stations() -> list[Station]:
    return [
        Station(id=s.id, code=s.code, name=s.name, sector=s.sector, lat=s.lat, lng=s.lng)
        for s in get_stations()
    ]

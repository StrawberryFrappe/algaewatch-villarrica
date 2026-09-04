"""Canonical station catalog — real reference data (which 4 physical IoT
stations exist, and where), not mock. Shared by the feature pipeline and the
backend so there is one source of truth for station identity/location.

TODO: coordinates are placeholders within the lake bbox, pending the real GPS
that will come with the SNIA CSVs (see src/features/insitu.py).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Station:
    id: str
    code: str
    name: str
    sector: str
    lat: float
    lng: float


STATIONS: list[Station] = [
    Station("pucon", "E-01", "Litoral Pucón", "Sector oriente", -39.2810, -71.9720),
    Station("norte", "E-02", "Zona Norte", "Bahía norte", -39.2450, -72.0800),
    Station("tolten", "E-03", "Desembocadura Río Toltén", "Sector poniente", -39.2700, -72.2200),
    Station("sur", "E-04", "Bahía Villarrica (sur)", "Sector sur", -39.3100, -72.0800),
]

STATIONS_BY_ID = {s.id: s for s in STATIONS}
STATION_IDS = [s.id for s in STATIONS]

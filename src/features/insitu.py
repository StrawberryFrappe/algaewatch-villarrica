"""In-situ station data ingestion — STUB.

The user will provide CSVs exported from SNIA (Servicio Nacional de
Información de Aguas) for the 4 stations. Until those arrive, this module
returns clearly-marked mock rows so build_dataset.py has a stable interface
to call, without pretending to have real in-situ data.

TODO once SNIA CSVs are provided: replace load_insitu_csv() to parse the real
file format (columns, units, timestamp format, per-station file layout are
all unknown until then), and update src/features/stations.py with the real
station GPS coordinates the CSVs will contain.
"""

from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "insitu"


def load_insitu_csv(station_id: str, csv_path: Path | None = None) -> pd.DataFrame:
    """STUB. Returns an empty, correctly-shaped DataFrame until real SNIA CSVs
    are wired in. Never fabricates values — callers must handle empty results.
    """
    if csv_path is not None and csv_path.exists():
        raise NotImplementedError(
            "SNIA CSV format not yet defined — implement parsing here once "
            "the real file layout is known."
        )
    return pd.DataFrame(
        columns=["date", "station_id", "water_temp_c", "ph", "dissolved_oxygen_mgl"]
    )


def is_stub() -> bool:
    return True

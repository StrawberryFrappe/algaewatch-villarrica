"""ERA5-Land ingestion via the CDS API — pure feature engineering, no model here.

Fetches daily-aggregated temperature, precipitation and wind over the lake
bbox and reduces each variable to a single lake-area value per day, to be
joined with FAI + in-situ data in build_dataset.py.

NOTE: the CDS account behind CDS_TOKEN must accept the dataset licence once,
manually, at:
  https://cds.climate.copernicus.eu/datasets/derived-era5-land-daily-statistics?tab=download#manage-licences
Without that, every request fails with HTTP 403 "required licences not
accepted" — this is a one-time manual step tied to the account, not something
this code can do for you.
"""

import zipfile
from pathlib import Path

import cdsapi
import numpy as np
import xarray as xr

from .config import CDS_API_URL, CDS_TOKEN, LAKE_BBOX

DATASET = "derived-era5-land-daily-statistics"
VARIABLES = [
    "2m_temperature",
    "total_precipitation",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
]

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "era5"


def _client() -> cdsapi.Client:
    return cdsapi.Client(url=CDS_API_URL, key=CDS_TOKEN)


def _cds_area(bbox=LAKE_BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return [max_lat, min_lon, min_lat, max_lon]  # CDS wants [N, W, S, E]


def fetch_era5_land_day(date_iso: str, statistic: str = "daily_mean", out_dir: Path = RAW_DIR) -> Path:
    """Submits, waits for, and downloads one day of ERA5-Land daily stats.

    Blocks until the CDS queue processes the request (can take from seconds
    to several minutes depending on queue load). Returns the path to the
    downloaded archive (zip of NetCDF files, one per variable).
    """
    year, month, day = date_iso.split("-")
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"era5_land_{date_iso}_{statistic}.zip"

    client = _client()
    client.retrieve(
        DATASET,
        {
            "variable": VARIABLES,
            "year": year,
            "month": month,
            "day": [day],
            "daily_statistic": statistic,
            "time_zone": "utc+00:00",
            "frequency": "1_hourly",
            "area": _cds_area(),
        },
        str(target),
    )
    return target


def load_daily_means(zip_path: Path) -> dict:
    """Unzips a fetch_era5_land_day() result and reduces each variable to a
    single bbox-mean value for that day.

    Returns: {"temp_c": float, "precip_mm": float, "wind_kmh": float}
    """
    extract_dir = zip_path.with_suffix("")
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    nc_files = list(extract_dir.glob("*.nc"))
    if not nc_files:
        raise FileNotFoundError(f"No .nc files found in {zip_path}")

    values = {}
    for nc_path in nc_files:
        ds = xr.open_dataset(nc_path)
        for var in ds.data_vars:
            values[var] = float(ds[var].mean().values)
        ds.close()

    temp_c = values.get("t2m", values.get("2m_temperature"))
    if temp_c is not None and temp_c > 200:  # Kelvin -> Celsius
        temp_c -= 273.15

    precip_m = values.get("tp", values.get("total_precipitation"))
    precip_mm = precip_m * 1000 if precip_m is not None else None

    u = values.get("u10", values.get("10m_u_component_of_wind"))
    v = values.get("v10", values.get("10m_v_component_of_wind"))
    wind_kmh = float(np.hypot(u, v) * 3.6) if u is not None and v is not None else None

    return {"temp_c": temp_c, "precip_mm": precip_mm, "wind_kmh": wind_kmh}

"""ERA5-Land ingestion via the CDS API — pure feature engineering, no model here.

Fetches hourly temperature, precipitation and wind over the lake bbox, reduces
them to one lake-area value per UTC day, and joins them to the real Sentinel-2
pass dates downstream.

NOTE: the CDS account behind CDS_TOKEN must accept the ERA5-Land dataset licence
once, manually, in the CDS dataset page.
Without that, every request fails with HTTP 403 "required licences not
accepted" — this is a one-time manual step tied to the account, not something
this code can do for you.
"""

import zipfile
from pathlib import Path

import cdsapi
import numpy as np
import pandas as pd
import xarray as xr

from .config import CDS_API_URL, CDS_TOKEN, LAKE_BBOX

HOURLY_DATASET = "reanalysis-era5-land"
HOURLY_VARIABLES = [
    "2m_temperature",
    "10m_u_component_of_wind",
    "10m_v_component_of_wind",
    "total_precipitation",
]
PRECIP_VARIABLE = "total_precipitation"

RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw" / "era5"


def _client() -> cdsapi.Client:
    return cdsapi.Client(url=CDS_API_URL, key=CDS_TOKEN)


def _cds_area(bbox=LAKE_BBOX):
    min_lon, min_lat, max_lon, max_lat = bbox
    return [max_lat, min_lon, min_lat, max_lon]  # CDS wants [N, W, S, E]


def _precip_path(daily_zip: Path) -> Path:
    return daily_zip.with_name(daily_zip.stem + "_total_precipitation.nc")


def fetch_era5_land_dates(
    dates: list[str], statistic: str = "daily_mean", out_dir: Path = RAW_DIR
) -> Path:
    """Fetch one calendar month's hourly fields in one resumable request.

    Temperature and wind are averaged by UTC day and precipitation is summed
    locally. This avoids the derived daily-statistics queue, whose product also
    omits accumulated variables such as total precipitation.
    """
    if not dates:
        raise ValueError("At least one date is required")
    parsed = pd.to_datetime(pd.Series(dates), errors="raise")
    months = parsed.dt.strftime("%Y-%m").unique()
    if len(months) != 1:
        raise ValueError("fetch_era5_land_dates accepts dates from one calendar month")

    year = parsed.dt.strftime("%Y").iloc[0]
    month = parsed.dt.strftime("%m").iloc[0]
    # Fetch the small continuous span bounded by the first/last pass in the
    # month, then filter locally after daily aggregation.
    # ERA5-Land accumulated fields stamped at D+1 00 UTC describe day D.
    # All project month groups end before the calendar boundary, so including
    # one extra day remains a valid single-month request.
    request_end = parsed.max() + pd.Timedelta(days=1)
    if request_end.month != parsed.max().month:
        raise ValueError("A month-end observation requires a split precipitation request")
    days = pd.date_range(parsed.min(), request_end, freq="D").strftime("%d").tolist()
    month_key = months[0]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"era5_land_{month_key}_hourly-v2.nc"

    client = _client()
    if not target.exists():
        client.retrieve(
            HOURLY_DATASET,
            {
                "variable": HOURLY_VARIABLES,
                "year": year,
                "month": month,
                "day": days,
                "time": [f"{hour:02d}:00" for hour in range(24)],
                "data_format": "netcdf",
                "download_format": "unarchived",
                "area": _cds_area(),
            },
            str(target),
        )
    return target


def fetch_era5_land_day(date_iso: str, statistic: str = "daily_mean", out_dir: Path = RAW_DIR) -> Path:
    """Submit, wait for and download one day of hourly ERA5-Land fields.

    Blocks until the CDS queue processes the request (can take from seconds
    to several minutes depending on queue load). Daily statistics are computed
    by :func:`load_era5_dates` rather than requested as a separate CDS product.
    """
    return fetch_era5_land_dates([date_iso], statistic=statistic, out_dir=out_dir)


def _spatial_mean(data: xr.DataArray) -> xr.DataArray:
    dims = [dim for dim in ("latitude", "longitude") if dim in data.dims]
    return data.mean(dim=dims) if dims else data


def load_era5_dates(zip_path: Path) -> pd.DataFrame:
    """Reduce a monthly download to one row per actual UTC date."""
    if zip_path.suffix == ".nc":
        return _load_hourly_dates(zip_path)

    extract_dir = zip_path.with_suffix("")
    extract_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(extract_dir)

    nc_files = list(extract_dir.glob("*.nc"))
    if not nc_files:
        raise FileNotFoundError(f"No .nc files found in {zip_path}")

    series: dict[str, pd.Series] = {}
    for nc_path in nc_files:
        with xr.open_dataset(nc_path) as ds:
            for var in ds.data_vars:
                values = _spatial_mean(ds[var])
                time_dim = next((d for d in ("valid_time", "time") if d in values.dims), None)
                if time_dim is None:
                    continue
                index = pd.to_datetime(values[time_dim].values).normalize()
                series[var] = pd.Series(np.asarray(values.values, dtype=float), index=index)

    temp = series.get("t2m", series.get("2m_temperature"))
    u = series.get("u10", series.get("10m_u_component_of_wind"))
    v = series.get("v10", series.get("10m_v_component_of_wind"))

    precip_path = _precip_path(zip_path)
    precip = None
    if precip_path.exists():
        with xr.open_dataset(precip_path) as ds:
            data = ds.get("tp", ds.get(PRECIP_VARIABLE))
            if data is not None:
                values = _spatial_mean(data)
                time_dim = next((d for d in ("valid_time", "time") if d in values.dims), None)
                if time_dim is not None:
                    times = pd.to_datetime(values[time_dim].values).normalize()
                    precip = pd.Series(np.asarray(values.values, dtype=float), index=times).groupby(
                        level=0
                    ).sum() * 1000

    indexes = [item.index for item in (temp, u, v, precip) if item is not None]
    if not indexes:
        return pd.DataFrame(columns=["date", "temp_c", "precip_mm", "wind_kmh"])
    index = indexes[0]
    for other in indexes[1:]:
        index = index.union(other)
    frame = pd.DataFrame(index=index.sort_values())
    frame["temp_c"] = temp.reindex(frame.index) - 273.15 if temp is not None else np.nan
    frame["precip_mm"] = precip.reindex(frame.index) if precip is not None else np.nan
    if u is not None and v is not None:
        frame["wind_kmh"] = np.hypot(u.reindex(frame.index), v.reindex(frame.index)) * 3.6
    else:
        frame["wind_kmh"] = np.nan
    frame.index.name = "date"
    return frame.reset_index().assign(date=lambda d: d["date"].dt.date.astype(str))


def _load_hourly_dates(nc_path: Path) -> pd.DataFrame:
    """Aggregate one hourly ERA5-Land NetCDF to UTC daily lake means."""
    with xr.open_dataset(nc_path) as ds:
        variables: dict[str, pd.Series] = {}
        for canonical, aliases in {
            "temp": ("t2m", "2m_temperature"),
            "u": ("u10", "10m_u_component_of_wind"),
            "v": ("v10", "10m_v_component_of_wind"),
            "precip": ("tp", PRECIP_VARIABLE),
        }.items():
            data = next((ds.get(name) for name in aliases if ds.get(name) is not None), None)
            if data is None:
                raise ValueError(f"ERA5 hourly file lacks {canonical}: {nc_path}")
            values = _spatial_mean(data)
            time_dim = next((d for d in ("valid_time", "time") if d in values.dims), None)
            if time_dim is None:
                raise ValueError(f"ERA5 hourly file lacks a time dimension: {nc_path}")
            index = pd.to_datetime(values[time_dim].values)
            variables[canonical] = pd.Series(np.asarray(values.values, dtype=float), index=index)

    temp_grouped = variables["temp"].groupby(variables["temp"].index.normalize())
    complete_dates = temp_grouped.count().loc[lambda count: count == 24].index
    daily = pd.DataFrame(index=complete_dates.sort_values())
    daily["temp_c"] = temp_grouped.mean() - 273.15
    u = variables["u"].groupby(variables["u"].index.normalize()).mean()
    v = variables["v"].groupby(variables["v"].index.normalize()).mean()
    daily["wind_kmh"] = np.hypot(u, v) * 3.6
    precip = variables["precip"]
    midnight = precip.loc[precip.index.hour == 0].copy()
    midnight.index = midnight.index - pd.Timedelta(days=1)
    daily["precip_mm"] = midnight.groupby(level=0).last() * 1000
    daily.index.name = "date"
    return daily.reset_index().assign(date=lambda d: d["date"].dt.date.astype(str))[
        ["date", "temp_c", "precip_mm", "wind_kmh"]
    ]


def load_daily_means(zip_path: Path) -> dict:
    """Unzips a fetch_era5_land_day() result and reduces each variable to a
    single bbox-mean value for that day.

    Returns: {"temp_c": float, "precip_mm": float, "wind_kmh": float}.
    ``precip_mm`` is the bbox-mean sum of the 24 hourly accumulations.
    """
    frame = load_era5_dates(zip_path)
    if len(frame) != 1:
        raise ValueError(f"Expected one ERA5 day in {zip_path}, found {len(frame)}")
    row = frame.iloc[0]
    return {
        "temp_c": float(row["temp_c"]),
        "precip_mm": float(row["precip_mm"]),
        "wind_kmh": float(row["wind_kmh"]),
    }


def collect_era5_days(dates: list[str], out_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Fetch and reduce ERA5-Land for real observation dates only.

    The function is resumable because :func:`fetch_era5_land_day` reuses both
    downloaded files. A failed or incomplete day raises instead of fabricating
    a row with null measurements (PR-3).
    """
    requested = pd.DataFrame({"date": sorted(set(dates))})
    requested["month"] = requested["date"].str[:7]
    frames = []
    for month, group in requested.groupby("month", sort=True):
        month_dates = group["date"].tolist()
        daily_zip = fetch_era5_land_dates(month_dates, out_dir=out_dir)
        frame = load_era5_dates(daily_zip)
        frame = frame[frame["date"].isin(month_dates)]
        if (
            len(frame) != len(month_dates)
            or frame[["temp_c", "precip_mm", "wind_kmh"]].isna().any().any()
        ):
            raise ValueError(f"ERA5 month {month} is incomplete")
        frames.append(frame)
        print(f"  [ok] {month}: {len(frame)}/{len(month_dates)} requested days")

    out = pd.concat(frames, ignore_index=True).sort_values("date", kind="stable")
    # Left-join onto the requested dates so the output is ordered by request and
    # a silently absent day surfaces as NaN below rather than as a short frame.
    # `requested[["date"]]` already projects `month` away; the loaded frames never
    # carried it, so there is nothing left to drop here.
    out = requested[["date"]].merge(out, on="date", how="left")
    missing = out.loc[out[["temp_c", "precip_mm", "wind_kmh"]].isna().any(axis=1), "date"]
    if len(missing):
        raise ValueError(f"ERA5 is incomplete for: {', '.join(missing)}")
    return out

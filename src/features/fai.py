"""FAI (Floating Algae Index) from Sentinel-2 L2A — pure feature engineering.

FAI is a FORMULA over spectral bands, not a model: it has no training step and
predicts nothing by itself. This module only computes it from raw reflectance.
The model (src/model) later consumes a historical *window* of this value as
one of its input features — this file must never import from src/model.

Reference (Hu, 2009): FAI = R_NIR - R'_NIR, where R'_NIR is the red-SWIR
linearly interpolated reflectance at the NIR wavelength:
    R'_NIR = R_RED + (R_SWIR - R_RED) * (lambda_NIR - lambda_RED) / (lambda_SWIR - lambda_RED)

For Sentinel-2: RED = B04 (665 nm), NIR = B08 (842 nm), SWIR = B11 (1610 nm).
"""

import numpy as np
from sentinelhub import BBox, CRS, DataCollection, MimeType, SentinelHubRequest, bbox_to_dimensions

from .config import LAKE_BBOX, sentinelhub_config

LAMBDA_RED, LAMBDA_NIR, LAMBDA_SWIR = 665.0, 842.0, 1610.0
SCL_WATER = 6

_EVALSCRIPT = """
//VERSION=3
function setup() {
  return {
    input: ["B04", "B08", "B11", "SCL"],
    output: { bands: 4, sampleType: "FLOAT32" }
  };
}
function evaluatePixel(sample) {
  return [sample.B04, sample.B08, sample.B11, sample.SCL];
}
"""


def _s2l2a_collection():
    config = sentinelhub_config()
    return DataCollection.SENTINEL2_L2A.define_from("s2l2a_cdse", service_url=config.sh_base_url)


class FaiRaster:
    """A single date's FAI raster over the lake bbox, plus a water mask."""

    def __init__(self, fai, is_water, bbox, width, height):
        self.fai = fai  # (H, W) float32, NaN where not water
        self.is_water = is_water  # (H, W) bool
        self.bbox = bbox  # (min_lon, min_lat, max_lon, max_lat)
        self.width = width
        self.height = height

    def lake_mean(self) -> float | None:
        values = self.fai[self.is_water]
        return float(np.nanmean(values)) if values.size else None

    def sample_grid(self, stride_px: int = 15, *, include_pixel_id: bool = False) -> list[dict]:
        """Downsamples the water pixels to a grid for the map's real heatmap
        overlay (every stride_px-th pixel in each axis — stride_px=15 at 20m
        resolution is a ~300m grid, a few hundred to ~2000 points depending on
        lake size, small enough for a JSON payload / leaflet.heat).
        """
        min_lon, min_lat, max_lon, max_lat = self.bbox
        points = []
        for row in range(0, self.height, stride_px):
            for col in range(0, self.width, stride_px):
                if not self.is_water[row, col]:
                    continue
                lon = min_lon + (col / self.width) * (max_lon - min_lon)
                lat = max_lat - (row / self.height) * (max_lat - min_lat)
                value = self.fai[row, col]
                if np.isnan(value):
                    continue
                point = {"lat": round(lat, 5), "lng": round(lon, 5), "fai": round(float(value), 5)}
                if include_pixel_id:
                    # Raster geometry is fixed by LAKE_BBOX + resolution, so
                    # row/column is stable across passes even when clouds or
                    # the SCL mask make a pixel absent on one date.
                    point["pixel_id"] = f"r{row:04d}_c{col:04d}"
                points.append(point)
        return points

    def at_latlon(self, lat: float, lon: float, max_radius_px: int = 60) -> float | None:
        """Nearest water pixel to (lat, lon), expanding a search window if needed."""
        min_lon, min_lat, max_lon, max_lat = self.bbox
        col = int((lon - min_lon) / (max_lon - min_lon) * self.width)
        # Row 0 is the top (max_lat) in the array returned by SentinelHubRequest.
        row = int((max_lat - lat) / (max_lat - min_lat) * self.height)
        col = min(max(col, 0), self.width - 1)
        row = min(max(row, 0), self.height - 1)

        for radius in range(max_radius_px + 1):
            r0, r1 = max(0, row - radius), min(self.height, row + radius + 1)
            c0, c1 = max(0, col - radius), min(self.width, col + radius + 1)
            window_mask = self.is_water[r0:r1, c0:c1]
            if window_mask.any():
                window_fai = self.fai[r0:r1, c0:c1]
                return float(np.nanmean(window_fai[window_mask]))
        return None


def fetch_fai_raster(date_iso: str, bbox=LAKE_BBOX, resolution_m: int = 20) -> FaiRaster:
    """Fetches one Sentinel-2 L2A scene for the given day and computes FAI.

    Picks the least-cloudy scene covering the lake on that calendar date. Raises
    if no scene is found (e.g. no overpass that day — ~5 day revisit cadence).
    """
    config = sentinelhub_config()
    sh_bbox = BBox(bbox, crs=CRS.WGS84)
    size = bbox_to_dimensions(sh_bbox, resolution=resolution_m)

    request = SentinelHubRequest(
        evalscript=_EVALSCRIPT,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=_s2l2a_collection(),
                time_interval=(f"{date_iso}T00:00:00", f"{date_iso}T23:59:59"),
                mosaicking_order="leastCC",
            )
        ],
        responses=[SentinelHubRequest.output_response("default", MimeType.TIFF)],
        bbox=sh_bbox,
        size=size,
        config=config,
    )
    data = request.get_data()
    if not data:
        raise ValueError(f"No Sentinel-2 L2A data returned for {date_iso} over {bbox}")

    arr = data[0].astype(np.float32)  # (H, W, 4): B04, B08, B11, SCL
    red, nir, swir, scl = arr[..., 0], arr[..., 1], arr[..., 2], arr[..., 3]

    r_prime_nir = red + (swir - red) * (LAMBDA_NIR - LAMBDA_RED) / (LAMBDA_SWIR - LAMBDA_RED)
    fai = nir - r_prime_nir
    is_water = scl == SCL_WATER

    return FaiRaster(fai=fai, is_water=is_water, bbox=bbox, width=size[0], height=size[1])

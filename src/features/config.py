"""Shared config for the feature pipeline (Sentinel-2 FAI + ERA5-Land).

Credentials come from the repo-root .env (CDS_TOKEN, CDSE_CLIENT_ID,
CDSE_CLIENT_SECRET) via find_dotenv(), so this works unchanged on a server
with a different absolute path.
"""

import os

from dotenv import find_dotenv, load_dotenv
from sentinelhub import SHConfig

load_dotenv(find_dotenv())

# Lake Villarrica bounding box: [min_lon, min_lat, max_lon, max_lat]
LAKE_BBOX = (-72.35, -39.35, -71.95, -39.20)

CDSE_CLIENT_ID = os.environ.get("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.environ.get("CDSE_CLIENT_SECRET")
CDS_TOKEN = os.environ.get("CDS_TOKEN")

CDS_API_URL = "https://cds.climate.copernicus.eu/api"


def sentinelhub_config() -> SHConfig:
    """SHConfig wired to Copernicus Data Space Ecosystem (not the old sentinel-hub.com)."""
    config = SHConfig()
    config.sh_client_id = CDSE_CLIENT_ID
    config.sh_client_secret = CDSE_CLIENT_SECRET
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
    return config

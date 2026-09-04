import os

from dotenv import find_dotenv, load_dotenv

# find_dotenv() walks up from the current working directory, so this
# resolves correctly whether the app is run from backend/, the project
# root, or a server deployment with a different absolute path.
load_dotenv(find_dotenv())

CDS_TOKEN = os.environ.get("CDS_TOKEN")
CDSE_CLIENT_ID = os.environ.get("CDSE_CLIENT_ID")
CDSE_CLIENT_SECRET = os.environ.get("CDSE_CLIENT_SECRET")
MAPBOX_ACCESS_TOKEN = os.environ.get("MAPBOX_ACCESS_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

CORS_ORIGINS = [
    origin.strip()
    for origin in os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if origin.strip()
]

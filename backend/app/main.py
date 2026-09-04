from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import CORS_ORIGINS
from .routers import forecast, model_metrics, observations, risk, stations

app = FastAPI(
    title="AlgaeWatch Villarrica API",
    description=(
        "Backend for AlgaeWatch Villarrica. /risk reads real Sentinel-2 FAI "
        "directly; /forecast runs the trained Gradient Boosting model. "
        "In-situ fields are null pending real SNIA data (see data_source.py)."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(stations.router)
app.include_router(observations.router)
app.include_router(risk.router)
app.include_router(forecast.router)
app.include_router(model_metrics.router)


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok"}

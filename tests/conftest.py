"""Shared fixtures.

Everything here reads committed CSVs. No test touches the network, needs
credentials, or retrains a model — the suite has to be runnable by anyone who
clones the repository, including a reviewer checking a claim.

The dataset path is overridable so the same gate can be pointed at a candidate
table without editing tests:

    ALGAEWATCH_DATASET=data/processed/candidate.csv pytest

That matters for WI-005: the retrain is judged by exactly these checks, not by
a second set written to suit it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
PROCESSED = REPO_ROOT / "data" / "processed"

DEFAULT_DATASET = PROCESSED / "training_dataset.csv"
FAI_SERIES = PROCESSED / "fai_series_raw.csv"
FAI_GRID = PROCESSED / "fai_grid_latest.csv"
METRICS = REPO_ROOT / "src" / "model" / "artifacts" / "metrics.json"


@pytest.fixture(scope="session")
def dataset_path() -> Path:
    override = os.environ.get("ALGAEWATCH_DATASET")
    return Path(override) if override else DEFAULT_DATASET


@pytest.fixture(scope="session")
def dataset(dataset_path: Path) -> pd.DataFrame:
    """The training table under test."""
    return pd.read_csv(dataset_path)


@pytest.fixture(scope="session")
def fai_series() -> pd.DataFrame:
    """Real Sentinel-2 readings, one row per pass date, one column per station."""
    return pd.read_csv(FAI_SERIES)


@pytest.fixture(scope="session")
def fai_grid() -> pd.DataFrame:
    """Water pixels sampled from a single pass — the water reference."""
    return pd.read_csv(FAI_GRID)


@pytest.fixture(scope="session")
def metrics() -> dict:
    return json.loads(METRICS.read_text())


@pytest.fixture(scope="session")
def bloom_threshold(metrics: dict) -> float:
    return metrics["fai_alert_threshold"]


@pytest.fixture(scope="session")
def stations() -> list[dict]:
    """The station catalogue as plain data.

    Imported here rather than inside `src/model/`, which PR-1 forbids from
    importing `src/features/`. A test is not `src/model/`, so it may read the
    catalogue and hand it over.
    """
    from src.features.stations import STATIONS

    return [{"id": s.id, "lat": s.lat, "lng": s.lng, "name": s.name} for s in STATIONS]


@pytest.fixture(scope="session")
def pipeline_split(dataset: pd.DataFrame):
    """The split the audited training path actually performs.

    `src/model/train.py` slices the date-sorted frame at 80% and stops, with no
    embargo. Reproducing that here — rather than asserting against the embargoed
    splitter — is what keeps the MI-2 check from grading its own homework.
    """
    from src.model.baselines import chronological_split

    return chronological_split(dataset, embargo_days=0)


@pytest.fixture(scope="session")
def embargoed_split(dataset: pd.DataFrame):
    """The split MI-2 requires: chronological, with a horizon-length embargo."""
    from src.model.baselines import chronological_split

    return chronological_split(dataset)

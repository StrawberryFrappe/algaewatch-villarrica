"""Loads the trained artifacts and scores new feature rows. This is the only
module that should be imported by the backend once /risk and /forecast switch
from mock_data.py to real predictions (a later step, not wired in yet).
"""

import json
from pathlib import Path

import joblib
import pandas as pd

from .train import ARTIFACTS_DIR


class ModelNotTrainedError(RuntimeError):
    pass


def load_artifacts(artifacts_dir: Path = ARTIFACTS_DIR) -> dict:
    metrics_path = artifacts_dir / "metrics.json"
    classifier_path = artifacts_dir / "classifier.joblib"
    regressor_path = artifacts_dir / "regressor.joblib"
    if not (metrics_path.exists() and classifier_path.exists() and regressor_path.exists()):
        raise ModelNotTrainedError(
            f"No trained model found in {artifacts_dir} — run src/model/train.py first."
        )
    return {
        "classifier": joblib.load(classifier_path),
        "regressor": joblib.load(regressor_path),
        "metrics": json.loads(metrics_path.read_text()),
    }


def predict_risk(artifacts: dict, feature_row: dict) -> dict:
    """feature_row must contain (at least) the columns in
    artifacts['metrics']['features_used']. Missing/NaN values are tolerated
    (the classifier/regressor were fit on median-imputed data), but callers
    should prefer supplying real values.

    Returns: {"risk": int (0-100), "bloom_probability": float, "fai_7d": float}
    """
    features = artifacts["metrics"]["features_used"]
    X = pd.DataFrame([{f: feature_row.get(f) for f in features}])
    proba = float(artifacts["classifier"].predict_proba(X)[0, 1])
    fai_7d = float(artifacts["regressor"].predict(X)[0])
    return {
        "risk": round(proba * 100),
        "bloom_probability": proba,
        "fai_7d": fai_7d,
    }

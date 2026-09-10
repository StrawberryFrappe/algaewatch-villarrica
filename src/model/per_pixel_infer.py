"""Load the trained per-pixel quantile model and predict with it.

Counterpart to `src/model/per_pixel.py`, which trains and writes the artifact.
Until this module existed the artifact was write-only: `scripts/train_per_pixel.py`
saved `quantile_mlp.pt` and nothing ever read it back, so the trained model could
not reach the API. Mirrors `src/model/infer.py`, which does the same job for the
legacy Gradient Boosting artifacts.

Kept separate from `per_pixel.py` on purpose: the backend must be able to load a
model without importing the training path, so `src/features` and the training
loop stay off the request path.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from .per_pixel import FeatureScaler, QuantileMLP

ARTIFACT_DIR = Path(__file__).resolve().parent / "artifacts" / "per_pixel"
MODEL_PATH = ARTIFACT_DIR / "quantile_mlp.pt"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"


class PerPixelNotTrainedError(RuntimeError):
    """Raised when the artifact is missing, so callers can degrade explicitly."""


def load_metrics(path: Path = METRICS_PATH) -> dict:
    if not path.exists():
        raise PerPixelNotTrainedError(
            f"{path} not found — run scripts/train_per_pixel.py first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def load_artifact(path: Path = MODEL_PATH) -> dict:
    """Read the saved artifact dict under torch's safe unpickler.

    `weights_only=True` is the secure default from torch 2.6 on: it refuses to
    execute arbitrary code while unpickling. The artifact is written to suit it —
    `per_pixel.fit_and_evaluate` stores the scaler as tensors rather than numpy
    arrays, because numpy arrays are rejected by that unpickler and would
    otherwise force every reader to opt back into `weights_only=False` just to
    read our own normalisation constants.

    Keeping the scaler inside the same file, rather than in a second one, is
    deliberate: separable halves are how a model ends up served with the wrong
    normalisation.
    """
    if not path.exists():
        raise PerPixelNotTrainedError(
            f"{path} not found — run scripts/train_per_pixel.py first."
        )
    return torch.load(path, map_location="cpu", weights_only=True)


def load_model(path: Path = MODEL_PATH) -> tuple[QuantileMLP, FeatureScaler, list[str], list[float]]:
    """Rebuild the network and its scaler from the artifact.

    The network is sized from the artifact's own feature list rather than from
    the module-level `FEATURES` constant, so an artifact trained on a different
    feature set loads correctly instead of failing with a shape error or, worse,
    silently mismatching.
    """
    artifact = load_artifact(path)
    features = list(artifact["features"])
    model = QuantileMLP(n_features=len(features))
    model.load_state_dict(artifact["state_dict"])
    model.eval()
    scaler = FeatureScaler(
        mean=np.asarray(artifact["feature_mean"], dtype=float),
        scale=np.asarray(artifact["feature_scale"], dtype=float),
    )
    return model, scaler, features, list(artifact["quantiles"])


def predict_fai_quantiles(
    frame: pd.DataFrame,
    *,
    path: Path = MODEL_PATH,
) -> np.ndarray:
    """Predict FAI quantiles for rows of an already-built per-pixel table.

    Returns an (n, 3) array in raw FAI units, columns ordered q10, q50, q90.
    The model predicts a standardised anomaly, so the back-transform
    `fai = baseline_mean + z * baseline_std` is applied here — the same one
    `per_pixel.predict_quantiles` uses at training time, so a prediction served
    by the API is directly comparable to the reported `mae_fai`.
    """
    model, scaler, features, _quantiles = load_model(path)

    missing = [c for c in [*features, "baseline_mean", "baseline_std"] if c not in frame.columns]
    if missing:
        raise ValueError(f"Frame is missing required columns: {missing}")

    values = frame[features].to_numpy(dtype=np.float32)
    inputs = torch.from_numpy(scaler.transform(values).astype(np.float32))
    with torch.no_grad():
        anomaly = model(inputs).numpy()

    baseline = frame["baseline_mean"].to_numpy(dtype=float).reshape(-1, 1)
    spread = frame["baseline_std"].to_numpy(dtype=float).reshape(-1, 1)
    return baseline + anomaly * spread

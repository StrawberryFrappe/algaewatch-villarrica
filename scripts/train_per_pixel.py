"""Train and persist the per-pixel PyTorch quantile model."""

import json
import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.model.per_pixel import fit_and_evaluate  # noqa: E402

DATASET = ROOT / "data" / "processed" / "per_pixel_anomaly_dataset.csv"
ARTIFACTS = ROOT / "src" / "model" / "artifacts" / "per_pixel"


def main() -> int:
    frame = pd.read_csv(DATASET)
    print(
        f"Training on {len(frame)} honest pairs, {frame.pixel_id.nunique()} pixels, "
        f"{frame.date.nunique()} anchor dates"
    )
    result = fit_and_evaluate(frame)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    torch.save(result["artifact"], ARTIFACTS / "quantile_mlp.pt")
    (ARTIFACTS / "metrics.json").write_text(
        json.dumps(result["metrics"], indent=2) + "\n", encoding="utf-8"
    )
    metrics = result["metrics"]
    print(
        "MAE {:.6f} +/- {:.6f} | persistence {:.6f} | climatology {:.6f}".format(
            metrics["metrics"]["mae_fai"],
            metrics["metrics"]["mae_fai_cv_std"],
            metrics["baselines"]["persistence"]["mae_fai"],
            metrics["baselines"]["climatology"]["mae_fai"],
        )
    )
    print("Beats baselines:", metrics["beats_baselines"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

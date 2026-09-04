"""Builds the unified dataset from the collected FAI series and trains the
model. Run from the project root: .venv/bin/python scripts/train_model.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from src.features.build_dataset import build_unified_dataset
from src.model.train import save_artifacts, train

FAI_CSV = Path(__file__).resolve().parents[1] / "data" / "processed" / "fai_series_raw.csv"
DATASET_CSV = Path(__file__).resolve().parents[1] / "data" / "processed" / "training_dataset.csv"

if __name__ == "__main__":
    fai_df = pd.read_csv(FAI_CSV)
    print(f"Loaded {len(fai_df)} FAI observations from {FAI_CSV}")

    dataset, threshold = build_unified_dataset(fai_df)
    dataset.to_csv(DATASET_CSV, index=False)
    print(f"Built unified dataset: {len(dataset)} rows, bloom_threshold={threshold:.4f}")
    print(f"Saved to {DATASET_CSV}")

    if dataset.empty:
        print("Dataset is empty — not enough FAI history to build lag features "
              "and a 7-day-ahead target yet. Need a longer collection window.")
        sys.exit(1)

    result = train(dataset, bloom_threshold=threshold)
    save_artifacts(result)
    print("\n=== Metrics ===")
    import json
    print(json.dumps(result["metrics"], indent=2))

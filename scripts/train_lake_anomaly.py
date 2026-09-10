"""WI-005 — build the lake-mean anomaly dataset and train the interim retrain.

Run from the project root:  .venv/bin/python scripts/train_lake_anomaly.py

Reads the committed `data/processed/fai_series_raw.csv` (no credentials, no
`sentinelhub`), writes:

  - data/processed/lake_anomaly_dataset.csv        the honest pairs + baseline
  - src/model/artifacts/lake_anomaly/metrics.json  metrics, baselines, verdict
  - src/model/artifacts/lake_anomaly/ridge.joblib  the fitted pipeline

It never touches `src/model/artifacts/` itself — the backend loads that at
import and serves per-station, and a lake-wide model cannot fill four station
cards (ADR-sf-0008). Rewiring the serving path is not WI-005.
"""

import json
import sys
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.features.lake_anomaly import DEFAULT_MIN_PRIOR, build_anomaly_pairs  # noqa: E402
from src.model.lake_anomaly import fit_and_evaluate  # noqa: E402

FAI_CSV = ROOT / "data" / "processed" / "fai_series_raw.csv"
DATASET_CSV = ROOT / "data" / "processed" / "lake_anomaly_dataset.csv"
ARTIFACTS = ROOT / "src" / "model" / "artifacts" / "lake_anomaly"

#: The uncalibrated station threshold, carried through so the gate can show it
#: is uncalibrated (EV-020). Not used as a training label.
STATION_THRESHOLD = json.loads(
    (ROOT / "src" / "model" / "artifacts" / "metrics.json").read_text()
)["fai_alert_threshold"]


def main() -> int:
    series = pd.read_csv(FAI_CSV)
    print(f"Loaded {len(series)} FAI pass rows from {FAI_CSV.name}")

    pairs = build_anomaly_pairs(
        series, min_prior=DEFAULT_MIN_PRIOR, bloom_threshold=STATION_THRESHOLD
    )
    if len(pairs) < 10:
        print(f"Only {len(pairs)} honest pairs — too few to train. Aborting.")
        return 1

    DATASET_CSV.parent.mkdir(parents=True, exist_ok=True)
    pairs.to_csv(DATASET_CSV, index=False)
    print(f"Wrote {len(pairs)} pairs -> {DATASET_CSV.relative_to(ROOT)}")

    result = fit_and_evaluate(pairs, bloom_threshold=STATION_THRESHOLD)
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(result["model"], ARTIFACTS / "ridge.joblib")
    (ARTIFACTS / "metrics.json").write_text(json.dumps(result["metrics"], indent=2) + "\n")
    print(f"Wrote metrics + model -> {ARTIFACTS.relative_to(ROOT)}/")

    m = result["metrics"]
    print("\n=== Interim lake-mean retrain (WI-005) ===")
    print(f"  pairs                {m['n_pairs']}  ({m['date_range']['start']}..{m['date_range']['end']})")
    print(f"  mae_fai (CV)         {m['metrics']['mae_fai']:.6f} +/- {m['metrics']['mae_fai_cv_std']:.6f}")
    print(f"  persistence baseline {m['baselines']['persistence']['mae_fai']:.6f}")
    print(f"  climatology baseline {m['baselines']['climatology']['mae_fai']:.6f}")
    print(f"  beats persistence?   {m['beats_baselines']['persistence']}")
    print(f"  beats climatology?   {m['beats_baselines']['climatology']}")
    print(f"  classification       null ({m['classification_reason'].split(':')[0]})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

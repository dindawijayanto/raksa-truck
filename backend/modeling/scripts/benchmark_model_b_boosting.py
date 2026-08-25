"""Benchmark CatBoost, LightGBM, and XGBoost for simulation-only Model B."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from _paths import DATA_DIR, RESEARCH_MODELS_DIR, REPORTS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))
RUNTIME_PACKAGES = SOURCE_DIR.parent / ".runtime_packages"
if RUNTIME_PACKAGES.exists():
    sys.path.insert(0, str(RUNTIME_PACKAGES))

from aic.boosting_benchmark import (
    benchmark_boosting_models,
    load_boosting_model_bundle,
    predict_boosting_model,
    write_boosting_benchmark_outputs,
)
from aic.synthetic_ml import SyntheticBenchmarkConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=DATA_DIR / "synthetic" / "model_b_physics_benchmark.csv",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=RESEARCH_MODELS_DIR / "model_b" / "synthetic_boosting_benchmark_v1",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=REPORTS_DIR / "model_b_boosting_benchmark",
    )
    parser.add_argument("--test-size", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = pd.read_csv(args.dataset)
    result = benchmark_boosting_models(dataset, SyntheticBenchmarkConfig(), test_size=args.test_size)
    write_boosting_benchmark_outputs(result, args.model_dir, args.report_dir)
    for path in sorted(args.model_dir.glob("*_model_b_synthetic_bundle_v1.joblib")):
        loaded = load_boosting_model_bundle(path)
        prediction = predict_boosting_model(loaded, dataset.head(1))
        if len(prediction) != 1 or prediction["model_status"].iloc[0] != "simulation_only":
            raise RuntimeError(f"Artifact verification failed for {path.name}")
    print("Boosting benchmark completed (simulation_only).")
    print(result.metrics.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"Model weights: {args.model_dir}")
    print(f"Visual report: {args.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

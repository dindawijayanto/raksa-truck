"""Train and persist the simulation-only ML surrogate for Model B."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from _paths import DATA_DIR, RESEARCH_MODELS_DIR, REPORTS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic.synthetic_ml import SyntheticBenchmarkConfig, train_synthetic_ml, write_synthetic_ml_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, default=DATA_DIR / "synthetic" / "model_b_physics_benchmark.csv")
    parser.add_argument("--model-dir", type=Path, default=RESEARCH_MODELS_DIR / "model_b" / "synthetic_ml_v1")
    parser.add_argument("--report-dir", type=Path, default=REPORTS_DIR / "model_b_synthetic_ml")
    parser.add_argument("--test-size", type=float, default=0.25)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = pd.read_csv(args.dataset)
    result = train_synthetic_ml(dataset, SyntheticBenchmarkConfig(), test_size=args.test_size)
    write_synthetic_ml_outputs(result, dataset, args.model_dir, args.report_dir)
    print("Synthetic ML training completed (simulation_only).")
    for name, value in result.metrics.items():
        print(f"{name}: {value:.4f}")
    print(f"Model weights: {args.model_dir}")
    print(f"Visual report: {args.report_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

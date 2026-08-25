"""Train the external EVIoT RUL benchmark for Model B research only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _paths import DATA_DIR, RESEARCH_MODELS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic.benchmark import load_eviot_dataset, train_eviot_rul_benchmark, write_benchmark_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--archive",
        type=Path,
        default=DATA_DIR / "external" / "eviot_predictive_maintenance.zip",
    )
    parser.add_argument("--output-dir", type=Path, default=RESEARCH_MODELS_DIR / "model_b" / "eviot_rul_benchmark")
    parser.add_argument("--max-rows", type=int, default=100_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = load_eviot_dataset(args.archive)
    report = train_eviot_rul_benchmark(dataset, max_rows=args.max_rows)
    write_benchmark_outputs(report, args.output_dir)
    print(f"EVIoT benchmark completed with {report.row_count:,} rows.")
    for name, value in report.metrics.items():
        print(f"{name}: {value:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

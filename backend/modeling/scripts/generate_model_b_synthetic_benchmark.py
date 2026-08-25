"""Generate the paper-backed, simulation-only truck benchmark for Model B ML."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _paths import DATA_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic.synthetic_ml import SyntheticBenchmarkConfig, generate_synthetic_benchmark, write_synthetic_benchmark


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DATA_DIR / "synthetic" / "model_b_physics_benchmark.csv")
    parser.add_argument("--fleet-units-per-template", type=int, default=20)
    parser.add_argument("--trips-per-unit", type=int, default=250)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = SyntheticBenchmarkConfig(
        fleet_units_per_template=args.fleet_units_per_template,
        trips_per_unit=args.trips_per_unit,
        random_seed=args.seed,
    )
    dataset = generate_synthetic_benchmark(config)
    write_synthetic_benchmark(dataset, args.output, config)
    print(f"Synthetic benchmark: {len(dataset):,} rows -> {args.output}")
    print(f"Service-due prevalence: {dataset['service_due_1000km'].mean():.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

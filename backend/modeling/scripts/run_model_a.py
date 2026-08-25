"""Run Model A across every local session archive."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from _paths import DATA_DIR, RESEARCH_MODELS_DIR, REPORTS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic import RoughnessConfig, process_all_archives, write_model_a_artifacts, write_model_a_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory containing the original sensor archives. Raw archives are intentionally not committed.",
    )
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR / "model_a")
    parser.add_argument("--model-dir", type=Path, default=RESEARCH_MODELS_DIR / "model_a")
    parser.add_argument("--min-gps-accuracy-m", type=float, default=10.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = RoughnessConfig(max_median_gps_accuracy_m=args.min_gps_accuracy_m)
    report = process_all_archives(args.data_dir, config)
    write_model_a_outputs(report, args.output_dir, config)
    write_model_a_artifacts(report, args.model_dir)
    processed = int((report.archive_audit["status"] == "processed").sum())
    skipped = int((report.archive_audit["status"] == "skipped").sum())
    print(f"Model A finished: {processed} archive(s) processed, {skipped} skipped.")
    print(f"Segments: {len(report.segments):,}; outputs: {args.output_dir}")
    print(f"Model weights: {args.model_dir}")
    return 0 if processed else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Run rule-based Model B from the persisted Model A segment table."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from _paths import DATA_DIR, RESEARCH_MODELS_DIR, REPORTS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic import WearConfig, score_wear, write_wear_model_spec, write_wear_outputs
from aic.reporting import write_model_b_presentation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", type=Path, default=DATA_DIR / "model_a" / "segments.csv")
    parser.add_argument("--output-dir", type=Path, default=REPORTS_DIR / "model_b")
    parser.add_argument("--model-dir", type=Path, default=RESEARCH_MODELS_DIR / "model_b")
    parser.add_argument("--load-kg", type=float, required=True, help="Actual or explicitly scenario-assumed cargo load.")
    parser.add_argument("--load-limit-kg", type=float, required=True, help="Legal/design load limit used for the ratio.")
    parser.add_argument("--service-interval-km", type=float, default=10_000.0)
    parser.add_argument("--load-profile", type=Path, help="Optional CSV: session_id,load_kg[,segment_id].")
    parser.add_argument(
        "--vehicle",
        action="append",
        help="Optional vehicle value to include; repeat the flag for more than one value.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    segments = pd.read_csv(args.segments)
    if args.vehicle:
        if "vehicle" not in segments.columns:
            raise ValueError("--vehicle requires a vehicle column in the Model A segment table")
        segments = segments.loc[segments["vehicle"].astype(str).isin(args.vehicle)].copy()
        if segments.empty:
            raise ValueError(f"No Model A rows match --vehicle {args.vehicle}")
    profile = pd.read_csv(args.load_profile) if args.load_profile else None
    config = WearConfig(
        load_kg=args.load_kg,
        load_limit_kg=args.load_limit_kg,
        service_interval_km=args.service_interval_km,
    )
    report = score_wear(segments, config, profile)
    write_wear_outputs(report, args.output_dir, config)
    write_wear_model_spec(args.model_dir, config)
    write_model_b_presentation(report, segments, config, args.output_dir)
    print(f"Model B finished for {len(report.session_summary)} session(s).")
    print(f"Outputs: {args.output_dir}")
    print(f"Model weights: {args.model_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

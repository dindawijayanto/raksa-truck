"""Create a labelled synthetic load profile for Model B debugging only."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from _paths import DATA_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic.synthetic import SyntheticLoadConfig, make_synthetic_load_profile


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--segments", type=Path, default=DATA_DIR / "model_a" / "segments.csv")
    parser.add_argument("--output", type=Path, default=DATA_DIR / "synthetic" / "load_profile_demo.csv")
    parser.add_argument("--load-limit-kg", type=float, required=True)
    parser.add_argument("--vehicle", default="tt", help="Vehicle value included in this debug fixture.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    segments = pd.read_csv(args.segments)
    if "vehicle" in segments.columns:
        segments = segments.loc[segments["vehicle"].astype(str) == args.vehicle].copy()
    profile = make_synthetic_load_profile(segments, SyntheticLoadConfig(load_limit_kg=args.load_limit_kg))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    profile.to_csv(args.output, index=False)
    print(f"Synthetic debug fixture written: {args.output} ({len(profile):,} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

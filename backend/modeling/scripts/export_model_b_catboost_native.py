"""Export the verified CatBoost benchmark bundle for API deployment.

The output uses CatBoost's native ``.cbm`` format, so a consuming API does not
need to unpickle the AIC research package. The exported model remains
``simulation_only`` until it is field-validated with fleet maintenance data.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from _paths import DEPLOYMENT_MODELS_DIR, RESEARCH_MODELS_DIR, SOURCE_DIR

sys.path.insert(0, str(SOURCE_DIR))

from aic.boosting_benchmark import load_boosting_model_bundle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bundle",
        type=Path,
        default=RESEARCH_MODELS_DIR
        / "model_b"
        / "synthetic_boosting_benchmark_v1"
        / "catboost_model_b_synthetic_bundle_v1.joblib",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEPLOYMENT_MODELS_DIR,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = load_boosting_model_bundle(args.bundle)
    if bundle.model_family != "catboost":
        raise ValueError(f"Expected a CatBoost bundle, received {bundle.model_family}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    bundle.damage_regressor.save_model(args.output_dir / "damage_regressor.cbm")
    bundle.rul_regressor.save_model(args.output_dir / "rul_regressor.cbm")
    bundle.service_classifier.save_model(args.output_dir / "service_classifier.cbm")
    contract = {
        "model_name": "model_b_catboost_native_v1",
        "model_family": "catboost",
        "model_status": "simulation_only",
        "feature_columns": list(bundle.feature_columns),
        "targets": {
            "damage_regressor": "log1p(damage_increment_pct)",
            "rul_regressor": "log1p(rul_km)",
            "service_classifier": "service_due_1000km",
        },
        "simulation_config": asdict(bundle.config),
        "restriction": "Model outputs are scenario estimates calibrated only to physics-informed synthetic labels, not observed maintenance outcomes.",
    }
    (args.output_dir / "model_contract.json").write_text(json.dumps(contract, indent=2), encoding="utf-8")
    print(f"Native CatBoost artifacts: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

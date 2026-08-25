"""Model B: transparent contextual wear scoring built on Model A output."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import numpy as np
import pandas as pd

from .config import WearConfig


@dataclass
class WearReport:
    """Model B outputs for a dashboard, notebook, or API response."""

    segment_wear: pd.DataFrame
    session_summary: pd.DataFrame


def _resolve_load_kg(
    segments: pd.DataFrame, default_load_kg: float, load_profile: pd.DataFrame | None
) -> tuple[pd.Series, pd.Series]:
    if load_profile is None:
        return pd.Series(default_load_kg, index=segments.index, dtype=float), pd.Series(
            "configured_default", index=segments.index, dtype="object"
        )
    required = {"session_id", "load_kg"}
    missing = required - set(load_profile.columns)
    if missing:
        raise ValueError(f"load_profile is missing columns: {sorted(missing)}")
    join_columns = ["session_id"]
    if "segment_id" in load_profile.columns:
        join_columns.append("segment_id")
    profile = load_profile[join_columns + ["load_kg"]].copy()
    profile["load_kg"] = pd.to_numeric(profile["load_kg"], errors="raise")
    if profile.duplicated(join_columns).any():
        raise ValueError("load_profile has duplicate session/segment rows")
    enriched = segments[join_columns].merge(profile, on=join_columns, how="left")
    profile_load = pd.Series(enriched["load_kg"].to_numpy(), index=segments.index, dtype=float)
    values = profile_load.fillna(default_load_kg)
    source = pd.Series(
        np.where(profile_load.notna(), "load_profile", "configured_default"), index=segments.index, dtype="object"
    )
    return values, source


def score_wear(
    roughness_segments: pd.DataFrame,
    config: WearConfig,
    load_profile: pd.DataFrame | None = None,
) -> WearReport:
    """Estimate service-life consumption without pretending to predict failures.

    Model A scores are session-relative, so cumulative wear is reset for every
    session. A real fleet deployment should continue it from the truck's last
    service record and use live load-cell values through ``load_profile``.
    """

    required = {"session_id", "segment_id", "distance_coverage_m", "relative_roughness_score"}
    missing = required - set(roughness_segments.columns)
    if missing:
        raise ValueError(f"roughness_segments is missing columns: {sorted(missing)}")
    segments = roughness_segments.dropna(subset=["relative_roughness_score"]).copy()
    if segments.empty:
        raise ValueError("Model A output has no scored segments")
    segments["relative_roughness_score"] = pd.to_numeric(segments["relative_roughness_score"], errors="raise")
    segments["distance_coverage_m"] = pd.to_numeric(segments["distance_coverage_m"], errors="raise")
    if (segments["distance_coverage_m"] < 0).any():
        raise ValueError("distance_coverage_m cannot be negative")
    segments["load_kg"], segments["load_source"] = _resolve_load_kg(segments, config.load_kg, load_profile)
    if (segments["load_kg"] < 0).any():
        raise ValueError("load profile cannot contain negative values")

    segments = segments.sort_values(["session_id", "segment_id"]).reset_index(drop=True)
    segments["load_ratio"] = (segments["load_kg"] / config.load_limit_kg).clip(lower=0)
    segments["overload_flag"] = segments["load_ratio"] > 1.0
    segments["roughness_ratio"] = (segments["relative_roughness_score"] / 100.0).clip(0, 1)
    segments["load_component_score"] = 100 * config.load_weight * segments["load_ratio"].clip(upper=1)
    segments["roughness_component_score"] = 100 * config.roughness_weight * segments["roughness_ratio"]
    segments["context_score"] = segments["load_component_score"] + segments["roughness_component_score"]
    segments["wear_risk_band"] = pd.cut(
        segments["context_score"],
        bins=[-np.inf, 40, 70, np.inf],
        labels=["Rendah", "Sedang", "Tinggi"],
        include_lowest=True,
    )
    segments["wear_multiplier"] = (
        1.0
        + config.load_weight * segments["load_ratio"]
        + config.roughness_weight * segments["roughness_ratio"]
        + config.interaction_weight * segments["load_ratio"] * segments["roughness_ratio"]
    )
    segments["distance_km"] = segments["distance_coverage_m"] / 1000.0
    segments["wear_increment"] = 100.0 * segments["distance_km"] / config.service_interval_km * segments["wear_multiplier"]
    segments["cumulative_wear_score"] = segments.groupby("session_id", sort=False)["wear_increment"].cumsum().clip(upper=100)
    current_rate_per_km = 100.0 / config.service_interval_km * segments["wear_multiplier"]
    segments["estimated_remaining_km"] = ((100 - segments["cumulative_wear_score"]) / current_rate_per_km).clip(lower=0)
    segments["service_alert"] = segments["cumulative_wear_score"] >= config.service_alert_score

    summary = (
        segments.groupby("session_id", as_index=False)
        .agg(
            segments=("segment_id", "size"),
            distance_km=("distance_km", "sum"),
            mean_load_kg=("load_kg", "mean"),
            mean_roughness_score=("relative_roughness_score", "mean"),
            mean_context_score=("context_score", "mean"),
            peak_context_score=("context_score", "max"),
            high_context_segments=("wear_risk_band", lambda values: int((values == "Tinggi").sum())),
            mean_wear_multiplier=("wear_multiplier", "mean"),
            final_wear_score=("cumulative_wear_score", "last"),
            estimated_remaining_km=("estimated_remaining_km", "last"),
            overload_segments=("overload_flag", "sum"),
            service_alert=("service_alert", "max"),
        )
        .sort_values("session_id")
        .reset_index(drop=True)
    )
    return WearReport(segment_wear=segments, session_summary=summary)


def write_wear_outputs(report: WearReport, output_dir: Path, config: WearConfig) -> None:
    """Persist dashboard-ready Model B tables and the scenario configuration."""

    output_dir.mkdir(parents=True, exist_ok=True)
    report.segment_wear.to_csv(output_dir / "segment_wear.csv", index=False)
    report.session_summary.to_csv(output_dir / "session_summary.csv", index=False)
    (output_dir / "run_config.json").write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")


def write_wear_model_spec(model_dir: Path, config: WearConfig) -> None:
    """Save the deployable, transparent Model B coefficients as model weights."""

    model_dir.mkdir(parents=True, exist_ok=True)
    specification = {
        "model_name": "contextual_wear_rule_based_v1",
        "model_type": "transparent_rule_based",
        "deployment_status": "usable after live load and service-distance inputs are connected",
        "weights": {
            "load_weight": config.load_weight,
            "roughness_weight": config.roughness_weight,
            "interaction_weight": config.interaction_weight,
        },
        "formula": {
            "context_score": "100 * (load_weight * min(load_kg/load_limit_kg, 1) + roughness_weight * relative_roughness_score/100)",
            "wear_multiplier": "1 + load_weight * load_ratio + roughness_weight * roughness_ratio + interaction_weight * load_ratio * roughness_ratio",
        },
        "runtime_parameters": asdict(config),
        "limitations": "The current local run uses a synthetic debug load profile; replace it with load-cell data before real service decisions.",
    }
    (model_dir / "contextual_wear_rule_based_v1.json").write_text(
        json.dumps(specification, indent=2), encoding="utf-8"
    )

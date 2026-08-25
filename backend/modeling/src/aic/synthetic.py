"""Clearly labelled synthetic fixtures for debugging before load-cell data arrives."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SyntheticLoadConfig:
    """Parameters for reproducible, non-production load-profile fixtures."""

    load_limit_kg: float
    mean_load_ratio: float = 0.55
    variation_ratio: float = 0.12
    random_seed: int = 42

    def __post_init__(self) -> None:
        if self.load_limit_kg <= 0:
            raise ValueError("load_limit_kg must be positive")
        if not 0 <= self.mean_load_ratio <= 1:
            raise ValueError("mean_load_ratio must be in [0, 1]")
        if self.variation_ratio < 0:
            raise ValueError("variation_ratio cannot be negative")


def make_synthetic_load_profile(segments: pd.DataFrame, config: SyntheticLoadConfig) -> pd.DataFrame:
    """Create a smooth, deterministic per-segment load fixture.

    It models trip-to-trip load changes plus small within-trip variations. The
    output is intentionally marked synthetic so callers cannot mistake it for
    a load-cell reading.
    """

    required = {"session_id", "segment_id"}
    missing = required - set(segments.columns)
    if missing:
        raise ValueError(f"segments is missing columns: {sorted(missing)}")
    rng = np.random.default_rng(config.random_seed)
    profile_parts: list[pd.DataFrame] = []
    for session_id, frame in segments.loc[:, ["session_id", "segment_id"]].drop_duplicates().groupby("session_id", sort=True):
        part = frame.sort_values("segment_id").copy()
        trip_ratio = config.mean_load_ratio + rng.normal(0, config.variation_ratio / 2)
        phase = np.linspace(0, 2 * np.pi, len(part), endpoint=False)
        noise = rng.normal(0, config.variation_ratio / 5, len(part))
        ratio = np.clip(trip_ratio + config.variation_ratio * np.sin(phase) + noise, 0.05, 1.0)
        part["load_kg"] = (ratio * config.load_limit_kg).round(1)
        part["data_origin"] = "synthetic_debug_fixture"
        profile_parts.append(part)
    return pd.concat(profile_parts, ignore_index=True) if profile_parts else pd.DataFrame(columns=[*required, "load_kg", "data_origin"])

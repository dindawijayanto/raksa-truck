"""Configuration objects shared by the offline pipeline and future dashboard."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RoughnessConfig:
    """Parameters for the session-relative road roughness pipeline."""

    target_sampling_hz: float | None = None
    filter_cutoff_hz: float = 0.5
    filter_order: int = 4
    segment_length_m: float = 20.0
    min_segment_coverage_m: float = 18.0
    min_speed_kmh: float = 5.0
    max_gps_tolerance_s: float = 1.5
    max_median_gps_accuracy_m: float = 10.0
    min_samples_per_segment: int = 50
    max_moving_sample_gap_s: float = 0.25
    min_model_segments: int = 15
    cluster_count: int = 3
    random_seed: int = 42

    def __post_init__(self) -> None:
        if self.target_sampling_hz is not None and self.target_sampling_hz <= 2 * self.filter_cutoff_hz:
            raise ValueError("target_sampling_hz must exceed twice filter_cutoff_hz")
        if self.segment_length_m <= 0 or self.min_segment_coverage_m <= 0:
            raise ValueError("segment lengths must be positive")
        if self.min_segment_coverage_m > self.segment_length_m:
            raise ValueError("min_segment_coverage_m cannot exceed segment_length_m")
        if self.cluster_count < 2:
            raise ValueError("cluster_count must be at least 2")


@dataclass(frozen=True)
class WearConfig:
    """Transparent rule-based Model B configuration.

    The score represents estimated service-life consumed. It is not a trained
    failure probability because this project does not yet contain labelled
    maintenance outcomes.
    """

    load_kg: float
    load_limit_kg: float
    service_interval_km: float
    load_weight: float = 0.60
    roughness_weight: float = 0.40
    interaction_weight: float = 0.20
    service_alert_score: float = 85.0

    def __post_init__(self) -> None:
        if self.load_kg < 0:
            raise ValueError("load_kg cannot be negative")
        if self.load_limit_kg <= 0:
            raise ValueError("load_limit_kg must be positive")
        if self.service_interval_km <= 0:
            raise ValueError("service_interval_km must be positive")
        if not 0 < self.service_alert_score <= 100:
            raise ValueError("service_alert_score must be in (0, 100]")

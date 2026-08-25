"""Validated API contracts for the simulation-only Model B endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class ModelBScenarioRequest(BaseModel):
    """Operational inputs needed to construct one truck-trip scenario."""

    truck_tare_kg: float = Field(gt=0, le=50_000, examples=[6_000])
    gross_weight_limit_kg: float = Field(gt=0, le=80_000, examples=[16_000])
    payload_kg: float = Field(ge=0, le=60_000, examples=[6_850])
    axle_count: int = Field(ge=2, le=4, examples=[3])
    road_iri_m_per_km: float = Field(ge=1.0, le=5.5, examples=[3.2])
    speed_kmh: float = Field(ge=24, le=89, examples=[48])
    suspension_type: Literal["leaf", "air"] = "leaf"
    tire_pressure_ratio: float = Field(ge=0.85, le=1.15, examples=[1.0])
    trip_distance_km: float = Field(ge=25, le=180, examples=[85])
    cumulative_wear_pct: float = Field(ge=0, le=100, examples=[28])

    @model_validator(mode="after")
    def validate_vehicle_mass(self) -> "ModelBScenarioRequest":
        if self.gross_weight_limit_kg <= self.truck_tare_kg:
            raise ValueError("gross_weight_limit_kg must be larger than truck_tare_kg")
        payload_capacity_kg = self.gross_weight_limit_kg - self.truck_tare_kg
        if self.payload_kg > payload_capacity_kg * 1.10:
            raise ValueError("payload_kg exceeds the benchmark's supported 110% payload stress-test range")
        return self


class DerivedFeatures(BaseModel):
    gross_weight_ratio: float
    payload_ratio: float
    dynamic_load_coefficient: float
    road_condition: Literal["smooth", "medium", "rough"]
    overload: bool


class ModelBScenarioResponse(BaseModel):
    model_name: str
    model_status: Literal["simulation_only"]
    notice: str
    risk_band: Literal["low", "medium", "high"]
    scenario_health_score: float
    predicted_damage_increment_pct: float
    predicted_rul_km: float
    service_due_probability: float
    derived_features: DerivedFeatures

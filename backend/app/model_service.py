"""Portable CatBoost inference service for the exported Model B artifact."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier, CatBoostRegressor

from .schemas import DerivedFeatures, ModelBScenarioRequest, ModelBScenarioResponse


class ModelBService:
    """Load native CatBoost weights once and predict a single trip scenario."""

    def __init__(self, model_dir: Path) -> None:
        contract_path = model_dir / "model_contract.json"
        if not contract_path.exists():
            raise FileNotFoundError(f"Model contract not found: {contract_path}")
        self.contract = json.loads(contract_path.read_text(encoding="utf-8"))
        if self.contract.get("model_status") != "simulation_only":
            raise ValueError("Only the explicitly simulation-only Model B contract is supported")
        self.feature_columns = tuple(self.contract["feature_columns"])
        self.damage_regressor = CatBoostRegressor()
        self.rul_regressor = CatBoostRegressor()
        self.service_classifier = CatBoostClassifier()
        self.damage_regressor.load_model(model_dir / "damage_regressor.cbm")
        self.rul_regressor.load_model(model_dir / "rul_regressor.cbm")
        self.service_classifier.load_model(model_dir / "service_classifier.cbm")

    @staticmethod
    def _dynamic_load_coefficient(scenario: ModelBScenarioRequest) -> float:
        """Deterministic deployment counterpart of the benchmark DLC feature."""

        suspension_factor = 0.88 if scenario.suspension_type == "air" else 1.0
        tire_factor = 1.0 + 0.25 * abs(scenario.tire_pressure_ratio - 1.0)
        coefficient = (
            0.04
            + 0.025
            * scenario.road_iri_m_per_km
            * (scenario.speed_kmh / 40.0)
            * suspension_factor
            * tire_factor
        )
        return float(np.clip(coefficient, 0.02, 0.45))

    @staticmethod
    def _road_condition(iri_m_per_km: float) -> str:
        if iri_m_per_km <= 2.3:
            return "smooth"
        if iri_m_per_km <= 3.8:
            return "medium"
        return "rough"

    def predict(self, scenario: ModelBScenarioRequest) -> ModelBScenarioResponse:
        payload_capacity_kg = scenario.gross_weight_limit_kg - scenario.truck_tare_kg
        payload_ratio = scenario.payload_kg / payload_capacity_kg
        gross_weight_ratio = (scenario.truck_tare_kg + scenario.payload_kg) / scenario.gross_weight_limit_kg
        dynamic_load_coefficient = self._dynamic_load_coefficient(scenario)
        feature_row = pd.DataFrame(
            [
                {
                    "gross_weight_ratio": gross_weight_ratio,
                    "payload_ratio": payload_ratio,
                    "axle_count": scenario.axle_count,
                    "road_iri_m_per_km": scenario.road_iri_m_per_km,
                    "speed_kmh": scenario.speed_kmh,
                    "suspension_is_air": int(scenario.suspension_type == "air"),
                    "tire_pressure_ratio": scenario.tire_pressure_ratio,
                    "trip_distance_km": scenario.trip_distance_km,
                    "dynamic_load_coefficient": dynamic_load_coefficient,
                    "cumulative_wear_pct": scenario.cumulative_wear_pct,
                }
            ],
            columns=self.feature_columns,
        )
        predicted_damage = float(np.clip(np.expm1(self.damage_regressor.predict(feature_row)[0]), 0, None))
        predicted_rul = float(np.clip(np.expm1(self.rul_regressor.predict(feature_row)[0]), 0, None))
        service_probability = float(self.service_classifier.predict_proba(feature_row)[0, 1])
        overload = gross_weight_ratio > 1.0
        risk_band = "high" if overload or service_probability >= 0.75 else "medium" if service_probability >= 0.45 else "low"
        health_score = float(np.clip(100.0 - scenario.cumulative_wear_pct - predicted_damage * 8.0, 0, 100))
        return ModelBScenarioResponse(
            model_name=self.contract["model_name"],
            model_status="simulation_only",
            notice="Estimasi skenario dari CatBoost yang dilatih pada label sintetis physics-informed; bukan keputusan maintenance yang tervalidasi di lapangan.",
            risk_band=risk_band,
            scenario_health_score=round(health_score, 1),
            predicted_damage_increment_pct=round(predicted_damage, 4),
            predicted_rul_km=round(predicted_rul, 1),
            service_due_probability=round(service_probability, 4),
            derived_features=DerivedFeatures(
                gross_weight_ratio=round(gross_weight_ratio, 4),
                payload_ratio=round(payload_ratio, 4),
                dynamic_load_coefficient=round(dynamic_load_coefficient, 4),
                road_condition=self._road_condition(scenario.road_iri_m_per_km),
                overload=overload,
            ),
        )

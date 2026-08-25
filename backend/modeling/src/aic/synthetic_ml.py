"""Paper-backed synthetic benchmark and ML surrogate for Model B research.

The generated labels are simulation targets, not observed fleet outcomes. The
module is deliberately isolated from the deployable rule-based Model B.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    average_precision_score,
    mean_absolute_error,
    mean_squared_error,
    precision_recall_curve,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit


@dataclass(frozen=True)
class TruckTemplate:
    """Generic truck configuration used only for scenario simulation."""

    name: str
    gross_weight_limit_t: float
    tare_weight_t: float
    axle_count: int

    @property
    def payload_capacity_t(self) -> float:
        return self.gross_weight_limit_t - self.tare_weight_t


DEFAULT_TRUCK_TEMPLATES = (
    TruckTemplate("light_generic", gross_weight_limit_t=8.0, tare_weight_t=3.0, axle_count=2),
    TruckTemplate("medium_generic", gross_weight_limit_t=16.0, tare_weight_t=6.0, axle_count=3),
    TruckTemplate("heavy_generic", gross_weight_limit_t=30.0, tare_weight_t=12.0, axle_count=4),
)

ROAD_CLASSES = {
    "smooth": (1.0, 2.3),
    "medium": (2.3, 3.8),
    "rough": (3.8, 5.5),
}
PAYLOAD_RATIOS = (0.0, 0.50, 0.75, 1.00, 1.10)
SPEED_STATES_KMH = (24.0, 48.0, 72.0, 89.0)
FEATURE_COLUMNS = (
    "gross_weight_ratio",
    "payload_ratio",
    "axle_count",
    "road_iri_m_per_km",
    "speed_kmh",
    "suspension_is_air",
    "tire_pressure_ratio",
    "trip_distance_km",
    "dynamic_load_coefficient",
    "cumulative_wear_pct",
)


@dataclass(frozen=True)
class SyntheticBenchmarkConfig:
    """Assumptions for the synthetic, physics-informed benchmark."""

    templates: tuple[TruckTemplate, ...] = DEFAULT_TRUCK_TEMPLATES
    fleet_units_per_template: int = 20
    trips_per_unit: int = 250
    road_profile_seeds: int = 3
    damage_exponent: float = 3.5
    nominal_service_life_km: float = 10_000.0
    service_due_horizon_km: float = 1_000.0
    random_seed: int = 42

    def __post_init__(self) -> None:
        if self.fleet_units_per_template < 2 or self.trips_per_unit < 10:
            raise ValueError("benchmark needs at least two units and ten trips per unit")
        if not 3.0 <= self.damage_exponent <= 4.0:
            raise ValueError("damage_exponent must stay in the documented [3, 4] sensitivity range")
        if self.nominal_service_life_km <= 0 or self.service_due_horizon_km <= 0:
            raise ValueError("service distances must be positive")


@dataclass
class SyntheticMlArtifact:
    """Two fitted surrogate models plus the scenario contract they learned."""

    feature_columns: tuple[str, ...]
    config: SyntheticBenchmarkConfig
    damage_regressor: TransformedTargetRegressor
    rul_regressor: TransformedTargetRegressor
    service_classifier: HistGradientBoostingClassifier


@dataclass
class SyntheticMlTrainingResult:
    artifact: SyntheticMlArtifact
    metrics: dict[str, float]
    test_predictions: pd.DataFrame
    feature_importance: pd.DataFrame


def _dynamic_load_coefficient(
    iri_m_per_km: float,
    speed_kmh: float,
    suspension_type: str,
    tire_pressure_ratio: float,
    noise: float,
) -> float:
    """Compact response proxy: rougher/faster conditions induce higher dynamics."""

    suspension_factor = 0.88 if suspension_type == "air" else 1.0
    tire_factor = 1.0 + 0.25 * abs(tire_pressure_ratio - 1.0)
    coefficient = 0.04 + 0.025 * iri_m_per_km * (speed_kmh / 40.0) * suspension_factor * tire_factor + noise
    return float(np.clip(coefficient, 0.02, 0.45))


def generate_synthetic_benchmark(config: SyntheticBenchmarkConfig | None = None) -> pd.DataFrame:
    """Generate sequential fleet exposure scenarios and simulation-only labels.

    Roughness bands use the smooth/medium/rough IRI boundaries tested with
    heavy vehicles. Damage uses a load exponent sampled as a fixed sensitivity
    assumption within the documented 3--4 range, then combines roughness,
    velocity, suspension, tyre state, and dynamic load coefficient.
    """

    config = config or SyntheticBenchmarkConfig()
    rng = np.random.default_rng(config.random_seed)
    rows: list[dict[str, Any]] = []
    for template in config.templates:
        for unit_index in range(config.fleet_units_per_template):
            fleet_unit_id = f"{template.name}_{unit_index:03d}"
            suspension_type = "air" if unit_index % 2 else "leaf"
            cumulative_damage = float(rng.uniform(0.02, 0.45))
            maintenance_cycle = 0
            for trip_index in range(config.trips_per_unit):
                payload_ratio = float(rng.choice(PAYLOAD_RATIOS, p=[0.08, 0.27, 0.30, 0.25, 0.10]))
                road_class = str(rng.choice(tuple(ROAD_CLASSES)))
                iri_min, iri_max = ROAD_CLASSES[road_class]
                road_seed = int(rng.integers(0, config.road_profile_seeds))
                seed_shift = (road_seed - (config.road_profile_seeds - 1) / 2) * 0.08
                iri_m_per_km = float(np.clip(rng.uniform(iri_min, iri_max) + seed_shift, iri_min, iri_max))
                speed_kmh = float(rng.choice(SPEED_STATES_KMH))
                tire_pressure_ratio = float(rng.choice((0.85, 1.0, 1.15), p=[0.2, 0.6, 0.2]))
                trip_distance_km = float(rng.uniform(25, 180))
                payload_t = template.payload_capacity_t * payload_ratio
                gross_weight_t = template.tare_weight_t + payload_t
                gross_weight_ratio = gross_weight_t / template.gross_weight_limit_t
                dynamic_load_coefficient = _dynamic_load_coefficient(
                    iri_m_per_km,
                    speed_kmh,
                    suspension_type,
                    tire_pressure_ratio,
                    noise=float(rng.normal(0, 0.012)),
                )
                roughness_factor = 1.0 + 0.08 * iri_m_per_km
                speed_factor = 1.0 + 0.25 * (speed_kmh / max(SPEED_STATES_KMH)) ** 2
                tire_factor = 1.0 + 0.15 * abs(tire_pressure_ratio - 1.0)
                suspension_damage_factor = 0.90 if suspension_type == "air" else 1.0
                load_factor = max(gross_weight_ratio, 0.05) ** config.damage_exponent
                damage_rate_per_km = (
                    load_factor
                    * roughness_factor
                    * speed_factor
                    * (1.0 + dynamic_load_coefficient)
                    * tire_factor
                    * suspension_damage_factor
                    / config.nominal_service_life_km
                )
                remaining_damage = max(1.0 - cumulative_damage, 0.0)
                rul_km = remaining_damage / max(damage_rate_per_km, 1e-12)
                damage_increment = damage_rate_per_km * trip_distance_km
                service_due = int(rul_km <= config.service_due_horizon_km)
                rows.append(
                    {
                        "fleet_unit_id": fleet_unit_id,
                        "maintenance_cycle": maintenance_cycle,
                        "trip_index": trip_index,
                        "truck_class": template.name,
                        "gross_weight_limit_t": template.gross_weight_limit_t,
                        "tare_weight_t": template.tare_weight_t,
                        "axle_count": template.axle_count,
                        "suspension_type": suspension_type,
                        "suspension_is_air": int(suspension_type == "air"),
                        "payload_ratio": payload_ratio,
                        "payload_t": payload_t,
                        "gross_weight_t": gross_weight_t,
                        "gross_weight_ratio": gross_weight_ratio,
                        "road_class": road_class,
                        "road_iri_m_per_km": iri_m_per_km,
                        "road_profile_seed": road_seed,
                        "speed_kmh": speed_kmh,
                        "tire_pressure_ratio": tire_pressure_ratio,
                        "trip_distance_km": trip_distance_km,
                        "dynamic_load_coefficient": dynamic_load_coefficient,
                        "cumulative_wear_pct": cumulative_damage * 100.0,
                        "damage_increment_pct": damage_increment * 100.0,
                        "rul_km": rul_km,
                        "service_due_1000km": service_due,
                        "data_origin": "physics_informed_synthetic_benchmark",
                    }
                )
                cumulative_damage += damage_increment
                if cumulative_damage >= 1.0:
                    cumulative_damage = float(rng.uniform(0.0, 0.03))
                    maintenance_cycle += 1
    return pd.DataFrame(rows)


def write_synthetic_benchmark(dataset: pd.DataFrame, output_path: Path, config: SyntheticBenchmarkConfig) -> None:
    """Persist the simulated data and a machine-readable methodology manifest."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(output_path, index=False)
    manifest = {
        "data_origin": "physics_informed_synthetic_benchmark",
        "rows": len(dataset),
        "feature_columns": list(FEATURE_COLUMNS),
        "targets": ["damage_increment_pct", "rul_km", "service_due_1000km"],
        "config": asdict(config),
        "restriction": "Synthetic labels are simulation outputs and must not be reported as field-validated maintenance performance.",
    }
    output_path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def _validate_training_data(dataset: pd.DataFrame) -> pd.DataFrame:
    required = set(FEATURE_COLUMNS) | {
        "fleet_unit_id",
        "damage_increment_pct",
        "rul_km",
        "service_due_1000km",
    }
    missing = required - set(dataset.columns)
    if missing:
        raise ValueError(f"Synthetic benchmark is missing columns: {sorted(missing)}")
    result = dataset.copy()
    for column in (*FEATURE_COLUMNS, "damage_increment_pct", "rul_km", "service_due_1000km"):
        result[column] = pd.to_numeric(result[column], errors="raise")
    if (result["rul_km"] < 0).any():
        raise ValueError("rul_km cannot be negative")
    if result["service_due_1000km"].nunique() < 2:
        raise ValueError("Synthetic benchmark needs both maintenance classes")
    return result


def train_synthetic_ml(
    dataset: pd.DataFrame,
    config: SyntheticBenchmarkConfig | None = None,
    test_size: float = 0.25,
) -> SyntheticMlTrainingResult:
    """Fit group-held-out RUL regression and service-horizon classification."""

    config = config or SyntheticBenchmarkConfig()
    dataset = _validate_training_data(dataset)
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=config.random_seed)
    train_index, test_index = next(splitter.split(dataset, groups=dataset["fleet_unit_id"]))
    train, test = dataset.iloc[train_index].copy(), dataset.iloc[test_index].copy()
    x_train, x_test = train.loc[:, FEATURE_COLUMNS], test.loc[:, FEATURE_COLUMNS]

    def make_regressor() -> TransformedTargetRegressor:
        return TransformedTargetRegressor(
            regressor=HistGradientBoostingRegressor(
                learning_rate=0.06,
                max_leaf_nodes=31,
                l2_regularization=0.1,
                max_iter=300,
                random_state=config.random_seed,
            ),
            func=np.log1p,
            inverse_func=np.expm1,
        )

    damage_regressor = make_regressor()
    damage_regressor.fit(x_train, train["damage_increment_pct"])
    regressor = make_regressor()
    regressor.fit(x_train, train["rul_km"])
    class_target = train["service_due_1000km"].astype(int)
    positive_rate = float(class_target.mean())
    weights = np.where(class_target.eq(1), 0.5 / positive_rate, 0.5 / (1 - positive_rate))
    classifier = HistGradientBoostingClassifier(
        learning_rate=0.06,
        max_leaf_nodes=31,
        l2_regularization=0.1,
        max_iter=250,
        random_state=config.random_seed,
    )
    classifier.fit(x_train, class_target, sample_weight=weights)

    predicted_rul = np.clip(regressor.predict(x_test), 0, None)
    predicted_damage = np.clip(damage_regressor.predict(x_test), 0, None)
    due_probability = classifier.predict_proba(x_test)[:, 1]
    due_prediction = (due_probability >= 0.5).astype(int)
    metrics = {
        "test_r2_damage_increment": float(r2_score(test["damage_increment_pct"], predicted_damage)),
        "test_mae_damage_increment_pct": float(mean_absolute_error(test["damage_increment_pct"], predicted_damage)),
        "test_r2_rul": float(r2_score(test["rul_km"], predicted_rul)),
        "test_mae_rul_km": float(mean_absolute_error(test["rul_km"], predicted_rul)),
        "test_rmse_rul_km": float(np.sqrt(mean_squared_error(test["rul_km"], predicted_rul))),
        "test_pr_auc_service_due": float(average_precision_score(test["service_due_1000km"], due_probability)),
        "test_precision_service_due": float(precision_score(test["service_due_1000km"], due_prediction, zero_division=0)),
        "test_recall_service_due": float(recall_score(test["service_due_1000km"], due_prediction, zero_division=0)),
        "test_rows": float(len(test)),
        "train_rows": float(len(train)),
        "test_fleet_units": float(test["fleet_unit_id"].nunique()),
    }
    importance_source = test.sample(min(2_000, len(test)), random_state=config.random_seed)
    permutation = permutation_importance(
        regressor,
        importance_source.loc[:, FEATURE_COLUMNS],
        importance_source["rul_km"],
        scoring="neg_mean_absolute_error",
        n_repeats=5,
        random_state=config.random_seed,
        n_jobs=1,
    )
    feature_importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance_mean": permutation.importances_mean,
            "importance_std": permutation.importances_std,
        }
    ).sort_values("importance_mean", ascending=False)
    predictions = test.loc[:, ["fleet_unit_id", "truck_class", "road_class", "payload_ratio", "speed_kmh", "rul_km", "service_due_1000km"]].copy()
    predictions["predicted_rul_km"] = predicted_rul
    predictions["damage_increment_pct"] = test["damage_increment_pct"].to_numpy()
    predictions["predicted_damage_increment_pct"] = predicted_damage
    predictions["service_due_probability"] = due_probability
    artifact = SyntheticMlArtifact(
        feature_columns=FEATURE_COLUMNS,
        config=config,
        damage_regressor=damage_regressor,
        rul_regressor=regressor,
        service_classifier=classifier,
    )
    return SyntheticMlTrainingResult(artifact, metrics, predictions, feature_importance)


def load_synthetic_ml_artifact(model_path: Path) -> SyntheticMlArtifact:
    """Load a saved simulation-only artifact for a dashboard integration test."""

    artifact = joblib.load(model_path)
    if not isinstance(artifact, SyntheticMlArtifact):
        raise TypeError(f"Unexpected artifact type: {type(artifact).__name__}")
    return artifact


def predict_synthetic_ml(artifact: SyntheticMlArtifact, feature_table: pd.DataFrame) -> pd.DataFrame:
    """Return the three Model B ML outputs for a validated feature table.

    The caller must preserve the model's `simulation_only` deployment status.
    """

    missing = set(artifact.feature_columns) - set(feature_table.columns)
    if missing:
        raise ValueError(f"feature_table is missing columns: {sorted(missing)}")
    features = feature_table.loc[:, artifact.feature_columns].apply(pd.to_numeric, errors="raise")
    result = feature_table.copy()
    result["predicted_damage_increment_pct"] = np.clip(artifact.damage_regressor.predict(features), 0, None)
    result["predicted_rul_km"] = np.clip(artifact.rul_regressor.predict(features), 0, None)
    result["service_due_probability"] = artifact.service_classifier.predict_proba(features)[:, 1]
    result["model_status"] = "simulation_only"
    return result


def write_synthetic_ml_outputs(
    result: SyntheticMlTrainingResult,
    dataset: pd.DataFrame,
    model_dir: Path,
    report_dir: Path,
) -> None:
    """Save ML weights, model card, metrics, and a presentation-ready overview."""

    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(result.artifact, model_dir / "physics_informed_synthetic_ml_v1.joblib")
    model_card = {
        "model_name": "physics_informed_synthetic_ml_v1",
        "deployment_status": "simulation_only",
        "model_components": [
            "HistGradientBoostingRegressor (damage increment)",
            "HistGradientBoostingRegressor (RUL)",
            "HistGradientBoostingClassifier (service horizon)",
        ],
        "feature_columns": list(result.artifact.feature_columns),
        "metrics": result.metrics,
        "simulation_config": asdict(result.artifact.config),
        "restriction": "Performance measures only fidelity to the generated simulation labels; they are not field-validation metrics.",
    }
    (model_dir / "model_card.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    (report_dir / "metrics.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    result.test_predictions.to_csv(report_dir / "test_predictions.csv", index=False)
    result.feature_importance.to_csv(report_dir / "feature_importance.csv", index=False)
    _write_benchmark_figure(result, dataset, report_dir / "synthetic_ml_overview.png")


def _write_benchmark_figure(
    result: SyntheticMlTrainingResult, dataset: pd.DataFrame, destination: Path
) -> None:
    predictions = result.test_predictions.sample(min(2_000, len(result.test_predictions)), random_state=42)
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    fig.patch.set_facecolor("#F8FCF9")
    fig.suptitle("Model B · Physics-Informed Synthetic ML Benchmark", fontsize=19, fontweight="bold", color="#163020")
    fig.text(
        0.5,
        0.955,
        "Metrik mengukur kecocokan pada label simulasi, bukan akurasi armada di lapangan.",
        ha="center",
        color="#B45309",
        fontsize=10,
    )

    axes[0, 0].scatter(predictions["rul_km"], predictions["predicted_rul_km"], alpha=0.42, s=16, color="#2563EB")
    maximum = float(max(predictions[["rul_km", "predicted_rul_km"]].max()))
    axes[0, 0].plot([0, maximum], [0, maximum], "--", color="#DC2626", linewidth=1.2)
    axes[0, 0].set(
        title=f"RUL: actual vs prediksi (R² {result.metrics['test_r2_rul']:.3f})",
        xlabel="RUL simulasi (km)",
        ylabel="RUL prediksi (km)",
    )

    precision, recall, _ = precision_recall_curve(
        predictions["service_due_1000km"], predictions["service_due_probability"]
    )
    axes[0, 1].plot(recall, precision, color="#15803D", linewidth=2.2)
    baseline = float(predictions["service_due_1000km"].mean())
    axes[0, 1].axhline(baseline, color="#64748B", linestyle="--", label=f"Baseline {baseline:.2f}")
    axes[0, 1].set(
        title=f"Service ≤1.000 km · PR-AUC {result.metrics['test_pr_auc_service_due']:.3f}",
        xlabel="Recall",
        ylabel="Precision",
        xlim=(0, 1),
        ylim=(0, 1.05),
    )
    axes[0, 1].legend(frameon=False)

    summary = dataset.groupby(["payload_ratio", "road_class"], observed=True)["rul_km"].median().unstack("road_class")
    summary = summary.reindex(index=PAYLOAD_RATIOS, columns=["smooth", "medium", "rough"])
    image = axes[1, 0].imshow(summary.to_numpy(), cmap="RdYlGn", aspect="auto")
    axes[1, 0].set(
        title="Median RUL simulasi menurut skenario",
        xticks=range(len(summary.columns)),
        xticklabels=["Halus", "Sedang", "Kasar"],
        yticks=range(len(summary.index)),
        yticklabels=[f"{ratio:.0%}" for ratio in summary.index],
        xlabel="Kondisi jalan",
        ylabel="Rasio muatan",
    )
    for row in range(summary.shape[0]):
        for column in range(summary.shape[1]):
            axes[1, 0].text(column, row, f"{summary.iloc[row, column]:,.0f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=axes[1, 0], label="RUL median (km)")

    importance = result.feature_importance.sort_values("importance_mean")
    axes[1, 1].barh(importance["feature"], importance["importance_mean"], xerr=importance["importance_std"], color="#D97706")
    axes[1, 1].set(title="Permutation importance untuk RUL", xlabel="Kenaikan MAE saat fitur diacak", ylabel="")
    fig.savefig(destination, dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

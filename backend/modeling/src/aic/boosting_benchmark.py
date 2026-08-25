"""Comparable CatBoost, LightGBM, and XGBoost benchmarks for Model B.

This module is intentionally separate from the deployed contextual-wear rule.
Every score and weight produced here is valid only for the physics-informed
synthetic benchmark until ground-truth fleet maintenance labels are collected.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    mean_absolute_error,
    mean_squared_error,
    precision_score,
    r2_score,
    recall_score,
)
from sklearn.model_selection import GroupShuffleSplit

from .synthetic_ml import FEATURE_COLUMNS, SyntheticBenchmarkConfig


MODEL_FAMILIES = ("catboost", "lightgbm", "xgboost")
METRIC_COLUMNS = (
    "test_r2_damage_increment",
    "test_mae_damage_increment_pct",
    "test_r2_rul",
    "test_mae_rul_km",
    "test_rmse_rul_km",
    "test_pr_auc_service_due",
    "test_precision_service_due",
    "test_recall_service_due",
    "training_seconds",
)


@dataclass
class BoostingModelBundle:
    """The three target estimators for one model family and their contract."""

    model_family: str
    feature_columns: tuple[str, ...]
    config: SyntheticBenchmarkConfig
    damage_regressor: Any
    rul_regressor: Any
    service_classifier: Any


@dataclass
class BoostingBenchmarkResult:
    """Comparable results from a shared group-held-out train/test split."""

    bundles: dict[str, BoostingModelBundle]
    metrics: pd.DataFrame
    test_predictions: pd.DataFrame
    feature_importance: pd.DataFrame
    train_rows: int
    test_rows: int
    test_fleet_units: int


def _validate_dataset(dataset: pd.DataFrame) -> pd.DataFrame:
    required = set(FEATURE_COLUMNS) | {
        "fleet_unit_id",
        "truck_class",
        "road_class",
        "payload_ratio",
        "speed_kmh",
        "damage_increment_pct",
        "rul_km",
        "service_due_1000km",
    }
    missing = required - set(dataset.columns)
    if missing:
        raise ValueError(f"Synthetic benchmark is missing columns: {sorted(missing)}")
    clean = dataset.copy()
    numeric_columns = (*FEATURE_COLUMNS, "damage_increment_pct", "rul_km", "service_due_1000km")
    for column in numeric_columns:
        clean[column] = pd.to_numeric(clean[column], errors="raise")
    if clean["rul_km"].lt(0).any():
        raise ValueError("rul_km cannot be negative")
    if clean["service_due_1000km"].nunique() != 2:
        raise ValueError("Benchmark requires both service-horizon classes")
    return clean


def _import_estimators() -> dict[str, tuple[type, type]]:
    """Load optional boosting dependencies only when this benchmark is run."""

    missing: list[str] = []
    try:
        from catboost import CatBoostClassifier, CatBoostRegressor
    except ImportError:
        missing.append("catboost")
        CatBoostClassifier = CatBoostRegressor = None  # type: ignore[assignment]
    try:
        from lightgbm import LGBMClassifier, LGBMRegressor
    except ImportError:
        missing.append("lightgbm")
        LGBMClassifier = LGBMRegressor = None  # type: ignore[assignment]
    try:
        from xgboost import XGBClassifier, XGBRegressor
    except ImportError:
        missing.append("xgboost")
        XGBClassifier = XGBRegressor = None  # type: ignore[assignment]
    if missing:
        joined = ", ".join(missing)
        raise ImportError(f"Missing benchmark dependency: {joined}. Install requirements.txt first.")
    return {
        "catboost": (CatBoostRegressor, CatBoostClassifier),  # type: ignore[arg-type]
        "lightgbm": (LGBMRegressor, LGBMClassifier),  # type: ignore[arg-type]
        "xgboost": (XGBRegressor, XGBClassifier),  # type: ignore[arg-type]
    }


def _make_estimators(model_family: str, random_seed: int) -> tuple[Any, Any, Any]:
    """Return similarly sized CPU estimators for a fair, reproducible comparison."""

    classes = _import_estimators()
    if model_family not in classes:
        raise ValueError(f"Unsupported model family: {model_family}")
    regressor_class, classifier_class = classes[model_family]
    if model_family == "catboost":
        common = {
            "iterations": 450,
            "learning_rate": 0.06,
            "depth": 7,
            "l2_leaf_reg": 3.0,
            "random_seed": random_seed,
            "thread_count": 4,
            "verbose": False,
            "allow_writing_files": False,
        }
        return (
            regressor_class(loss_function="RMSE", **common),
            regressor_class(loss_function="RMSE", **common),
            classifier_class(loss_function="Logloss", **common),
        )
    if model_family == "lightgbm":
        common = {
            "n_estimators": 450,
            "learning_rate": 0.06,
            "num_leaves": 31,
            "max_depth": -1,
            "min_child_samples": 20,
            "subsample": 0.9,
            "colsample_bytree": 0.9,
            "reg_lambda": 0.1,
            "random_state": random_seed,
            "n_jobs": 4,
            "verbosity": -1,
        }
        return (
            regressor_class(objective="regression", **common),
            regressor_class(objective="regression", **common),
            classifier_class(objective="binary", **common),
        )
    common = {
        "n_estimators": 450,
        "learning_rate": 0.06,
        "max_depth": 7,
        "min_child_weight": 1.0,
        "subsample": 0.9,
        "colsample_bytree": 0.9,
        "reg_lambda": 1.0,
        "random_state": random_seed,
        "n_jobs": 4,
        "tree_method": "hist",
        "verbosity": 0,
    }
    return (
        regressor_class(objective="reg:squarederror", **common),
        regressor_class(objective="reg:squarederror", **common),
        classifier_class(objective="binary:logistic", eval_metric="logloss", **common),
    )


def _balanced_weights(target: pd.Series) -> np.ndarray:
    """Give the service-due minority class equal total training weight."""

    positive_rate = float(target.mean())
    if not 0 < positive_rate < 1:
        raise ValueError("Both service classes are required to create balanced weights")
    return np.where(target.eq(1), 0.5 / positive_rate, 0.5 / (1.0 - positive_rate))


def _feature_importance(model: Any) -> np.ndarray:
    """Normalize native tree importance to a percentage for comparison."""

    values = np.asarray(getattr(model, "feature_importances_"), dtype=float)
    total = float(values.sum())
    return values / total * 100.0 if total > 0 else values


def benchmark_boosting_models(
    dataset: pd.DataFrame,
    config: SyntheticBenchmarkConfig | None = None,
    test_size: float = 0.25,
) -> BoostingBenchmarkResult:
    """Train the three boosting families on exactly the same fleet-unit split.

    Regression targets are log-transformed at fit time because both damage and
    RUL are non-negative and long-tailed. Metrics and saved predictions are
    converted back to their original units.
    """

    config = config or SyntheticBenchmarkConfig()
    dataset = _validate_dataset(dataset)
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=config.random_seed)
    train_index, test_index = next(splitter.split(dataset, groups=dataset["fleet_unit_id"]))
    train, test = dataset.iloc[train_index].copy(), dataset.iloc[test_index].copy()
    x_train = train.loc[:, FEATURE_COLUMNS]
    x_test = test.loc[:, FEATURE_COLUMNS]
    class_target = train["service_due_1000km"].astype(int)
    sample_weights = _balanced_weights(class_target)

    metric_rows: list[dict[str, Any]] = []
    prediction_frames: list[pd.DataFrame] = []
    importance_frames: list[pd.DataFrame] = []
    bundles: dict[str, BoostingModelBundle] = {}
    base_predictions = test.loc[
        :, ["fleet_unit_id", "truck_class", "road_class", "payload_ratio", "speed_kmh", "damage_increment_pct", "rul_km", "service_due_1000km"]
    ].copy()

    for model_family in MODEL_FAMILIES:
        damage_model, rul_model, service_model = _make_estimators(model_family, config.random_seed)
        started = time.perf_counter()
        damage_model.fit(x_train, np.log1p(train["damage_increment_pct"]))
        rul_model.fit(x_train, np.log1p(train["rul_km"]))
        service_model.fit(x_train, class_target, sample_weight=sample_weights)
        training_seconds = time.perf_counter() - started

        predicted_damage = np.clip(np.expm1(damage_model.predict(x_test)), 0, None)
        predicted_rul = np.clip(np.expm1(rul_model.predict(x_test)), 0, None)
        due_probability = service_model.predict_proba(x_test)[:, 1]
        due_prediction = (due_probability >= 0.5).astype(int)
        metric_rows.append(
            {
                "model_family": model_family,
                "test_r2_damage_increment": r2_score(test["damage_increment_pct"], predicted_damage),
                "test_mae_damage_increment_pct": mean_absolute_error(test["damage_increment_pct"], predicted_damage),
                "test_r2_rul": r2_score(test["rul_km"], predicted_rul),
                "test_mae_rul_km": mean_absolute_error(test["rul_km"], predicted_rul),
                "test_rmse_rul_km": np.sqrt(mean_squared_error(test["rul_km"], predicted_rul)),
                "test_pr_auc_service_due": average_precision_score(test["service_due_1000km"], due_probability),
                "test_precision_service_due": precision_score(test["service_due_1000km"], due_prediction, zero_division=0),
                "test_recall_service_due": recall_score(test["service_due_1000km"], due_prediction, zero_division=0),
                "training_seconds": training_seconds,
            }
        )
        prediction = base_predictions.copy()
        prediction["model_family"] = model_family
        prediction["predicted_damage_increment_pct"] = predicted_damage
        prediction["predicted_rul_km"] = predicted_rul
        prediction["service_due_probability"] = due_probability
        prediction_frames.append(prediction)
        importance_frames.append(
            pd.DataFrame(
                {
                    "model_family": model_family,
                    "feature": FEATURE_COLUMNS,
                    "rul_feature_importance_pct": _feature_importance(rul_model),
                }
            )
        )
        bundles[model_family] = BoostingModelBundle(
            model_family=model_family,
            feature_columns=FEATURE_COLUMNS,
            config=config,
            damage_regressor=damage_model,
            rul_regressor=rul_model,
            service_classifier=service_model,
        )

    metrics = pd.DataFrame(metric_rows).sort_values(
        ["test_r2_rul", "test_pr_auc_service_due", "test_mae_rul_km"],
        ascending=[False, False, True],
        ignore_index=True,
    )
    return BoostingBenchmarkResult(
        bundles=bundles,
        metrics=metrics,
        test_predictions=pd.concat(prediction_frames, ignore_index=True),
        feature_importance=pd.concat(importance_frames, ignore_index=True),
        train_rows=len(train),
        test_rows=len(test),
        test_fleet_units=int(test["fleet_unit_id"].nunique()),
    )


def load_boosting_model_bundle(model_path: Path) -> BoostingModelBundle:
    """Load one benchmark model family for a dashboard integration test."""

    artifact = joblib.load(model_path)
    if not isinstance(artifact, BoostingModelBundle):
        raise TypeError(f"Unexpected artifact type: {type(artifact).__name__}")
    return artifact


def predict_boosting_model(bundle: BoostingModelBundle, feature_table: pd.DataFrame) -> pd.DataFrame:
    """Predict the three Model B targets while preserving simulation-only status."""

    missing = set(bundle.feature_columns) - set(feature_table.columns)
    if missing:
        raise ValueError(f"feature_table is missing columns: {sorted(missing)}")
    features = feature_table.loc[:, bundle.feature_columns].apply(pd.to_numeric, errors="raise")
    result = feature_table.copy()
    result["predicted_damage_increment_pct"] = np.clip(
        np.expm1(bundle.damage_regressor.predict(features)), 0, None
    )
    result["predicted_rul_km"] = np.clip(np.expm1(bundle.rul_regressor.predict(features)), 0, None)
    result["service_due_probability"] = bundle.service_classifier.predict_proba(features)[:, 1]
    result["model_family"] = bundle.model_family
    result["model_status"] = "simulation_only"
    return result


def write_boosting_benchmark_outputs(
    result: BoostingBenchmarkResult,
    model_dir: Path,
    report_dir: Path,
) -> None:
    """Persist all benchmark weights, comparison metrics, and visual report."""

    model_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    for model_family, bundle in result.bundles.items():
        _atomic_joblib_dump(bundle, model_dir / f"{model_family}_model_b_synthetic_bundle_v1.joblib")
    champion = result.metrics.iloc[0].to_dict()
    model_card = {
        "model_name": "model_b_synthetic_boosting_benchmark_v1",
        "deployment_status": "simulation_only",
        "model_families": list(MODEL_FAMILIES),
        "target_models_per_family": ["damage increment regressor", "RUL regressor", "service-horizon classifier"],
        "feature_columns": list(FEATURE_COLUMNS),
        "evaluation_protocol": {
            "split": "GroupShuffleSplit by fleet_unit_id",
            "train_rows": result.train_rows,
            "test_rows": result.test_rows,
            "held_out_fleet_units": result.test_fleet_units,
            "selection_rule": "highest test_r2_rul, then highest test_pr_auc_service_due, then lowest test_mae_rul_km",
        },
        "champion_on_synthetic_test": champion,
        "metrics": result.metrics.to_dict(orient="records"),
        "simulation_config": asdict(next(iter(result.bundles.values())).config),
        "restriction": "These metrics measure fidelity to generated simulation labels, never field-validated maintenance performance. Do not deploy before validation against real maintenance records.",
    }
    (model_dir / "model_card.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    (report_dir / "benchmark_metrics.json").write_text(json.dumps(model_card, indent=2), encoding="utf-8")
    result.metrics.to_csv(report_dir / "benchmark_metrics.csv", index=False)
    result.test_predictions.to_csv(report_dir / "test_predictions.csv", index=False)
    result.feature_importance.to_csv(report_dir / "rul_feature_importance.csv", index=False)
    _write_benchmark_figure(result, report_dir / "boosting_benchmark.png")


def _atomic_joblib_dump(value: Any, destination: Path) -> None:
    """Replace a model artifact only after its complete pickle has been written."""

    temporary = destination.with_suffix(destination.suffix + ".tmp")
    try:
        joblib.dump(value, temporary, compress=3)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        loaded_temporary = joblib.load(temporary)
        if not isinstance(loaded_temporary, type(value)):
            raise TypeError(f"Unexpected temporary artifact type: {type(loaded_temporary).__name__}")
        temporary.replace(destination)
        with destination.open("rb") as handle:
            os.fsync(handle.fileno())
        loaded_destination = joblib.load(destination)
        if not isinstance(loaded_destination, type(value)):
            raise TypeError(f"Unexpected saved artifact type: {type(loaded_destination).__name__}")
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_benchmark_figure(result: BoostingBenchmarkResult, destination: Path) -> None:
    colors = {"catboost": "#2563EB", "lightgbm": "#16A34A", "xgboost": "#D97706"}
    labels = {"catboost": "CatBoost", "lightgbm": "LightGBM", "xgboost": "XGBoost"}
    metrics = result.metrics.set_index("model_family").loc[list(MODEL_FAMILIES)].reset_index()
    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    fig.patch.set_facecolor("#F8FCF9")
    fig.suptitle("Model B · CatBoost vs LightGBM vs XGBoost", fontsize=19, fontweight="bold", color="#163020")
    fig.text(
        0.5,
        0.955,
        "Perbandingan group-held-out pada label simulasi; bukan akurasi armada nyata.",
        ha="center",
        color="#B45309",
        fontsize=10,
    )
    bar_colors = [colors[family] for family in metrics["model_family"]]
    display_names = [labels[family] for family in metrics["model_family"]]
    axes[0, 0].bar(display_names, metrics["test_r2_rul"], color=bar_colors)
    axes[0, 0].set(title="R² prediksi RUL", ylabel="R²", ylim=(0, 1.02))
    axes[0, 0].bar_label(axes[0, 0].containers[0], fmt="%.4f", padding=3)
    axes[0, 1].bar(display_names, metrics["test_mae_rul_km"], color=bar_colors)
    axes[0, 1].set(title="MAE RUL (lebih rendah lebih baik)", ylabel="km")
    axes[0, 1].bar_label(axes[0, 1].containers[0], fmt="%.0f km", padding=3)
    axes[1, 0].bar(display_names, metrics["test_pr_auc_service_due"], color=bar_colors)
    axes[1, 0].set(title="PR-AUC service due ≤ 1.000 km", ylabel="PR-AUC", ylim=(0, 1.02))
    axes[1, 0].bar_label(axes[1, 0].containers[0], fmt="%.4f", padding=3)
    for model_family in MODEL_FAMILIES:
        frame = result.test_predictions.query("model_family == @model_family").sample(
            min(900, result.test_rows), random_state=42
        )
        axes[1, 1].scatter(
            frame["rul_km"],
            frame["predicted_rul_km"],
            s=12,
            alpha=0.35,
            color=colors[model_family],
            label=labels[model_family],
        )
    maximum = float(result.test_predictions[["rul_km", "predicted_rul_km"]].to_numpy().max())
    axes[1, 1].plot([0, maximum], [0, maximum], "--", color="#DC2626", linewidth=1.2)
    axes[1, 1].set(title="RUL aktual vs prediksi", xlabel="RUL simulasi (km)", ylabel="RUL prediksi (km)")
    axes[1, 1].legend(frameon=False, loc="upper left")
    fig.savefig(destination, dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

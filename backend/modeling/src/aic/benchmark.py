"""External-data benchmark for Model B, kept separate from fleet inference."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


EVIOT_FEATURES = ("Load_Weight", "Route_Roughness", "Distance_Traveled", "Driving_Speed")
EVIOT_TARGET = "RUL"
REQUIRED_EVIOT_COLUMNS = frozenset((*EVIOT_FEATURES, EVIOT_TARGET))


@dataclass
class BenchmarkReport:
    """Evaluation details for the external-data benchmark."""

    metrics: dict[str, float]
    model: HistGradientBoostingRegressor
    row_count: int


def load_eviot_dataset(archive_path: Path) -> pd.DataFrame:
    """Load the public EVIoT CSV without mixing it into primary sensor data."""

    if not zipfile.is_zipfile(archive_path):
        raise ValueError(f"EVIoT archive is not a valid ZIP: {archive_path}")
    with zipfile.ZipFile(archive_path) as archive:
        candidates = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(candidates) != 1:
            raise ValueError("EVIoT archive must contain exactly one CSV")
        frame = pd.read_csv(archive.open(candidates[0]))
    missing = REQUIRED_EVIOT_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"EVIoT CSV is missing columns: {sorted(missing)}")
    selected = frame.loc[:, [*EVIOT_FEATURES, EVIOT_TARGET]].apply(pd.to_numeric, errors="coerce").dropna()
    if selected.empty:
        raise ValueError("EVIoT CSV contains no usable training rows")
    return selected


def train_eviot_rul_benchmark(
    dataset: pd.DataFrame,
    max_rows: int = 100_000,
    random_seed: int = 42,
) -> BenchmarkReport:
    """Train a reproducible RUL benchmark with only dashboard-compatible inputs.

    This is a transferability check, not a production fleet model: EVIoT is a
    public EV dataset, while the local project captures road vibration. The
    temporal holdout prevents the result from being presented as a test on the
    same training records.
    """

    missing = REQUIRED_EVIOT_COLUMNS - set(dataset.columns)
    if missing:
        raise ValueError(f"dataset is missing columns: {sorted(missing)}")
    if len(dataset) > max_rows:
        dataset = dataset.sample(max_rows, random_state=random_seed).sort_index()
    split_index = int(len(dataset) * 0.8)
    if split_index < 100 or len(dataset) - split_index < 25:
        raise ValueError("at least 125 rows are required for the benchmark")
    train, test = dataset.iloc[:split_index], dataset.iloc[split_index:]
    model = HistGradientBoostingRegressor(
        learning_rate=0.08,
        max_leaf_nodes=31,
        l2_regularization=0.1,
        max_iter=200,
        random_state=random_seed,
    )
    model.fit(train.loc[:, EVIOT_FEATURES], train[EVIOT_TARGET])
    prediction = model.predict(test.loc[:, EVIOT_FEATURES])
    metrics = {
        "test_mae_rul": float(mean_absolute_error(test[EVIOT_TARGET], prediction)),
        "test_rmse_rul": float(np.sqrt(mean_squared_error(test[EVIOT_TARGET], prediction))),
        "test_r2_rul": float(r2_score(test[EVIOT_TARGET], prediction)),
        "train_rows": float(len(train)),
        "test_rows": float(len(test)),
    }
    return BenchmarkReport(metrics=metrics, model=model, row_count=len(dataset))


def write_benchmark_outputs(report: BenchmarkReport, output_dir: Path) -> None:
    """Save model/metrics separately from the deployable rule-based Model B."""

    output_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(report.model, output_dir / "eviot_rul_benchmark.joblib")
    payload: dict[str, Any] = {
        "dataset": "EVIoT-PredictiveMaint Dataset (external benchmark)",
        "features": list(EVIOT_FEATURES),
        "target": EVIOT_TARGET,
        "rows_used": report.row_count,
        "metrics": report.metrics,
        "deployment_note": "Not deployed to local trips; local load-cell and maintenance labels are still required.",
    }
    (output_dir / "metrics.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

"""Model A: session-relative road-roughness estimation from IMU and GPS."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import joblib
from scipy.integrate import cumulative_trapezoid, trapezoid
from scipy.signal import butter, find_peaks, sosfiltfilt, welch
from scipy.stats import kurtosis
from sklearn.cluster import KMeans
from sklearn.linear_model import HuberRegressor
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import RobustScaler

from .config import RoughnessConfig
from .data import ArchiveValidationError, SensorSession, discover_archives, load_session_archive


CORE_FEATURES = ("rms_vertical", "p95_abs", "vdv_per_m", "psd_0_5_3hz", "psd_3_15hz")


@dataclass
class RoughnessModelArtifact:
    """Fitted components needed to reproduce one session's Model A scores."""

    session_id: str
    config: RoughnessConfig
    feature_names: tuple[str, ...]
    corrected_feature_names: tuple[str, ...]
    reference_speed_kmh: float
    speed_models: dict[str, HuberRegressor]
    scaler: RobustScaler
    kmeans: KMeans
    cluster_name_map: dict[int, str]
    hotspot_threshold: float


@dataclass
class ModelAReport:
    """Tabular outputs intentionally shaped for both notebooks and a dashboard."""

    archive_audit: pd.DataFrame
    session_summary: pd.DataFrame
    segments: pd.DataFrame
    artifacts: dict[str, RoughnessModelArtifact]


def _estimate_sampling_hz(timestamps_s: np.ndarray, config: RoughnessConfig) -> float:
    if config.target_sampling_hz is not None:
        return config.target_sampling_hz
    steps = np.diff(np.unique(timestamps_s))
    steps = steps[steps > 0]
    if len(steps) == 0:
        raise ArchiveValidationError("accelerometer timestamps are not increasing")
    observed_hz = 1.0 / float(np.median(steps))
    rounded_hz = round(observed_hz / 5.0) * 5.0
    if rounded_hz < 10:
        raise ArchiveValidationError(f"accelerometer sampling rate is too low ({observed_hz:.2f} Hz)")
    return float(rounded_hz)


def _haversine_m(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    radius_m = 6_371_000.0
    lat1_rad, lat2_rad = np.radians(lat1), np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)
    a_value = np.sin(delta_lat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    return 2 * radius_m * np.arctan2(np.sqrt(a_value), np.sqrt(1 - a_value))


def _band_power(frequency: np.ndarray, power: np.ndarray, lower_hz: float, upper_hz: float) -> float:
    mask = (frequency >= lower_hz) & (frequency < upper_hz)
    return float(trapezoid(power[mask], frequency[mask])) if mask.sum() >= 2 else 0.0


def _robust_mad(values: np.ndarray) -> float:
    return float(np.median(np.abs(values - np.median(values))))


def _nearest_sample_gap(grid: np.ndarray, observation_times: np.ndarray) -> np.ndarray:
    right = np.searchsorted(observation_times, grid, side="left")
    right = np.clip(right, 0, len(observation_times) - 1)
    left = np.clip(right - 1, 0, len(observation_times) - 1)
    return np.minimum(np.abs(grid - observation_times[left]), np.abs(grid - observation_times[right]))


def _align_session(session: SensorSession, config: RoughnessConfig) -> tuple[pd.DataFrame, dict[str, float]]:
    accelerometer = session.imu.loc[session.imu["sensor_type"].str.lower() == "accelerometer"].copy()
    if accelerometer.empty:
        raise ArchiveValidationError("imu.csv has no accelerometer rows")
    accelerometer = accelerometer.sort_values("sensor_timestamp_ns").drop_duplicates("sensor_timestamp_ns")
    gps = session.gps.sort_values("elapsed_realtime_ns").drop_duplicates("elapsed_realtime_ns").copy()
    if len(accelerometer) < 100 or len(gps) < 3:
        raise ArchiveValidationError("not enough accelerometer or GPS samples")

    origin_ns = min(accelerometer["sensor_timestamp_ns"].min(), gps["elapsed_realtime_ns"].min())
    acc_time = (accelerometer["sensor_timestamp_ns"].to_numpy(dtype=float) - origin_ns) / 1e9
    gps_time = (gps["elapsed_realtime_ns"].to_numpy(dtype=float) - origin_ns) / 1e9
    sampling_hz = _estimate_sampling_hz(acc_time, config)
    if sampling_hz <= 2 * config.filter_cutoff_hz:
        raise ArchiveValidationError("sampling rate is incompatible with the configured filter")

    start = np.ceil(acc_time.min() * sampling_hz) / sampling_hz
    end = np.floor(acc_time.max() * sampling_hz) / sampling_hz
    grid = np.arange(start, end + 0.5 / sampling_hz, 1.0 / sampling_hz)
    if len(grid) < max(100, 3 * config.filter_order):
        raise ArchiveValidationError("session is too short for zero-phase filtering")

    acc_xyz = accelerometer[["x", "y", "z"]].to_numpy(dtype=float)
    regular_xyz = np.column_stack([np.interp(grid, acc_time, acc_xyz[:, axis]) for axis in range(3)])
    lowpass = butter(config.filter_order, config.filter_cutoff_hz, btype="lowpass", fs=sampling_hz, output="sos")
    highpass = butter(config.filter_order, config.filter_cutoff_hz, btype="highpass", fs=sampling_hz, output="sos")
    gravity_xyz = np.column_stack([sosfiltfilt(lowpass, regular_xyz[:, axis]) for axis in range(3)])
    dynamic_xyz = np.column_stack([sosfiltfilt(highpass, regular_xyz[:, axis]) for axis in range(3)])
    gravity_norm = np.linalg.norm(gravity_xyz, axis=1)
    gravity_unit = gravity_xyz / np.clip(gravity_norm[:, None], 1e-6, None)
    vertical_acc = np.sum(dynamic_xyz * gravity_unit, axis=1)

    speed_mps = gps["speed_mps"].to_numpy(dtype=float)
    distance_m = cumulative_trapezoid(speed_mps, gps_time, initial=0.0)
    gps_gap = _nearest_sample_gap(grid, gps_time)
    imu_gap = _nearest_sample_gap(grid, acc_time)
    allowed_imu_gap_s = max(2.5 / sampling_hz, 0.04)
    aligned = pd.DataFrame(
        {
            "t_s": grid,
            "vertical_acc": vertical_acc,
            "resultant_acc": np.linalg.norm(dynamic_xyz, axis=1),
            "vertical_jerk": np.gradient(vertical_acc, 1.0 / sampling_hz),
            "speed_kmh": np.interp(grid, gps_time, speed_mps * 3.6),
            "distance_m": np.interp(grid, gps_time, distance_m),
            "latitude": np.interp(grid, gps_time, gps["latitude"]),
            "longitude": np.interp(grid, gps_time, gps["longitude"]),
            "gps_accuracy_m": np.interp(grid, gps_time, gps["accuracy_m"]),
            "nearest_gps_gap_s": gps_gap,
            "nearest_imu_gap_s": imu_gap,
            "gravity_norm": gravity_norm,
        }
    )
    aligned["edge_valid"] = aligned["t_s"].between(aligned["t_s"].min() + 2, aligned["t_s"].max() - 2)
    aligned["gps_valid"] = aligned["nearest_gps_gap_s"] <= config.max_gps_tolerance_s
    aligned["imu_valid"] = aligned["nearest_imu_gap_s"] <= allowed_imu_gap_s
    aligned["moving"] = aligned["speed_kmh"] >= config.min_speed_kmh
    aligned["analysis_valid"] = aligned["edge_valid"] & aligned["gps_valid"] & aligned["imu_valid"] & aligned["moving"]
    aligned["segment_id"] = np.floor(aligned["distance_m"] / config.segment_length_m).astype(int)

    haversine_distance_m = float(
        _haversine_m(
            gps["latitude"].to_numpy()[:-1],
            gps["longitude"].to_numpy()[:-1],
            gps["latitude"].to_numpy()[1:],
            gps["longitude"].to_numpy()[1:],
        ).sum()
    )
    diagnostics = {
        "sampling_hz": sampling_hz,
        "distance_speed_integrated_m": float(distance_m[-1]),
        "distance_haversine_m": haversine_distance_m,
        "valid_sample_share": float(aligned["analysis_valid"].mean()),
    }
    return aligned, diagnostics


def _extract_segment_features(segment: pd.DataFrame, config: RoughnessConfig, sampling_hz: float) -> dict[str, Any]:
    valid = segment.loc[segment["analysis_valid"]].sort_values("t_s").copy()
    acceleration = valid["vertical_acc"].to_numpy(dtype=float)
    jerk = valid["vertical_jerk"].to_numpy(dtype=float)
    times = valid["t_s"].to_numpy(dtype=float)
    distances = valid["distance_m"].to_numpy(dtype=float)
    coverage_m = float(distances.max() - distances.min()) if len(distances) else 0.0
    maximum_gap_s = float(np.diff(times).max()) if len(times) > 1 else np.inf
    absolute_acceleration = np.abs(acceleration)
    prominence = max(3 * _robust_mad(absolute_acceleration), 0.25)
    peaks, _ = find_peaks(absolute_acceleration, prominence=prominence, distance=max(1, int(0.1 * sampling_hz)))
    nperseg = min(128, len(acceleration))
    frequency, power = welch(
        acceleration, fs=sampling_hz, nperseg=nperseg, noverlap=nperseg // 2, scaling="density"
    )

    reasons: list[str] = []
    if coverage_m < config.min_segment_coverage_m:
        reasons.append(f"coverage<{config.min_segment_coverage_m:g}m")
    if len(valid) < config.min_samples_per_segment:
        reasons.append(f"samples<{config.min_samples_per_segment}")
    if maximum_gap_s > config.max_moving_sample_gap_s:
        reasons.append("discontinuous")
    if float(valid["gps_accuracy_m"].median()) > config.max_median_gps_accuracy_m:
        reasons.append(f"gps>{config.max_median_gps_accuracy_m:g}m")

    segment_id = int(segment["segment_id"].iloc[0])
    segment_distance = max(coverage_m, 1e-6)
    return {
        "segment_id": segment_id,
        "segment_start_m": segment_id * config.segment_length_m,
        "segment_end_m": (segment_id + 1) * config.segment_length_m,
        "start_time_s": float(times.min()),
        "end_time_s": float(times.max()),
        "latitude": float(valid["latitude"].median()),
        "longitude": float(valid["longitude"].median()),
        "mean_speed_kmh": float(valid["speed_kmh"].mean()),
        "median_gps_accuracy_m": float(valid["gps_accuracy_m"].median()),
        "n_samples": int(len(valid)),
        "distance_coverage_m": coverage_m,
        "max_sample_gap_s": maximum_gap_s,
        "rms_vertical": float(np.sqrt(np.mean(acceleration**2))),
        "p95_abs": float(np.quantile(absolute_acceleration, 0.95)),
        "vdv_per_m": float((np.sum(acceleration**4) / sampling_hz / segment_distance) ** 0.25),
        "peak_density_per_m": float(len(peaks) / segment_distance),
        "psd_0_5_3hz": _band_power(frequency, power, 0.5, 3.0),
        "psd_3_15hz": _band_power(frequency, power, 3.0, 15.0),
        "data_quality_flag": "OK" if not reasons else " | ".join(reasons),
        "valid_segment": not reasons,
    }


def _score_session(
    features: pd.DataFrame, config: RoughnessConfig
) -> tuple[pd.DataFrame, dict[str, Any], RoughnessModelArtifact]:
    valid = features.loc[features["valid_segment"]].copy()
    if len(valid) < config.min_model_segments:
        raise ArchiveValidationError(
            f"only {len(valid)} valid segments; minimum for Model A is {config.min_model_segments}"
        )
    reference_speed_kmh = float(valid["mean_speed_kmh"].median())
    diagnostics: dict[str, Any] = {
        "reference_speed_kmh": reference_speed_kmh,
        "model_reliability": "limited_segments" if len(valid) < 50 else "standard",
    }
    corrected_columns: list[str] = []
    speed_models: dict[str, HuberRegressor] = {}
    for feature in CORE_FEATURES:
        positive = valid[feature].clip(lower=1e-9)
        speed = valid["mean_speed_kmh"].clip(lower=1e-6)
        regressor = HuberRegressor(epsilon=1.35, alpha=0.0001, max_iter=1000).fit(
            np.log(speed).to_numpy().reshape(-1, 1), np.log(positive).to_numpy()
        )
        raw_gamma = float(regressor.coef_[0])
        raw_correlation = float(valid[[feature, "mean_speed_kmh"]].corr().iloc[0, 1])
        gamma = max(0.0, raw_gamma) if raw_correlation > 0 else 0.0
        column = f"{feature}_speed_corrected"
        valid[column] = valid[feature] * (reference_speed_kmh / speed) ** gamma
        corrected_columns.append(column)
        speed_models[feature] = regressor
        diagnostics[f"speed_gamma_{feature}"] = gamma

    percentile_matrix = valid[corrected_columns].rank(pct=True, method="average")
    valid["relative_roughness_score"] = (100 * percentile_matrix.median(axis=1)).round(1)
    scaler = RobustScaler(quantile_range=(25.0, 75.0))
    matrix = scaler.fit_transform(percentile_matrix.to_numpy(dtype=float))
    if np.unique(matrix, axis=0).shape[0] < config.cluster_count:
        raise ArchiveValidationError("roughness feature matrix has fewer unique rows than clusters")
    clustering = KMeans(n_clusters=config.cluster_count, n_init=50, random_state=config.random_seed, algorithm="lloyd")
    valid["raw_cluster"] = clustering.fit_predict(matrix)
    ordered_clusters = valid.groupby("raw_cluster")["relative_roughness_score"].median().sort_values().index.tolist()
    labels = ["Rendah", "Sedang", "Tinggi"]
    if config.cluster_count != 3:
        labels = [f"Level {index + 1}" for index in range(config.cluster_count)]
    cluster_name_map = dict(zip(ordered_clusters, labels))
    valid["roughness_class"] = valid["raw_cluster"].map(cluster_name_map)
    threshold = float(valid["relative_roughness_score"].quantile(0.90))
    valid["hotspot_flag"] = (valid["roughness_class"] == labels[-1]) & (
        valid["relative_roughness_score"] >= threshold
    )
    diagnostics.update(
        {
            "silhouette_score": float(silhouette_score(matrix, valid["raw_cluster"])),
            "davies_bouldin_score": float(davies_bouldin_score(matrix, valid["raw_cluster"])),
            "calinski_harabasz_score": float(calinski_harabasz_score(matrix, valid["raw_cluster"])),
            "hotspot_threshold": threshold,
        }
    )
    artifact = RoughnessModelArtifact(
        session_id="",
        config=config,
        feature_names=CORE_FEATURES,
        corrected_feature_names=tuple(corrected_columns),
        reference_speed_kmh=reference_speed_kmh,
        speed_models=speed_models,
        scaler=scaler,
        kmeans=clustering,
        cluster_name_map=cluster_name_map,
        hotspot_threshold=threshold,
    )
    return valid, diagnostics, artifact


def process_session(
    session: SensorSession, config: RoughnessConfig
) -> tuple[pd.DataFrame, dict[str, Any], RoughnessModelArtifact]:
    """Process one archive; scores remain comparable only inside this session."""

    aligned, diagnostics = _align_session(session, config)
    sampling_hz = float(diagnostics["sampling_hz"])
    rows = [
        _extract_segment_features(group, config, sampling_hz)
        for _, group in aligned.groupby("segment_id", sort=True)
        if len(group.loc[group["analysis_valid"]]) >= 2
    ]
    if not rows:
        raise ArchiveValidationError("no moving GPS-aligned segments were found")
    features = pd.DataFrame(rows).sort_values("segment_id").reset_index(drop=True)
    scored, score_diagnostics, artifact = _score_session(features, config)
    artifact.session_id = session.session_id
    final = features.merge(
        scored.drop(columns=["valid_segment", "data_quality_flag"]), on="segment_id", how="left", suffixes=("", "_model")
    )
    final.insert(0, "session_id", session.session_id)
    final.insert(1, "archive_name", session.archive_path.name)
    final.insert(2, "vehicle", str(session.session_info.get("vehicle", "unknown")))
    final.insert(3, "mount_position", str(session.session_info.get("mount_position", "unknown")))
    final.insert(4, "sampling_label", str(session.session_info.get("sampling_label", "unknown")))
    summary: dict[str, Any] = {
        "session_id": session.session_id,
        "archive_name": session.archive_path.name,
        "vehicle": session.session_info.get("vehicle", "unknown"),
        "status": "processed",
        "total_segments": int(len(final)),
        "valid_segments": int(final["relative_roughness_score"].notna().sum()),
        "hotspots": int(final["hotspot_flag"].fillna(False).sum()),
        **diagnostics,
        **score_diagnostics,
    }
    return final, summary, artifact


def process_all_archives(data_dir: Path, config: RoughnessConfig | None = None) -> ModelAReport:
    """Run Model A for every ZIP in a folder and retain a full audit trail."""

    config = config or RoughnessConfig()
    audit_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    segment_frames: list[pd.DataFrame] = []
    artifacts: dict[str, RoughnessModelArtifact] = {}
    archives = discover_archives(data_dir)
    if not archives:
        raise FileNotFoundError(f"No .zip archives found in {data_dir}")
    for archive_path in archives:
        try:
            session = load_session_archive(archive_path)
            segments, summary, artifact = process_session(session, config)
        except (ArchiveValidationError, OSError, ValueError) as exc:
            audit_rows.append(
                {"archive_name": archive_path.name, "status": "skipped", "reason": str(exc), "session_id": None}
            )
            continue
        audit_rows.append(
            {"archive_name": archive_path.name, "status": "processed", "reason": None, "session_id": session.session_id}
        )
        summaries.append(summary)
        segment_frames.append(segments)
        artifacts[session.session_id] = artifact
    empty_segments = pd.DataFrame(
        columns=["session_id", "archive_name", "segment_id", "relative_roughness_score", "roughness_class"]
    )
    return ModelAReport(
        archive_audit=pd.DataFrame(audit_rows),
        session_summary=pd.DataFrame(summaries),
        segments=pd.concat(segment_frames, ignore_index=True) if segment_frames else empty_segments,
        artifacts=artifacts,
    )


def write_model_a_outputs(report: ModelAReport, output_dir: Path, config: RoughnessConfig | None = None) -> None:
    """Persist dashboard-friendly Model A tables plus run configuration."""

    output_dir.mkdir(parents=True, exist_ok=True)
    report.archive_audit.to_csv(output_dir / "archive_audit.csv", index=False)
    report.session_summary.to_csv(output_dir / "session_summary.csv", index=False)
    report.segments.to_csv(output_dir / "segments.csv", index=False)
    (output_dir / "run_config.json").write_text(
        json.dumps(asdict(config or RoughnessConfig()), indent=2), encoding="utf-8"
    )


def write_model_a_artifacts(report: ModelAReport, model_dir: Path) -> None:
    """Save all fitted Model A weights with a human-readable manifest."""

    model_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "model_type": "session_relative_roughness",
        "artifact_format": "joblib",
        "comparability": "Scores are valid within a session; do not rank across devices or vehicles.",
        "sessions": [],
    }
    for session_id, artifact in sorted(report.artifacts.items()):
        filename = f"roughness_{session_id}.joblib"
        joblib.dump(artifact, model_dir / filename)
        manifest["sessions"].append(
            {
                "session_id": session_id,
                "artifact": filename,
                "sampling_hz": artifact.config.target_sampling_hz,
                "reference_speed_kmh": artifact.reference_speed_kmh,
                "features": list(artifact.feature_names),
            }
        )
    (model_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

"""Input validation and loading for mobile-sensor session archives."""

from __future__ import annotations

import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


REQUIRED_FILES = frozenset(
    {
        "imu.csv",
        "gps.csv",
        "orientation.csv",
        "markers.csv",
        "metadata.txt",
        "quality_report.json",
        "session_info.json",
    }
)
REQUIRED_COLUMNS = {
    "imu.csv": frozenset(
        {"session_id", "sensor_timestamp_ns", "wall_time_ms", "sensor_type", "x", "y", "z", "accuracy"}
    ),
    "gps.csv": frozenset(
        {"session_id", "elapsed_realtime_ns", "wall_time_ms", "latitude", "longitude", "speed_mps", "accuracy_m"}
    ),
    "orientation.csv": frozenset(
        {"session_id", "sensor_timestamp_ns", "quat_x", "quat_y", "quat_z", "quat_w"}
    ),
    "markers.csv": frozenset({"session_id", "elapsed_realtime_ns", "wall_time_ms", "label", "latitude", "longitude"}),
}


class ArchiveValidationError(ValueError):
    """Raised when an archive cannot safely enter the modelling pipeline."""


@dataclass
class SensorSession:
    """A fully validated capture session loaded from one ZIP archive."""

    archive_path: Path
    session_info: dict[str, Any]
    quality_report: dict[str, Any]
    metadata: dict[str, str]
    imu: pd.DataFrame
    gps: pd.DataFrame
    orientation: pd.DataFrame
    markers: pd.DataFrame

    @property
    def session_id(self) -> str:
        return str(self.session_info.get("session_id") or self.archive_path.stem)


def discover_archives(data_dir: Path) -> list[Path]:
    """Return user-provided ZIP files in deterministic order."""

    return sorted(path for path in data_dir.glob("*.zip") if path.is_file())


def _parse_metadata(payload: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in payload.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            metadata[key.strip()] = value.strip()
    return metadata


def _require_columns(frame: pd.DataFrame, filename: str) -> None:
    missing = REQUIRED_COLUMNS[filename] - set(frame.columns)
    if missing:
        raise ArchiveValidationError(f"{filename} is missing columns: {sorted(missing)}")


def _coerce_numeric(frame: pd.DataFrame, columns: list[str], filename: str) -> pd.DataFrame:
    result = frame.copy()
    for column in columns:
        result[column] = pd.to_numeric(result[column], errors="coerce")
    if result[columns].isna().any().any():
        invalid = result[columns].isna().sum()
        details = ", ".join(f"{name}={count}" for name, count in invalid.items() if count)
        raise ArchiveValidationError(f"{filename} contains non-numeric required values: {details}")
    return result


def load_session_archive(archive_path: Path) -> SensorSession:
    """Load a capture archive, failing early on corruption or schema drift."""

    if not zipfile.is_zipfile(archive_path):
        raise ArchiveValidationError("not a valid ZIP archive")

    try:
        with zipfile.ZipFile(archive_path) as archive:
            members = set(archive.namelist())
            missing = REQUIRED_FILES - members
            if missing:
                raise ArchiveValidationError(f"missing required files: {sorted(missing)}")

            frames = {
                name: pd.read_csv(archive.open(name))
                for name in ("imu.csv", "gps.csv", "orientation.csv", "markers.csv")
            }
            session_info = json.loads(archive.read("session_info.json"))
            quality_report = json.loads(archive.read("quality_report.json"))
            metadata = _parse_metadata(archive.read("metadata.txt").decode("utf-8"))
    except zipfile.BadZipFile as exc:
        raise ArchiveValidationError("ZIP central directory is unreadable") from exc
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveValidationError(f"cannot read archive metadata: {exc}") from exc

    for name, frame in frames.items():
        _require_columns(frame, name)

    imu = _coerce_numeric(
        frames["imu.csv"], ["sensor_timestamp_ns", "wall_time_ms", "x", "y", "z", "accuracy"], "imu.csv"
    )
    gps = _coerce_numeric(
        frames["gps.csv"],
        ["elapsed_realtime_ns", "wall_time_ms", "latitude", "longitude", "speed_mps", "accuracy_m"],
        "gps.csv",
    )
    orientation = _coerce_numeric(
        frames["orientation.csv"],
        ["sensor_timestamp_ns", "quat_x", "quat_y", "quat_z", "quat_w"],
        "orientation.csv",
    )
    markers = _coerce_numeric(
        frames["markers.csv"], ["elapsed_realtime_ns", "wall_time_ms", "latitude", "longitude"], "markers.csv"
    )
    return SensorSession(archive_path, session_info, quality_report, metadata, imu, gps, orientation, markers)

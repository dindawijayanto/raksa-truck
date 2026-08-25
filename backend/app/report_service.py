"""Read-only access to the validated Model A and rule-based Model B reports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


class ModelReportService:
    """Serve precomputed report outputs without re-running sensor processing in HTTP requests."""

    def __init__(self, data_dir: Path, model_dir: Path) -> None:
        self.model_a_sessions = pd.read_csv(data_dir / "model_a" / "session_summary.csv")
        self.model_a_segment_rows = pd.read_csv(data_dir / "model_a" / "segments.csv")
        self.model_b_sessions = pd.read_csv(data_dir / "model_b" / "session_summary.csv")
        self.model_a_manifest = json.loads((model_dir / "model_a" / "manifest.json").read_text(encoding="utf-8"))

    @staticmethod
    def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
        """Convert pandas/numpy values to JSON-safe built-in Python values."""

        records = json.loads(frame.to_json(orient="records"))
        return records

    def model_a_session_summaries(self) -> dict[str, Any]:
        columns = [
            "session_id",
            "archive_name",
            "vehicle",
            "status",
            "total_segments",
            "valid_segments",
            "hotspots",
            "sampling_hz",
            "distance_speed_integrated_m",
            "reference_speed_kmh",
            "model_reliability",
            "silhouette_score",
        ]
        sessions = self.model_a_sessions.loc[:, columns].sort_values("session_id")
        return {
            "model_name": "Model A — session-relative road roughness",
            "model_status": "report_backed",
            "comparability": self.model_a_manifest["comparability"],
            "sessions": self._records(sessions),
            "total_sessions": int(len(sessions)),
            "total_valid_segments": int(sessions["valid_segments"].sum()),
            "total_hotspots": int(sessions["hotspots"].sum()),
        }

    def model_a_segments(self, session_id: str, limit: int) -> dict[str, Any] | None:
        session = self.model_a_sessions.loc[self.model_a_sessions["session_id"].eq(session_id)]
        if session.empty:
            return None
        segments = self.model_a_segment_rows.loc[
            self.model_a_segment_rows["session_id"].eq(session_id)
            & self.model_a_segment_rows["valid_segment"].eq(True)
            & self.model_a_segment_rows["relative_roughness_score"].notna(),
            [
                "segment_id",
                "latitude",
                "longitude",
                "segment_start_m",
                "segment_end_m",
                "mean_speed_kmh",
                "relative_roughness_score",
                "roughness_class",
                "hotspot_flag",
                "data_quality_flag",
            ],
        ].head(limit)
        roughness_counts = segments["roughness_class"].value_counts().reindex(["Rendah", "Sedang", "Tinggi"], fill_value=0)
        return {
            "session_id": session_id,
            "comparability": self.model_a_manifest["comparability"],
            "roughness_counts": {label.lower(): int(value) for label, value in roughness_counts.items()},
            "segments": self._records(segments),
        }

    def dashboard_overview(self) -> dict[str, Any]:
        model_a = self.model_a_session_summaries()
        model_b_columns = [
            "session_id",
            "segments",
            "distance_km",
            "mean_load_kg",
            "mean_roughness_score",
            "mean_context_score",
            "peak_context_score",
            "high_context_segments",
            "final_wear_score",
            "estimated_remaining_km",
            "overload_segments",
            "service_alert",
        ]
        model_b_sessions = self.model_b_sessions.loc[:, model_b_columns].sort_values("session_id")
        return {
            "model_a": model_a,
            "model_b_rule_based": {
                "model_name": "Model B — contextual wear rule",
                "model_status": "operational_rule_based",
                "sessions": self._records(model_b_sessions),
            },
        }

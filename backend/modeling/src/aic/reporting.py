"""Presentation outputs for Model B that reuse the dashboard-facing tables."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import WearConfig
from .model_b import WearReport, score_wear


PALETTE = {"Rendah": "#15803D", "Sedang": "#D97706", "Tinggi": "#DC2626"}


def compare_load_scenarios(roughness_segments: pd.DataFrame, config: WearConfig) -> pd.DataFrame:
    """Compare transparent 50/75/100 percent loading scenarios for one route."""

    scenario_rows: list[pd.DataFrame] = []
    for ratio, label in ((0.50, "50% limit"), (0.75, "75% limit"), (1.00, "100% limit")):
        scenario_config = replace(config, load_kg=config.load_limit_kg * ratio)
        scenario = score_wear(roughness_segments, scenario_config).session_summary.copy()
        scenario["scenario"] = label
        scenario["load_ratio"] = ratio
        scenario_rows.append(scenario)
    return pd.concat(scenario_rows, ignore_index=True)


def _distance_axis(frame: pd.DataFrame) -> pd.Series:
    if "segment_start_m" in frame.columns:
        return frame["segment_start_m"] / 1000.0
    return frame["distance_km"].cumsum()


def write_model_b_presentation(
    report: WearReport,
    roughness_segments: pd.DataFrame,
    config: WearConfig,
    output_dir: Path,
) -> None:
    """Create a concise visual brief and scenario table from actual model output."""

    output_dir.mkdir(parents=True, exist_ok=True)
    scenarios = compare_load_scenarios(roughness_segments, config)
    scenarios.to_csv(output_dir / "load_scenarios.csv", index=False)
    segments = report.segment_wear.copy()
    summary = report.session_summary.copy()
    if segments.empty:
        return

    fig, axes = plt.subplots(2, 2, figsize=(16, 10), constrained_layout=True)
    fig.patch.set_facecolor("#F8FCF9")
    load_provenance = ", ".join(sorted(report.segment_wear["load_source"].dropna().unique()))
    fig.suptitle("Model B · Contextual Wear Insight", fontsize=19, fontweight="bold", color="#163020")
    fig.text(
        0.5,
        0.955,
        f"Beban + kekasaran relatif + jarak · sumber muatan: {load_provenance} · bukan probabilitas kegagalan.",
        ha="center",
        color="#64748B",
        fontsize=10,
    )

    scatter = None
    for session_id, frame in segments.groupby("session_id", sort=True):
        scatter = axes[0, 0].scatter(
            _distance_axis(frame),
            frame["context_score"],
            c=frame["context_score"],
            cmap="RdYlGn_r",
            vmin=0,
            vmax=100,
            s=28,
            alpha=0.9,
            label=str(session_id)[-6:],
        )
    axes[0, 0].axhline(70, color="#DC2626", linestyle="--", linewidth=1.1, label="Ambang tinggi")
    axes[0, 0].set(title="Skor konteks sepanjang rute", xlabel="Jarak dalam sesi (km)", ylabel="Context score (0–100)")
    axes[0, 0].legend(title="Sesi", frameon=False, fontsize=8)
    if scatter is not None:
        fig.colorbar(scatter, ax=axes[0, 0], label="Context score")

    contribution = segments.groupby("session_id", as_index=True)[["load_component_score", "roughness_component_score"]].mean()
    contribution.plot(
        kind="bar",
        stacked=True,
        color=["#2563EB", "#D97706"],
        ax=axes[0, 1],
        width=0.72,
    )
    axes[0, 1].set(title="Kontributor rata-rata skor konteks", xlabel="Sesi", ylabel="Poin skor")
    axes[0, 1].legend(["Beban", "Kekasaran"], frameon=False)
    axes[0, 1].tick_params(axis="x", rotation=20)

    for band, color in PALETTE.items():
        subset = segments.loc[segments["wear_risk_band"] == band]
        axes[1, 0].scatter(
            subset["roughness_ratio"] * 100,
            subset["wear_multiplier"],
            color=color,
            alpha=0.7,
            s=30,
            label=band,
        )
    axes[1, 0].set(
        title="Efek gabungan kondisi operasi",
        xlabel="Kekasaran relatif (0–100)",
        ylabel="Pengali laju keausan",
    )
    axes[1, 0].legend(title="Band risiko", frameon=False)

    scenario_summary = scenarios.groupby("scenario", as_index=False).agg(
        mean_remaining_km=("estimated_remaining_km", "mean"),
        mean_context_score=("mean_context_score", "mean"),
    )
    scenario_summary = scenario_summary.set_index("scenario").reindex(["50% limit", "75% limit", "100% limit"])
    bars = axes[1, 1].bar(
        scenario_summary.index,
        scenario_summary["mean_remaining_km"],
        color=["#86EFAC", "#F4C95D", "#FCA5A5"],
    )
    axes[1, 1].bar_label(bars, labels=[f"{value:,.0f} km" for value in scenario_summary["mean_remaining_km"]], padding=4)
    axes[1, 1].set(title="Dampak skenario muatan", xlabel="Muatan terhadap limit", ylabel="Estimasi jarak servis tersisa (km)")
    axes[1, 1].set_ylim(bottom=0)

    fig.savefig(output_dir / "model_b_overview.png", dpi=170, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    top = summary.sort_values("peak_context_score", ascending=False).iloc[0]
    brief = "\n".join(
        [
            "# Model B — Operational Brief",
            "",
            f"Provenance muatan: `{load_provenance}`. Verifikasi asal profile sebelum memakai hasil untuk keputusan servis.",
            "",
            f"- Sesi dianalisis: {len(summary)}",
            f"- Context score puncak: {top['peak_context_score']:.1f} ({top['session_id']})",
            f"- Pengali keausan rata-rata: {summary['mean_wear_multiplier'].mean():.2f}×",
            f"- Estimasi sisa jarak rata-rata: {summary['estimated_remaining_km'].mean():,.0f} km",
            "",
            "Lihat `model_b_overview.png` dan `load_scenarios.csv` untuk visual dan detail per-skenario.",
        ]
    )
    (output_dir / "operational_brief.md").write_text(brief, encoding="utf-8")

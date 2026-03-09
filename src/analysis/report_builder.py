from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.plotting import plot_comparison
from src.utils.paths import REPORT_FIGURES_DIR, REPORT_SUMMARIES_DIR


def build_markdown_report(output_dir: Path, summary_df: pd.DataFrame, metrics_df: pd.DataFrame) -> Path:
    row = summary_df.iloc[0]
    report_lines = [
        f"# {row['scenario_name']}",
        "",
        "## Research framing",
        "- Purpose: surface transport prediction for oil-adsorbed microplastics using OpenDrift PlastDrift.",
        "- Modeling note: polymer/oil/salinity differences are represented through scenario parameter mapping, not direct chemistry.",
        "",
        "## Final metrics",
        f"- Final max distance (km): {row['final_max_distance_km']:.3f}",
        f"- Final mean distance (km): {row['final_mean_distance_km']:.3f}",
        f"- Final centroid distance (km): {row['final_centroid_distance_km']:.3f}",
        f"- Final convex hull area (km^2): {row['final_convex_hull_area_km2']:.3f}",
        f"- Surface retention ratio: {row['final_surface_retention_ratio']:.3f}",
        "",
        "## Snapshot metrics",
    ]
    for hour in (24, 72, 168):
        key = f"h{hour}"
        if f"{key}_actual_hour" in row:
            report_lines.extend(
                [
                    f"- {hour}h request (nearest={row[f'{key}_actual_hour']:.1f}h): "
                    f"max={row[f'{key}_max_distance_km']:.3f} km, "
                    f"centroid={row[f'{key}_centroid_distance_km']:.3f} km, "
                    f"area={row[f'{key}_convex_hull_area_km2']:.3f} km^2",
                ]
            )
    report_lines.extend(
        [
            "",
            "## Limitations",
            "- This project is a surface-only baseline and does not model oil weathering.",
            "- Demo mode uses synthetic current/wind fields and is only for verification.",
            "- Real-world interpretation depends on the quality and coverage of user-supplied NetCDF forcing data.",
        ]
    )
    path = output_dir / "analysis_report.md"
    path.write_text("\n".join(report_lines), encoding="utf-8")
    return path


def build_comparison_report(result_dirs: list[Path]) -> dict[str, Path]:
    REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    metrics_map: dict[str, pd.DataFrame] = {}
    for result_dir in result_dirs:
        summary_path = result_dir / "summary.csv"
        metrics_path = result_dir / "metrics.csv"
        if summary_path.exists() and metrics_path.exists():
            summary_df = pd.read_csv(summary_path)
            metrics_df = pd.read_csv(metrics_path, parse_dates=["timestamp"])
            summaries.append(summary_df)
            metrics_map[str(summary_df.iloc[0]["scenario_name"])] = metrics_df

    if not summaries:
        raise ValueError("No comparable result directories were found.")

    combined_summary = pd.concat(summaries, ignore_index=True)
    summary_output = REPORT_SUMMARIES_DIR / "scenario_comparison_summary.csv"
    plot_output = REPORT_FIGURES_DIR / "comparison_plot.png"
    report_output = REPORT_SUMMARIES_DIR / "scenario_comparison_report.md"

    combined_summary.to_csv(summary_output, index=False)
    plot_comparison(metrics_map, plot_output)

    report_lines = ["# Scenario comparison", ""]
    for _, row in combined_summary.iterrows():
        report_lines.append(
            f"- {row['scenario_name']}: final max={row['final_max_distance_km']:.3f} km, "
            f"final centroid={row['final_centroid_distance_km']:.3f} km, "
            f"final hull={row['final_convex_hull_area_km2']:.3f} km^2"
        )
    report_output.write_text("\n".join(report_lines), encoding="utf-8")
    return {
        "comparison_summary_csv": summary_output,
        "comparison_plot_png": plot_output,
        "comparison_report_md": report_output,
    }

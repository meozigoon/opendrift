from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.analysis.plotting import plot_comparison
from src.utils.paths import REPORT_FIGURES_DIR, REPORT_SUMMARIES_DIR


def build_markdown_report(output_dir: Path, summary_df: pd.DataFrame) -> Path:
    row = summary_df.iloc[0]
    report_lines = [
        f"# {row['scenario_name']}",
        "",
        "## 연구 개요",
        "- 목적: OpenDrift PlastDrift를 사용해 유흡착 미세플라스틱의 표층 이동을 예측합니다.",
        "- 모델링 메모: 고분자, 유류, 염분 차이는 직접 화학 반응이 아니라 시나리오 인자 매핑으로 표현합니다.",
        "",
        "## 최종 지표",
        f"- 최종 최대 이동거리 (km): {row['final_max_distance_km']:.3f}",
        f"- 최종 평균 이동거리 (km): {row['final_mean_distance_km']:.3f}",
        f"- 최종 중심점 이동거리 (km): {row['final_centroid_distance_km']:.3f}",
        f"- 최종 볼록 껍질 면적 (km^2): {row['final_convex_hull_area_km2']:.3f}",
        f"- 표층 잔류 비율: {row['final_surface_retention_ratio']:.3f}",
        "",
        "## 스냅샷 지표",
    ]
    for hour in (24, 72, 168):
        key = f"h{hour}"
        if f"{key}_actual_hour" in row:
            report_lines.extend(
                [
                    f"- 요청 시점 {hour}시간 (가장 가까운 저장 시각={row[f'{key}_actual_hour']:.1f}시간): "
                    f"최대 이동거리={row[f'{key}_max_distance_km']:.3f} km, "
                    f"중심점 이동거리={row[f'{key}_centroid_distance_km']:.3f} km, "
                    f"면적={row[f'{key}_convex_hull_area_km2']:.3f} km^2",
                ]
            )
    report_lines.extend(
        [
            "",
            "## 한계",
            "- 이 프로젝트는 표층 전용 기준 실험이며 유류의 풍화 과정은 모사하지 않습니다.",
            "- 데모 모드는 합성 해류 및 바람장을 사용하므로 기능 검증용으로만 해석해야 합니다.",
            "- 실제 해석의 신뢰도는 사용자가 제공한 NetCDF 입력 자료의 품질과 공간, 시간 범위에 크게 좌우됩니다.",
        ]
    )
    path = output_dir / "analysis_report.md"
    path.write_text("\n".join(report_lines), encoding="utf-8")
    return path


def _build_comparison_label(result_dir: Path, scenario_name: str, seen: set[str]) -> str:
    label = scenario_name
    if label in seen:
        label = f"{scenario_name} ({result_dir.name})"
    seen.add(label)
    return label


def build_comparison_report(result_dirs: list[Path]) -> dict[str, Path]:
    REPORT_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    summaries = []
    metrics_map: dict[str, pd.DataFrame] = {}
    used_labels: set[str] = set()
    for result_dir in result_dirs:
        summary_path = result_dir / "summary.csv"
        metrics_path = result_dir / "metrics.csv"
        if summary_path.exists() and metrics_path.exists():
            summary_df = pd.read_csv(summary_path)
            metrics_df = pd.read_csv(metrics_path, parse_dates=["timestamp"])
            summaries.append(summary_df)
            scenario_name = str(summary_df.iloc[0]["scenario_name"])
            metrics_map[_build_comparison_label(result_dir, scenario_name, used_labels)] = metrics_df

    if not summaries:
        raise ValueError("비교 가능한 결과 디렉터리를 찾지 못했습니다.")

    combined_summary = pd.concat(summaries, ignore_index=True)
    summary_output = REPORT_SUMMARIES_DIR / "scenario_comparison_summary.csv"
    plot_output = REPORT_FIGURES_DIR / "comparison_plot.png"
    report_output = REPORT_SUMMARIES_DIR / "scenario_comparison_report.md"

    combined_summary.to_csv(summary_output, index=False)
    plot_comparison(metrics_map, plot_output)

    report_lines = ["# 시나리오 비교", ""]
    for _, row in combined_summary.iterrows():
        report_lines.append(
            f"- {row['scenario_name']}: 최종 최대 이동거리={row['final_max_distance_km']:.3f} km, "
            f"최종 중심점 이동거리={row['final_centroid_distance_km']:.3f} km, "
            f"최종 볼록 껍질 면적={row['final_convex_hull_area_km2']:.3f} km^2"
        )
    report_output.write_text("\n".join(report_lines), encoding="utf-8")
    return {
        "comparison_summary_csv": summary_output,
        "comparison_plot_png": plot_output,
        "comparison_report_md": report_output,
    }

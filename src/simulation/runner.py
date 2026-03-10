from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable

import xarray as xr

from src.analysis.export import export_bundle, export_manifest, export_scenario_copies, export_tables
from src.analysis.metrics import calculate_metrics
from src.analysis.plotting import (
    plot_centroid_distance,
    plot_comparison,
    plot_convex_hull_map,
    plot_dispersion_area,
    plot_trajectory_map,
)
from src.analysis.report_builder import build_markdown_report
from src.analysis.snapshot import build_animation_gif, save_snapshot
from src.simulation.config_loader import ScenarioConfig, scenario_to_dict
from src.simulation.model_factory import create_model
from src.simulation.readers import build_readers, prepare_input_paths
from src.simulation.seed import seed_model
from src.utils.logging_utils import configure_run_logging
from src.utils.paths import OUTPUT_DIR, ensure_project_dirs, make_output_dir, resolve_project_path
from src.utils.validation import validate_scenario_payload


ProgressCallback = Callable[[str, str, float], None]


@dataclass(slots=True)
class RunResult:
    output_dir: Path
    result_path: Path
    log_path: Path
    manifest_path: Path
    bundle_path: Path
    summary_csv: Path
    metrics_csv: Path
    warnings: list[str]
    notes: list[str]


def _notify(callback: ProgressCallback | None, stage: str, message: str, progress: float) -> None:
    if callback is not None:
        callback(stage, message, progress)


def run_scenario(
    scenario: ScenarioConfig,
    raw_payload: dict,
    progress_callback: ProgressCallback | None = None,
    unique_output_dir: bool = True,
) -> RunResult:
    ensure_project_dirs()
    output_root = resolve_project_path(scenario.output_root) or OUTPUT_DIR
    output_dir = make_output_dir(scenario.output_label, output_root=output_root, unique=unique_output_dir)
    log_path = output_dir / "run.log"
    logger, cleanup_logging = configure_run_logging(log_path, scenario.log_level)
    warnings: list[str] = []
    notes: list[str] = []

    try:
        _notify(progress_callback, "validate", "시나리오 입력값을 검증하고 있습니다.", 0.05)
        validation = validate_scenario_payload(raw_payload)
        warnings.extend(validation.warnings)
        notes.extend(validation.info)
        if not validation.ok:
            raise ValueError("\n".join(validation.errors))

        _notify(progress_callback, "inputs", "입력용 NetCDF 자료를 준비하고 있습니다.", 0.15)
        current_path, wind_path, input_notes = prepare_input_paths(scenario, output_dir)
        notes.extend(input_notes)

        _notify(progress_callback, "model", "PlastDrift 모델을 초기화하고 있습니다.", 0.3)
        current_reader, wind_reader = build_readers(current_path, wind_path)
        model = create_model(scenario)
        model.add_reader([current_reader, wind_reader])
        seed_model(model, scenario)
        logger.info("시나리오 초기 입자 %s개를 좌표 (%.4f, %.4f)에 배치했습니다.", scenario.particles, scenario.release_lat, scenario.release_lon)

        _notify(progress_callback, "simulation", "OpenDrift PlastDrift 시뮬레이션을 실행하고 있습니다.", 0.45)
        result_path = output_dir / "result.nc"
        model.run(
            duration=timedelta(hours=scenario.duration_hours),
            time_step=scenario.time_step_minutes * 60,
            time_step_output=scenario.output_time_step_minutes * 60,
            outfile=str(result_path),
            export_variables=scenario.export_variables or None,
        )
        logger.info("시뮬레이션이 완료되었습니다: %s", result_path)

        _notify(progress_callback, "analysis", "지표와 표 형식 산출물을 계산하고 있습니다.", 0.72)
        with xr.open_dataset(result_path) as dataset_file:
            dataset = dataset_file.load()
        metrics_df, summary_df, centroid_df = calculate_metrics(dataset, scenario)
        exported_tables = export_tables(output_dir, summary_df, metrics_df, centroid_df)
        resolved_payload = scenario_to_dict(scenario)
        export_scenario_copies(output_dir, raw_payload, resolved_payload)

        _notify(progress_callback, "plots", "지도, 그래프, 애니메이션을 생성하고 있습니다.", 0.82)
        plot_trajectory_map(dataset, scenario, metrics_df, output_dir / "trajectory_map.png")
        plot_convex_hull_map(dataset, scenario, output_dir / "convex_hull_map.png")
        plot_centroid_distance(metrics_df, output_dir / "centroid_distance_plot.png")
        plot_dispersion_area(metrics_df, scenario.snapshots_hours, output_dir / "dispersion_area_plot.png")
        plot_comparison({scenario.scenario_name: metrics_df}, output_dir / "comparison_plot.png")
        for hour in scenario.snapshots_hours:
            save_snapshot(dataset, scenario, output_dir / f"snapshot_{hour}h.png", hour)
        build_animation_gif(dataset, scenario, output_dir / "animation.gif", frame_stride=scenario.animation_frame_stride)
        build_markdown_report(output_dir, summary_df)
        dataset.close()

        _notify(progress_callback, "bundle", "파일 목록과 ZIP 산출물을 정리하고 있습니다.", 0.94)
        manifest_path = export_manifest(output_dir, warnings, notes)
        bundle_path = export_bundle(output_dir)

        _notify(progress_callback, "done", "시뮬레이션과 후처리가 모두 완료되었습니다.", 1.0)
        return RunResult(
            output_dir=output_dir,
            result_path=result_path,
            log_path=log_path,
            manifest_path=manifest_path,
            bundle_path=bundle_path,
            summary_csv=exported_tables["summary_csv"],
            metrics_csv=exported_tables["metrics_csv"],
            warnings=warnings,
            notes=notes,
        )
    except Exception:
        logger.exception("시나리오 실행에 실패했습니다.")
        raise
    finally:
        cleanup_logging()

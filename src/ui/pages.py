from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pandas as pd
import streamlit as st
import xarray as xr

from src.analysis.report_builder import build_comparison_report
from src.simulation.config_loader import get_parameter_preset, load_defaults, resolve_scenario_payload
from src.simulation.runner import run_scenario
from src.simulation.scenario_manager import list_available_results, list_saved_scenarios, load_saved_scenario, save_scenario_payload
from src.ui.components import (
    render_animation_if_exists,
    render_download_buttons,
    render_image_if_exists,
    render_manifest,
    render_plot_footnote,
    render_pydeck_map,
    render_screen_help,
    render_summary_cards,
    render_validation_result,
)
from src.ui.state import apply_payload_to_state, build_payload_from_state
from src.utils.file_utils import read_json, read_text, save_uploaded_file
from src.utils.paths import UPLOAD_DIR
from src.utils.validation import ValidationResult, validate_scenario_payload


def _preview_validation(payload: dict, current_upload, wind_upload) -> ValidationResult:
    validation = validate_scenario_payload(payload)
    if current_upload is not None:
        validation.errors = [
            message for message in validation.errors if "current NetCDF" not in message and "current NetCDF not found" not in message
        ]
        validation.info.append("Current NetCDF upload is queued and will be staged when the run starts.")
    if wind_upload is not None:
        validation.errors = [
            message for message in validation.errors if "wind NetCDF" not in message and "wind NetCDF not found" not in message
        ]
        validation.info.append("Wind NetCDF upload is queued and will be staged when the run starts.")
    return validation


def _load_result_bundle(result_dir: Path) -> dict:
    summary_df = pd.read_csv(result_dir / "summary.csv") if (result_dir / "summary.csv").exists() else pd.DataFrame()
    metrics_df = pd.read_csv(result_dir / "metrics.csv", parse_dates=["timestamp"]) if (result_dir / "metrics.csv").exists() else pd.DataFrame()
    resolved = read_json(result_dir / "resolved_scenario.json") if (result_dir / "resolved_scenario.json").exists() else {}
    return {"summary": summary_df, "metrics": metrics_df, "resolved": resolved}


def _run_payload_from_ui(defaults: dict, current_upload, wind_upload) -> tuple[dict, dict]:
    payload = build_payload_from_state(defaults)
    payload_for_run = deepcopy(payload)
    if current_upload is not None:
        staged = save_uploaded_file(current_upload, UPLOAD_DIR, f"{payload['output_name']}_current")
        payload_for_run["data_source"]["current_path"] = str(staged)
        payload_for_run["data_source"]["use_demo_data"] = False
    if wind_upload is not None:
        staged = save_uploaded_file(wind_upload, UPLOAD_DIR, f"{payload['output_name']}_wind")
        payload_for_run["data_source"]["wind_path"] = str(staged)
        payload_for_run["data_source"]["use_demo_data"] = False
    return payload, payload_for_run


def render_input_tab() -> None:
    defaults = load_defaults()
    saved_scenarios = list_saved_scenarios()
    scenario_options = {path.name: path for path in saved_scenarios}

    st.subheader("Scenario input")
    render_screen_help(
        "입력 화면 설명",
        "이 화면에서는 플라스틱 종류, 염분, 기름 종류, 방출 위치와 시간, 입자 수, Drift 파라미터, forcing NetCDF를 설정하고 시뮬레이션을 실행할 수 있습니다.",
    )
    top_cols = st.columns([2, 1, 1, 1])
    selected_name = top_cols[0].selectbox("Saved scenario", options=[""] + list(scenario_options.keys()))
    if top_cols[1].button("Load selected") and selected_name:
        apply_payload_to_state(load_saved_scenario(scenario_options[selected_name]))
        st.rerun()
    if top_cols[2].button("Reset defaults"):
        apply_payload_to_state(resolve_scenario_payload({}, defaults)[1])
        st.rerun()
    if top_cols[3].button("Save scenario"):
        path = save_scenario_payload(build_payload_from_state(defaults))
        st.success(f"Saved scenario: {path.name}")

    preset = get_parameter_preset(
        defaults,
        st.session_state["form_polymer_type"],
        int(st.session_state["form_salinity_psu"]),
        st.session_state["form_oil_type"],
    )
    if st.button("Apply recommended preset values"):
        st.session_state["form_terminal_velocity"] = float(preset["terminal_velocity"])
        st.session_state["form_wind_drift_factor"] = float(preset["wind_drift_factor"])
        st.session_state["form_current_drift_factor"] = float(preset["current_drift_factor"])
        st.rerun()
    st.caption(
        "Recommended preset "
        f"(terminal_velocity={preset['terminal_velocity']}, "
        f"wind_drift_factor={preset['wind_drift_factor']}, "
        f"current_drift_factor={preset['current_drift_factor']})"
    )

    left, right = st.columns(2)
    with left:
        st.text_input("Scenario name", key="form_scenario_name")
        st.text_input("Output name", key="form_output_name")
        st.selectbox("Polymer", options=["PE", "PP", "PET"], key="form_polymer_type")
        st.selectbox("Salinity (psu)", options=[33, 40], key="form_salinity_psu")
        st.selectbox("Oil type", options=["diesel", "kerosene"], key="form_oil_type")
        st.number_input("Release latitude", key="form_release_lat", format="%.6f")
        st.number_input("Release longitude", key="form_release_lon", format="%.6f")
        st.text_input("Release time (ISO-8601)", key="form_release_time")
        st.number_input("Duration (hours)", min_value=1, step=1, key="form_duration_hours")
        st.number_input("Particles", min_value=1, step=1, key="form_particles")
        st.number_input("Release radius (m)", min_value=0.0, step=100.0, key="form_radius_m")

    with right:
        st.number_input("Terminal velocity", step=0.0001, format="%.4f", key="form_terminal_velocity")
        st.number_input("Wind drift factor", step=0.001, format="%.4f", key="form_wind_drift_factor")
        st.number_input("Current drift factor", step=0.001, format="%.4f", key="form_current_drift_factor")
        st.number_input("Release depth z", step=0.1, format="%.1f", key="form_z")
        st.checkbox("Use Stokes drift", key="form_stokes_drift")
        st.checkbox("Enable vertical mixing", key="form_vertical_mixing")
        st.checkbox("Enable vertical advection", key="form_vertical_advection")
        st.checkbox("Use synthetic demo data", key="form_use_demo_data")
        st.text_input("Current NetCDF path", key="form_current_path", disabled=st.session_state["form_use_demo_data"])
        st.text_input("Wind NetCDF path", key="form_wind_path", disabled=st.session_state["form_use_demo_data"])
        st.number_input("Target radius (km)", min_value=0.0, step=1.0, key="form_target_radius_km")

    st.map(pd.DataFrame({"lat": [st.session_state["form_release_lat"]], "lon": [st.session_state["form_release_lon"]]}), size=10)
    render_plot_footnote("single map point = current release location preview entered in the form.")

    st.checkbox("Enable interest area bbox", key="form_interest_enabled")
    if st.session_state["form_interest_enabled"]:
        bbox_cols = st.columns(4)
        bbox_cols[0].number_input("min lon", key="form_interest_min_lon", format="%.4f")
        bbox_cols[1].number_input("max lon", key="form_interest_max_lon", format="%.4f")
        bbox_cols[2].number_input("min lat", key="form_interest_min_lat", format="%.4f")
        bbox_cols[3].number_input("max lat", key="form_interest_max_lat", format="%.4f")

    upload_cols = st.columns(2)
    current_upload = upload_cols[0].file_uploader("Upload current NetCDF", type=["nc", "nc4"])
    wind_upload = upload_cols[1].file_uploader("Upload wind NetCDF", type=["nc", "nc4"])

    preview_payload = build_payload_from_state(defaults)
    preview_validation = _preview_validation(preview_payload, current_upload, wind_upload)
    render_validation_result(preview_validation)

    if st.button("Run simulation", type="primary"):
        payload, payload_for_run = _run_payload_from_ui(defaults, current_upload, wind_upload)
        scenario, normalized = resolve_scenario_payload(payload_for_run, defaults)
        status = st.status("Running scenario", expanded=True)
        progress = st.progress(0)

        def callback(stage: str, message: str, fraction: float) -> None:
            status.write(f"[{stage}] {message}")
            progress.progress(int(max(0.0, min(1.0, fraction)) * 100))

        try:
            result = run_scenario(scenario, normalized, progress_callback=callback)
            st.session_state["active_result_dir"] = str(result.output_dir)
            st.session_state["last_run_logs"] = result.logs
            status.update(label="Run completed", state="complete")
            st.success(f"Completed: {result.output_dir.name}")
            st.rerun()
        except Exception as exc:
            status.update(label="Run failed", state="error")
            st.error(str(exc))


def _render_result_selector() -> Path | None:
    result_dirs = list_available_results()
    if not result_dirs:
        st.info("No completed results are available yet.")
        return None
    default_index = 0
    active = st.session_state.get("active_result_dir")
    if active:
        for index, path in enumerate(result_dirs):
            if str(path) == active:
                default_index = index
                break
    selected = st.selectbox("Result set", options=result_dirs, index=default_index, format_func=lambda path: path.name)
    st.session_state["active_result_dir"] = str(selected)
    return selected


def render_results_tabs() -> None:
    selected = _render_result_selector()
    if selected is None:
        return
    bundle = _load_result_bundle(selected)
    summary_df = bundle["summary"]
    metrics_df = bundle["metrics"]
    resolved = bundle["resolved"]
    if resolved.get("use_demo_data"):
        st.warning("This result was generated in synthetic demo mode.")

    basic_tab, animation_tab, analysis_tab, download_tab, log_tab = st.tabs(
        ["Basic result", "Animation", "Analysis", "Download", "Log"]
    )

    with basic_tab:
        render_screen_help(
            "기본 결과 화면 설명",
            "선택한 시점의 입자 분포, 주요 핵심 지표, 궤적 지도, convex hull 지도, 시점별 스냅샷을 확인하는 화면입니다.",
        )
        render_summary_cards(summary_df)
        if (selected / "result.nc").exists():
            with xr.open_dataset(selected / "result.nc") as dataset:
                time_index = st.slider("Timestep index", min_value=0, max_value=int(dataset.sizes["time"]) - 1, value=int(dataset.sizes["time"]) - 1)
                render_pydeck_map(dataset, time_index)
        image_cols = st.columns(2)
        with image_cols[0]:
            render_image_if_exists(selected / "trajectory_map.png", "Trajectory map")
            render_plot_footnote(
                "trajectory map에서 파란 얇은 선은 개별 입자 궤적, 주황 점은 최종 입자 위치, 빨간 별은 방출점, 초록 선은 centroid 이동 경로, 보라 선은 최종 convex hull입니다."
            )
            render_image_if_exists(selected / "convex_hull_map.png", "Convex hull map")
            render_plot_footnote(
                "convex hull map에서 파란 점은 최종 시점 입자 위치, 빨간 선은 외곽 경계, 초록 별은 원래 방출점입니다."
            )
        with image_cols[1]:
            render_image_if_exists(selected / "snapshot_24h.png", "Snapshot 24h")
            render_plot_footnote("snapshot 이미지에서 파란 점은 해당 시점 입자 위치, 빨간 별은 방출점, 보라 선은 그 시점의 외곽 범위입니다.")
            render_image_if_exists(selected / "snapshot_72h.png", "Snapshot 72h")
            render_plot_footnote("snapshot 이미지의 범례 의미는 동일합니다.")
            render_image_if_exists(selected / "snapshot_168h.png", "Snapshot 168h")
            render_plot_footnote("snapshot 이미지의 범례 의미는 동일합니다.")

    with animation_tab:
        render_screen_help(
            "애니메이션 화면 설명",
            "시뮬레이션 시간에 따라 미세플라스틱 입자군이 어떻게 이동하는지 GIF 애니메이션으로 계속 반복 재생해서 보여주는 화면입니다.",
        )
        render_animation_if_exists(selected / "animation.gif", "Particle animation (looping GIF)")
        render_plot_footnote(
            "애니메이션 프레임에서 파란 점은 각 시점의 입자 위치, 빨간 별은 초기 방출점입니다. GIF는 반복(loop) 재생됩니다."
        )
        if (selected / "animation.gif").exists():
            st.download_button(
                label="Download animation.gif",
                data=(selected / "animation.gif").read_bytes(),
                file_name="animation.gif",
                mime="image/gif",
                key=f"download_animation_preview_{selected.name}",
            )

    with analysis_tab:
        render_screen_help(
            "분석 화면 설명",
            "시간에 따른 이동거리, centroid 이동, 확산 면적, 시나리오 비교 표와 그래프를 확인하는 화면입니다.",
        )
        if not metrics_df.empty:
            st.line_chart(metrics_df.set_index("hours_since_release")[["max_distance_km", "centroid_distance_km", "mean_distance_km"]])
            render_plot_footnote(
                "max_distance_km = farthest particle from release point, "
                "centroid_distance_km = distance from release point to particle-cluster center, "
                "mean_distance_km = average particle distance from release point."
            )
            st.line_chart(metrics_df.set_index("hours_since_release")[["convex_hull_area_km2", "dispersion_radius_km", "p95_radius_km"]])
            render_plot_footnote(
                "convex_hull_area_km2 = outer spread area, "
                "dispersion_radius_km = mean distance-based spread radius, "
                "p95_radius_km = 95th percentile distance from release point."
            )
            st.dataframe(summary_df, width="stretch")
            st.dataframe(metrics_df, width="stretch", height=300)
        plot_cols = st.columns(2)
        with plot_cols[0]:
            render_image_if_exists(selected / "centroid_distance_plot.png", "Distance plot")
            render_plot_footnote(
                "distance plot 선: centroid distance, max distance, mean distance의 시간 변화입니다."
            )
            render_image_if_exists(selected / "dispersion_area_plot.png", "Dispersion area plot")
            render_plot_footnote(
                "dispersion area 막대: 요청된 snapshot 시점에서의 convex hull 면적입니다."
            )
        with plot_cols[1]:
            render_image_if_exists(selected / "comparison_plot.png", "Scenario comparison plot")
            render_plot_footnote(
                "comparison plot: 위 패널은 시나리오별 최대 이동거리, 아래 패널은 시나리오별 convex hull 면적 비교입니다."
            )
            if (selected / "analysis_report.md").exists():
                st.markdown((selected / "analysis_report.md").read_text(encoding="utf-8"))

        compare_candidates = list_available_results()
        compare_selection = st.multiselect("Compare scenarios", options=compare_candidates, format_func=lambda path: path.name, default=[selected])
        if st.button("Build comparison report"):
            try:
                artifacts = build_comparison_report(compare_selection)
                st.session_state["comparison_artifacts"] = {key: str(value) for key, value in artifacts.items()}
                st.success("Comparison report updated.")
            except Exception as exc:
                st.error(str(exc))
        artifacts = st.session_state.get("comparison_artifacts", {})
        if artifacts:
            comparison_plot = Path(artifacts["comparison_plot_png"])
            comparison_summary = Path(artifacts["comparison_summary_csv"])
            render_image_if_exists(comparison_plot, "Cross-scenario comparison")
            render_plot_footnote(
                "각 색 선은 하나의 선택된 시나리오를 의미합니다. 위 패널은 최대 이동거리, 아래 패널은 convex hull 면적입니다."
            )
            if comparison_summary.exists():
                st.dataframe(pd.read_csv(comparison_summary), width="stretch")

    with download_tab:
        render_screen_help(
            "다운로드 화면 설명",
            "이 화면에서는 NetCDF, CSV, PNG, GIF, ZIP 등 생성된 산출물을 개별 또는 묶음 파일로 내려받을 수 있습니다.",
        )
        render_download_buttons(selected)
        file_table = [{"path": str(path.relative_to(selected)), "size_bytes": path.stat().st_size} for path in sorted(selected.rglob("*")) if path.is_file()]
        st.dataframe(pd.DataFrame(file_table), width="stretch")
        render_plot_footnote("파일 표는 현재 선택한 결과 폴더에 들어 있는 실제 산출물 목록과 파일 크기를 보여줍니다.")

    with log_tab:
        render_screen_help(
            "로그 화면 설명",
            "실행 로그, 경고, 생성 파일 manifest를 확인하여 입력 검증 결과와 실행 과정을 추적하는 화면입니다.",
        )
        render_manifest(selected)
        st.text_area("Run log", value=read_text(selected / "run.log"), height=300)
        render_plot_footnote("manifest는 결과 폴더의 파일 목록과 경고/메모를 요약하며, run log는 실제 실행 중 기록된 메시지입니다.")


def render_app() -> None:
    st.title("OpenDrift PlastDrift Surface Research Web App")
    st.caption("Surface-only prediction and analysis for oil-adsorbed microplastic transport scenarios.")
    top_tab, result_tab = st.tabs(["Scenario / Run", "Results"])
    with top_tab:
        render_input_tab()
    with result_tab:
        render_results_tabs()

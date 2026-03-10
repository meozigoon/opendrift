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
    render_localized_dataframe,
    render_manifest,
    render_plot_footnote,
    render_pydeck_map,
    render_screen_help,
    render_summary_cards,
    render_validation_result,
)
from src.ui.state import apply_payload_to_state, build_payload_from_state
from src.ui.texts import FIELD_HELP, format_oil, format_polymer, localize_column_name
from src.utils.file_utils import read_json, read_text, save_uploaded_file
from src.utils.paths import UPLOAD_DIR
from src.utils.validation import ValidationResult, validate_scenario_payload


POLYMER_OPTIONS = ["PE", "PP", "PET"]
OIL_OPTIONS = ["diesel", "kerosene"]
STAGE_LABELS = {
    "validate": "입력 검증",
    "inputs": "입력 데이터 준비",
    "model": "모델 초기화",
    "simulation": "시뮬레이션 실행",
    "analysis": "지표 계산",
    "plots": "시각화 생성",
    "bundle": "산출물 정리",
    "done": "완료",
}
UPLOAD_INFO_RULES = (
    ("해류 NetCDF", "해류 NetCDF 업로드 파일이 대기 중입니다. 실행을 시작하면 임시 저장 후 사용합니다."),
    ("바람 NetCDF", "바람 NetCDF 업로드 파일이 대기 중입니다. 실행을 시작하면 임시 저장 후 사용합니다."),
)


def _preview_validation(payload: dict, current_upload, wind_upload) -> ValidationResult:
    validation = validate_scenario_payload(payload)
    for upload, (kind_label, message) in zip((current_upload, wind_upload), UPLOAD_INFO_RULES, strict=False):
        if upload is None:
            continue
        validation.errors = [
            item
            for item in validation.errors
            if not (kind_label in item and ("필요합니다" in item or "찾을 수 없습니다" in item))
        ]
        validation.info.append(message)
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


def _localized_chart(metrics_df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    chart = metrics_df.set_index("hours_since_release")[columns].copy()
    chart.columns = [localize_column_name(column) for column in chart.columns]
    return chart


def render_input_tab() -> None:
    defaults = load_defaults()
    saved_scenarios = list_saved_scenarios()
    scenario_options = {path.name: path for path in saved_scenarios}

    st.subheader("시나리오 입력")
    render_screen_help(
        "입력 화면 설명",
        "이 화면에서는 플라스틱 종류, 염분, 기름 종류, 방출 위치와 시간, 입자 수, 이동 인자, 입력 NetCDF를 설정하고 시뮬레이션을 실행할 수 있습니다.",
    )
    top_cols = st.columns([2, 1, 1, 1])
    selected_name = top_cols[0].selectbox(
        "저장된 시나리오",
        options=[""] + list(scenario_options.keys()),
        help=FIELD_HELP["saved_scenario"],
    )
    if top_cols[1].button("선택 항목 불러오기", help="선택한 시나리오 설정으로 현재 입력값을 바꿉니다."):
        if selected_name:
            apply_payload_to_state(load_saved_scenario(scenario_options[selected_name]))
            st.rerun()
    if top_cols[2].button("기본값으로 초기화", help="기본 시나리오 설정으로 되돌립니다."):
        apply_payload_to_state(resolve_scenario_payload({}, defaults)[1])
        st.rerun()
    if top_cols[3].button("시나리오 저장", help="현재 폼 입력값을 시나리오 파일로 저장합니다."):
        path = save_scenario_payload(build_payload_from_state(defaults))
        st.success(f"시나리오를 저장했습니다: {path.name}")

    preset = get_parameter_preset(
        defaults,
        st.session_state["form_polymer_type"],
        int(st.session_state["form_salinity_psu"]),
        st.session_state["form_oil_type"],
    )
    if st.button("추천 프리셋 적용", help="현재 고분자, 염분, 유류 조합에 맞는 추천 이동 인자를 자동 입력합니다."):
        st.session_state["form_terminal_velocity"] = float(preset["terminal_velocity"])
        st.session_state["form_wind_drift_factor"] = float(preset["wind_drift_factor"])
        st.session_state["form_current_drift_factor"] = float(preset["current_drift_factor"])
        st.rerun()
    st.caption(
        "현재 조합의 추천값: "
        f"종말 속도={preset['terminal_velocity']}, "
        f"풍하중 계수={preset['wind_drift_factor']}, "
        f"해류 이동 계수={preset['current_drift_factor']}"
    )

    left, right = st.columns(2)
    with left:
        st.text_input("시나리오 이름", key="form_scenario_name", help=FIELD_HELP["scenario_name"])
        st.text_input("출력 이름", key="form_output_name", help=FIELD_HELP["output_name"])
        st.selectbox("고분자 종류", options=POLYMER_OPTIONS, key="form_polymer_type", format_func=format_polymer, help=FIELD_HELP["polymer_type"])
        st.selectbox("염분 조건 (PSU)", options=[33, 40], key="form_salinity_psu", help=FIELD_HELP["salinity_psu"])
        st.selectbox("유류 종류", options=OIL_OPTIONS, key="form_oil_type", format_func=format_oil, help=FIELD_HELP["oil_type"])
        st.number_input("방출 위도", key="form_release_lat", format="%.6f", help=FIELD_HELP["release_lat"])
        st.number_input("방출 경도", key="form_release_lon", format="%.6f", help=FIELD_HELP["release_lon"])
        st.text_input("방출 시각 (ISO-8601)", key="form_release_time", help=FIELD_HELP["release_time"])
        st.number_input("지속 시간 (시간)", min_value=1, step=1, key="form_duration_hours", help=FIELD_HELP["duration_hours"])
        st.number_input("입자 수", min_value=1, step=1, key="form_particles", help=FIELD_HELP["particles"])
        st.number_input("방출 반경 (m)", min_value=0.0, step=100.0, key="form_radius_m", help=FIELD_HELP["radius_m"])

    with right:
        st.number_input("종말 속도", step=0.0001, format="%.4f", key="form_terminal_velocity", help=FIELD_HELP["terminal_velocity"])
        st.number_input("풍하중 계수", step=0.001, format="%.4f", key="form_wind_drift_factor", help=FIELD_HELP["wind_drift_factor"])
        st.number_input("해류 이동 계수", step=0.001, format="%.4f", key="form_current_drift_factor", help=FIELD_HELP["current_drift_factor"])
        st.number_input("방출 깊이 z", step=0.1, format="%.1f", key="form_z", help=FIELD_HELP["z"])
        st.checkbox("스토크스 표류 사용", key="form_stokes_drift", help=FIELD_HELP["stokes_drift"])
        st.checkbox("수직 혼합 사용", key="form_vertical_mixing", help=FIELD_HELP["vertical_mixing"])
        st.checkbox("수직 이류 사용", key="form_vertical_advection", help=FIELD_HELP["vertical_advection"])
        st.checkbox("합성 데모 데이터 사용", key="form_use_demo_data", help=FIELD_HELP["use_demo_data"])
        st.text_input("해류 NetCDF 경로", key="form_current_path", disabled=st.session_state["form_use_demo_data"], help=FIELD_HELP["current_path"])
        st.text_input("바람 NetCDF 경로", key="form_wind_path", disabled=st.session_state["form_use_demo_data"], help=FIELD_HELP["wind_path"])
        st.number_input("목표 반경 (km)", min_value=0.0, step=1.0, key="form_target_radius_km", help=FIELD_HELP["target_radius_km"])

    st.map(pd.DataFrame({"lat": [st.session_state["form_release_lat"]], "lon": [st.session_state["form_release_lon"]]}), size=10)
    render_plot_footnote("지도에 보이는 단일 점은 현재 폼에 입력된 방출 위치 미리보기입니다.")

    st.checkbox("관심 영역 경계상자 사용", key="form_interest_enabled", help=FIELD_HELP["interest_enabled"])
    if st.session_state["form_interest_enabled"]:
        bbox_cols = st.columns(4)
        bbox_cols[0].number_input("최소 경도", key="form_interest_min_lon", format="%.4f", help=FIELD_HELP["interest_min_lon"])
        bbox_cols[1].number_input("최대 경도", key="form_interest_max_lon", format="%.4f", help=FIELD_HELP["interest_max_lon"])
        bbox_cols[2].number_input("최소 위도", key="form_interest_min_lat", format="%.4f", help=FIELD_HELP["interest_min_lat"])
        bbox_cols[3].number_input("최대 위도", key="form_interest_max_lat", format="%.4f", help=FIELD_HELP["interest_max_lat"])

    upload_cols = st.columns(2)
    current_upload = upload_cols[0].file_uploader("해류 NetCDF 업로드", type=["nc", "nc4"], help=FIELD_HELP["current_upload"])
    wind_upload = upload_cols[1].file_uploader("바람 NetCDF 업로드", type=["nc", "nc4"], help=FIELD_HELP["wind_upload"])

    preview_payload = build_payload_from_state(defaults)
    preview_validation = _preview_validation(preview_payload, current_upload, wind_upload)
    render_validation_result(preview_validation)

    if st.button("시뮬레이션 실행", type="primary", help="현재 입력값으로 OpenDrift PlastDrift 시뮬레이션을 실행합니다."):
        payload, payload_for_run = _run_payload_from_ui(defaults, current_upload, wind_upload)
        scenario, normalized = resolve_scenario_payload(payload_for_run, defaults)
        status = st.status("시나리오를 실행하는 중입니다.", expanded=True)
        progress = st.progress(0)

        def callback(stage: str, message: str, fraction: float) -> None:
            status.write(f"[{STAGE_LABELS.get(stage, stage)}] {message}")
            progress.progress(int(max(0.0, min(1.0, fraction)) * 100))

        try:
            result = run_scenario(scenario, normalized, progress_callback=callback)
            st.session_state["active_result_dir"] = str(result.output_dir)
            status.update(label="실행이 완료되었습니다.", state="complete")
            st.success(f"실행 완료: {result.output_dir.name}")
            st.rerun()
        except Exception as exc:
            status.update(label="실행에 실패했습니다.", state="error")
            st.error(str(exc))


def _render_result_selector() -> Path | None:
    result_dirs = list_available_results()
    if not result_dirs:
        st.info("아직 완료된 결과가 없습니다.")
        return None
    default_index = 0
    active = st.session_state.get("active_result_dir")
    if active:
        for index, path in enumerate(result_dirs):
            if str(path) == active:
                default_index = index
                break
    selected = st.selectbox(
        "결과 세트",
        options=result_dirs,
        index=default_index,
        format_func=lambda path: path.name,
        help=FIELD_HELP["result_set"],
    )
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
        st.warning("이 결과는 합성 데모 모드에서 생성되었습니다.")

    basic_tab, animation_tab, analysis_tab, download_tab, log_tab = st.tabs(
        ["기본 결과", "애니메이션", "분석", "다운로드", "로그"]
    )

    with basic_tab:
        render_screen_help(
            "기본 결과 화면 설명",
            "선택한 시점의 입자 분포, 주요 핵심 지표, 궤적 지도, 볼록 껍질 지도, 시점별 스냅샷을 확인하는 화면입니다.",
        )
        render_summary_cards(summary_df)
        if (selected / "result.nc").exists():
            with xr.open_dataset(selected / "result.nc") as dataset:
                time_index = st.slider(
                    "시점 인덱스",
                    min_value=0,
                    max_value=int(dataset.sizes["time"]) - 1,
                    value=int(dataset.sizes["time"]) - 1,
                    help=FIELD_HELP["time_index"],
                )
                render_pydeck_map(dataset, time_index)
        image_cols = st.columns(2)
        with image_cols[0]:
            render_image_if_exists(selected / "trajectory_map.png", "입자 궤적 지도")
            render_plot_footnote(
                "입자 궤적 지도에서 파란 얇은 선은 개별 입자 궤적, 주황 점은 최종 입자 위치, 빨간 별은 방출점, 초록 선은 중심점 이동 경로, 보라 선은 최종 볼록 껍질입니다."
            )
            render_image_if_exists(selected / "convex_hull_map.png", "최종 볼록 껍질 지도")
            render_plot_footnote(
                "볼록 껍질 지도에서 파란 점은 최종 시점 입자 위치, 빨간 선은 외곽 경계, 초록 별은 원래 방출점입니다."
            )
        with image_cols[1]:
            render_image_if_exists(selected / "snapshot_24h.png", "24시간 스냅샷")
            render_plot_footnote("스냅샷 이미지에서 파란 점은 해당 시점 입자 위치, 빨간 별은 방출점, 보라 선은 그 시점의 외곽 범위입니다.")
            render_image_if_exists(selected / "snapshot_72h.png", "72시간 스냅샷")
            render_plot_footnote("스냅샷 이미지의 범례 의미는 동일합니다.")
            render_image_if_exists(selected / "snapshot_168h.png", "168시간 스냅샷")
            render_plot_footnote("스냅샷 이미지의 범례 의미는 동일합니다.")

    with animation_tab:
        render_screen_help(
            "애니메이션 화면 설명",
            "시뮬레이션 시간에 따라 미세플라스틱 입자군이 어떻게 이동하는지 GIF 애니메이션으로 반복 재생해 보여주는 화면입니다.",
        )
        render_animation_if_exists(selected / "animation.gif", "입자 이동 애니메이션 (반복 GIF)")
        render_plot_footnote(
            "애니메이션 프레임에서 파란 점은 각 시점의 입자 위치, 빨간 별은 초기 방출점입니다. GIF는 반복 재생됩니다."
        )
        if (selected / "animation.gif").exists():
            st.download_button(
                label="animation.gif 다운로드",
                data=(selected / "animation.gif").read_bytes(),
                file_name="animation.gif",
                mime="image/gif",
                key=f"download_animation_preview_{selected.name}",
            )

    with analysis_tab:
        render_screen_help(
            "분석 화면 설명",
            "시간에 따른 이동거리, 중심점 이동, 확산 면적, 시나리오 비교 표와 그래프를 확인하는 화면입니다.",
        )
        if not metrics_df.empty:
            st.line_chart(_localized_chart(metrics_df, ["max_distance_km", "centroid_distance_km", "mean_distance_km"]))
            render_plot_footnote(
                "최대 이동거리 = 방출점에서 가장 멀리 이동한 입자 거리, 중심점 이동거리 = 방출점에서 입자군 중심까지의 거리, 평균 이동거리 = 방출점 기준 전체 입자의 평균 거리입니다."
            )
            st.line_chart(_localized_chart(metrics_df, ["convex_hull_area_km2", "dispersion_radius_km", "p95_radius_km"]))
            render_plot_footnote(
                "볼록 껍질 면적 = 입자군 외곽 확산 면적, 확산 반경 = 평균 거리 기반 확산 반경, 95퍼센타일 반경 = 방출점 기준 상위 95퍼센트 거리입니다."
            )
            render_localized_dataframe(summary_df, width="stretch")
            render_localized_dataframe(metrics_df, width="stretch", height=300)
        plot_cols = st.columns(2)
        with plot_cols[0]:
            render_image_if_exists(selected / "centroid_distance_plot.png", "거리 지표 그래프")
            render_plot_footnote("거리 지표 그래프의 선은 중심점 이동거리, 최대 이동거리, 평균 이동거리의 시간 변화를 나타냅니다.")
            render_image_if_exists(selected / "dispersion_area_plot.png", "확산 면적 그래프")
            render_plot_footnote("확산 면적 그래프의 막대는 요청한 스냅샷 시점에서의 볼록 껍질 면적입니다.")
        with plot_cols[1]:
            render_image_if_exists(selected / "comparison_plot.png", "시나리오 비교 그래프")
            render_plot_footnote(
                "비교 그래프는 위 패널에서 시나리오별 최대 이동거리, 아래 패널에서 시나리오별 볼록 껍질 면적을 비교합니다."
            )
            if (selected / "analysis_report.md").exists():
                st.markdown((selected / "analysis_report.md").read_text(encoding="utf-8"))

        compare_candidates = list_available_results()
        compare_selection = st.multiselect(
            "비교할 시나리오 선택",
            options=compare_candidates,
            format_func=lambda path: path.name,
            default=[selected],
            help=FIELD_HELP["compare_scenarios"],
        )
        if st.button("비교 보고서 생성", help="선택한 결과들을 기준으로 비교 그래프와 요약표를 다시 생성합니다."):
            try:
                artifacts = build_comparison_report(compare_selection)
                st.session_state["comparison_artifacts"] = {key: str(value) for key, value in artifacts.items()}
                st.success("비교 보고서를 업데이트했습니다.")
            except Exception as exc:
                st.error(str(exc))
        artifacts = st.session_state.get("comparison_artifacts", {})
        if artifacts:
            comparison_plot = Path(artifacts["comparison_plot_png"])
            comparison_summary = Path(artifacts["comparison_summary_csv"])
            render_image_if_exists(comparison_plot, "교차 시나리오 비교 그래프")
            render_plot_footnote(
                "각 색 선은 선택한 하나의 시나리오를 의미합니다. 위 패널은 최대 이동거리, 아래 패널은 볼록 껍질 면적의 시간 변화를 나타냅니다."
            )
            if comparison_summary.exists():
                render_localized_dataframe(pd.read_csv(comparison_summary), width="stretch")

    with download_tab:
        render_screen_help(
            "다운로드 화면 설명",
            "이 화면에서는 NetCDF, CSV, PNG, GIF, ZIP 등 생성된 산출물을 개별 또는 묶음 파일로 내려받을 수 있습니다.",
        )
        render_download_buttons(selected)
        file_table = [{"path": str(path.relative_to(selected)), "size_bytes": path.stat().st_size} for path in sorted(selected.rglob("*")) if path.is_file()]
        render_localized_dataframe(pd.DataFrame(file_table), width="stretch")
        render_plot_footnote("파일 표는 현재 선택한 결과 폴더에 들어 있는 실제 산출물 목록과 파일 크기를 보여줍니다.")

    with log_tab:
        render_screen_help(
            "로그 화면 설명",
            "실행 로그, 경고, 생성 파일 목록을 확인하여 입력 검증 결과와 실행 과정을 추적하는 화면입니다.",
        )
        render_manifest(selected)
        st.text_area("실행 로그", value=read_text(selected / "run.log"), height=300)
        render_plot_footnote("파일 목록 JSON은 결과 폴더의 파일 목록과 경고, 메모를 요약하며 실행 로그는 실제 수행 중 기록된 메시지입니다.")


def render_app() -> None:
    st.title("OpenDrift PlastDrift 표층 연구 웹 앱")
    st.caption("유흡착 미세플라스틱의 표층 이동 시나리오를 설정하고 결과를 분석하는 한글 웹 인터페이스입니다.")
    top_tab, result_tab = st.tabs(["시나리오 설정 / 실행", "결과 확인"])
    with top_tab:
        render_input_tab()
    with result_tab:
        render_results_tabs()

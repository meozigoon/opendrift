from __future__ import annotations

from typing import Any
import re

import pandas as pd


POLYMER_LABELS = {
    "PE": "폴리에틸렌 (PE)",
    "PP": "폴리프로필렌 (PP)",
    "PET": "폴리에틸렌 테레프탈레이트 (PET)",
}

OIL_LABELS = {
    "diesel": "디젤",
    "kerosene": "등유",
}

BOOLEAN_LABELS = {
    True: "예",
    False: "아니오",
}

FIELD_HELP = {
    "saved_scenario": "저장해 둔 시나리오 설정을 다시 불러옵니다. 선택 후 불러오기를 누르면 현재 입력값을 해당 설정으로 덮어씁니다.",
    "scenario_name": "시나리오를 식별하는 이름입니다. 결과 보고서 제목과 내부 비교 표에 사용됩니다.",
    "output_name": "실행 결과 폴더명과 산출물 묶음 이름의 기준이 됩니다. 같은 이름을 반복 실행하면 고유한 폴더가 자동 생성됩니다.",
    "polymer_type": "미세플라스틱의 고분자 종류입니다. 추천 이동 인자와 결과 해석 문맥에 함께 반영됩니다.",
    "salinity_psu": "해수 염분 조건입니다. PSU 값을 바꾸면 추천 종말 속도와 이동 계수가 달라질 수 있습니다.",
    "oil_type": "입자 표면에 흡착된 유류 종류입니다. 고분자와 염분 조합과 함께 추천 인자 선택에 사용됩니다.",
    "release_lat": "입자를 방출할 시작 위도입니다. 지도 미리보기와 실제 시뮬레이션의 초기 위치에 그대로 반영됩니다.",
    "release_lon": "입자를 방출할 시작 경도입니다. 지도 미리보기와 실제 시뮬레이션의 초기 위치에 그대로 반영됩니다.",
    "release_time": "방출을 시작할 시각입니다. ISO-8601 형식 예시는 2024-01-01T00:00:00 입니다.",
    "duration_hours": "시뮬레이션을 몇 시간 동안 진행할지 지정합니다. 값이 길수록 계산 시간과 산출물 크기가 늘어납니다.",
    "particles": "추적할 입자 개수입니다. 많을수록 분포 표현은 좋아지지만 계산 시간과 메모리 사용량이 증가합니다.",
    "radius_m": "초기 방출 위치를 중심으로 입자를 퍼뜨릴 반경입니다. 0이면 한 점에서 방출됩니다.",
    "terminal_velocity": "입자의 상하 방향 종말 속도입니다. 음수면 가라앉는 경향, 양수면 상승 경향을 의미합니다.",
    "wind_drift_factor": "풍속이 입자 수평 이동에 얼마나 반영되는지를 나타내는 비율 계수입니다.",
    "current_drift_factor": "해류 속도를 입자 이동에 적용하는 비율입니다. 기본적으로 1.0이면 해류장을 그대로 따릅니다.",
    "z": "초기 방출 깊이입니다. 표층 기준 깊이 좌표로 사용되며 보통 0에 가까울수록 표면 방출을 의미합니다.",
    "stokes_drift": "파랑에 의한 스토크스 표류를 추가할지 결정합니다. 기준 연구 설계와 다른 조건을 시험할 때 사용합니다.",
    "vertical_mixing": "수직 혼합을 활성화할지 결정합니다. 표층 기준 시뮬레이션보다 더 복잡한 수직 거동이 들어갑니다.",
    "vertical_advection": "수직 이류 계산을 포함할지 결정합니다. 표층 중심 실험에서는 보통 꺼 둡니다.",
    "use_demo_data": "실제 NetCDF 대신 합성 데모 해류/바람장을 사용할지 결정합니다. 기능 검증용이며 실제 해양 해석에는 적합하지 않습니다.",
    "current_path": "사용자 해류 NetCDF 파일 경로입니다. 실제 실행 시 동서/남북 해류 성분과 시간, 위도, 경도 좌표가 필요합니다.",
    "wind_path": "사용자 바람 NetCDF 파일 경로입니다. 실제 실행 시 x_wind, y_wind 성분과 시간, 위도, 경도 좌표가 필요합니다.",
    "target_radius_km": "방출점에서 몇 km 이상 벗어났는지를 평가할 기준 반경입니다. 요약 지표의 목표 반경 도달 비율 계산에 사용됩니다.",
    "interest_enabled": "관심 영역 경계상자를 사용하면 지정한 영역 안에 남아 있는 입자 비율을 함께 계산합니다.",
    "interest_min_lon": "관심 영역의 최소 경도입니다. 최대 경도보다 작아야 하며 경계상자의 서쪽 경계를 정의합니다.",
    "interest_max_lon": "관심 영역의 최대 경도입니다. 최소 경도보다 커야 하며 경계상자의 동쪽 경계를 정의합니다.",
    "interest_min_lat": "관심 영역의 최소 위도입니다. 최대 위도보다 작아야 하며 경계상자의 남쪽 경계를 정의합니다.",
    "interest_max_lat": "관심 영역의 최대 위도입니다. 최소 위도보다 커야 하며 경계상자의 북쪽 경계를 정의합니다.",
    "current_upload": "해류 NetCDF 파일을 직접 업로드합니다. 실행 버튼을 누르면 임시 저장 후 입력 자료로 사용됩니다.",
    "wind_upload": "바람 NetCDF 파일을 직접 업로드합니다. 실행 버튼을 누르면 임시 저장 후 입력 자료로 사용됩니다.",
    "result_set": "조회할 완료 결과 폴더를 선택합니다. 선택한 결과에 맞춰 아래 탭의 그래프와 산출물이 바뀝니다.",
    "time_index": "결과 NetCDF에서 확인할 저장 시점의 인덱스입니다. 마지막 값일수록 방출 후 더 늦은 시점입니다.",
    "compare_scenarios": "비교 보고서에 포함할 결과를 여러 개 선택합니다. 선택한 시나리오만 비교 그래프와 요약표에 반영됩니다.",
}

COLUMN_LABELS = {
    "scenario_name": "시나리오 이름",
    "output_name": "출력 이름",
    "polymer_type": "고분자 종류",
    "salinity_psu": "염분 (PSU)",
    "oil_type": "유류 종류",
    "parameter_source": "인자 출처",
    "temperature_c": "수온 (°C)",
    "use_demo_data": "데모 데이터 사용",
    "release_time": "방출 시각",
    "duration_hours": "지속 시간 (시간)",
    "particles": "입자 수",
    "release_lat": "방출 위도",
    "release_lon": "방출 경도",
    "release_radius_m": "방출 반경 (m)",
    "terminal_velocity": "종말 속도",
    "wind_drift_factor": "풍하중 계수",
    "current_drift_factor": "해류 이동 계수",
    "target_radius_km": "목표 반경 (km)",
    "interest_area_bbox": "관심 영역 경계상자",
    "final_max_distance_km": "최종 최대 이동거리 (km)",
    "final_mean_distance_km": "최종 평균 이동거리 (km)",
    "final_centroid_distance_km": "최종 중심점 이동거리 (km)",
    "final_convex_hull_area_km2": "최종 볼록 껍질 면적 (km²)",
    "final_surface_retention_ratio": "최종 표층 잔류 비율",
    "final_reached_target_radius_ratio": "최종 목표 반경 도달 비율",
    "timestamp": "시각",
    "hours_since_release": "방출 후 경과 시간 (시간)",
    "particle_count": "유효 입자 수",
    "max_distance_km": "최대 이동거리 (km)",
    "mean_distance_km": "평균 이동거리 (km)",
    "centroid_lon": "중심점 경도",
    "centroid_lat": "중심점 위도",
    "centroid_distance_km": "중심점 이동거리 (km)",
    "convex_hull_area_km2": "볼록 껍질 면적 (km²)",
    "dispersion_radius_km": "확산 반경 (km)",
    "p95_radius_km": "95퍼센타일 반경 (km)",
    "reached_target_radius_ratio": "목표 반경 도달 비율",
    "interest_area_ratio": "관심 영역 내 비율",
    "surface_retention_ratio": "표층 잔류 비율",
    "path": "파일 경로",
    "size_bytes": "크기 (바이트)",
}

SNAPSHOT_COLUMN_SUFFIXES = {
    "actual_hour": "실제 저장 시각 (시간)",
    "max_distance_km": "최대 이동거리 (km)",
    "mean_distance_km": "평균 이동거리 (km)",
    "centroid_distance_km": "중심점 이동거리 (km)",
    "convex_hull_area_km2": "볼록 껍질 면적 (km²)",
    "reached_target_radius_ratio": "목표 반경 도달 비율",
}

MANIFEST_KEY_LABELS = {
    "warnings": "경고",
    "notes": "메모",
    "files": "파일 목록",
    "path": "경로",
    "size_bytes": "크기 (바이트)",
}


def format_polymer(value: Any) -> str:
    return POLYMER_LABELS.get(str(value), str(value))


def format_oil(value: Any) -> str:
    return OIL_LABELS.get(str(value), str(value))


def format_parameter_source(value: Any) -> str:
    if not isinstance(value, str):
        return str(value)
    if value == "user_override":
        return "사용자 지정"
    if value.startswith("preset:"):
        preset = value.split(":", 1)[1]
        parts = preset.split("/")
        if len(parts) == 3:
            polymer, salinity, oil = parts
            return f"추천 프리셋 ({format_polymer(polymer)}, {salinity} PSU, {format_oil(oil)})"
        return f"추천 프리셋 ({preset})"
    return value


def localize_column_name(column: str) -> str:
    if column in COLUMN_LABELS:
        return COLUMN_LABELS[column]
    match = re.fullmatch(r"h(\d+)_(.+)", column)
    if match:
        hour, suffix = match.groups()
        suffix_label = SNAPSHOT_COLUMN_SUFFIXES.get(suffix, suffix)
        return f"{hour}시간 스냅샷 {suffix_label}"
    return column


def localize_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe
    localized = dataframe.copy()
    if "polymer_type" in localized.columns:
        localized["polymer_type"] = localized["polymer_type"].map(format_polymer).fillna(localized["polymer_type"])
    if "oil_type" in localized.columns:
        localized["oil_type"] = localized["oil_type"].map(format_oil).fillna(localized["oil_type"])
    if "parameter_source" in localized.columns:
        localized["parameter_source"] = localized["parameter_source"].map(format_parameter_source).fillna(localized["parameter_source"])
    for column in (
        "use_demo_data",
        "stokes_drift",
        "vertical_mixing",
        "vertical_advection",
    ):
        if column in localized.columns:
            localized[column] = localized[column].map(BOOLEAN_LABELS).fillna(localized[column])
    localized.columns = [localize_column_name(str(column)) for column in localized.columns]
    return localized


def localize_manifest(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {MANIFEST_KEY_LABELS.get(str(key), str(key)): localize_manifest(value) for key, value in payload.items()}
    if isinstance(payload, list):
        return [localize_manifest(item) for item in payload]
    return payload

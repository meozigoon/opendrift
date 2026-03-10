from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable
from datetime import datetime
import math

import xarray as xr

from src.utils.paths import PROJECT_ROOT, resolve_project_path


ALLOWED_POLYMERS = {"PE", "PP", "PET"}
ALLOWED_SALINITIES = {33, 40}
ALLOWED_OILS = {"diesel", "kerosene"}
KIND_LABELS = {"current": "해류", "wind": "바람"}
FIELD_LABELS = {
    "release.lat": "방출 위도",
    "release.lon": "방출 경도",
    "release.time": "방출 시각",
    "release.duration_hours": "지속 시간",
    "release.particles": "입자 수",
    "release.radius_m": "방출 반경",
    "drift.terminal_velocity": "종말 속도",
    "drift.wind_drift_factor": "풍하중 계수",
    "drift.current_drift_factor": "해류 이동 계수",
    "targets.radius_km": "목표 반경",
    "runtime.time_step_minutes": "계산 시간 간격",
    "runtime.output_time_step_minutes": "출력 시간 간격",
}


@dataclass(slots=True)
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _dataset_has_variable(
    dataset: xr.Dataset,
    variable_names: Iterable[str],
    standard_names: Iterable[str],
) -> bool:
    names = set(variable_names)
    standards = set(standard_names)
    for name, data_array in dataset.data_vars.items():
        if name in names:
            return True
        if data_array.attrs.get("standard_name") in standards:
            return True
    return False


def validate_netcdf_file(path: Path, kind: str) -> ValidationResult:
    result = ValidationResult()
    kind_label = KIND_LABELS.get(kind, kind)
    try:
        dataset = xr.open_dataset(path)
    except Exception as exc:  # pragma: no cover
        result.errors.append(f"{kind_label} NetCDF 파일을 열 수 없습니다: {exc}")
        return result

    try:
        if "time" not in dataset.coords:
            result.errors.append(f"{kind_label} NetCDF에 time 좌표가 없습니다.")
        if not any(coord in dataset.coords for coord in ("lat", "latitude")):
            result.errors.append(f"{kind_label} NetCDF에 위도 좌표가 없습니다.")
        if not any(coord in dataset.coords for coord in ("lon", "longitude")):
            result.errors.append(f"{kind_label} NetCDF에 경도 좌표가 없습니다.")

        if kind == "current":
            has_u = _dataset_has_variable(
                dataset,
                {"uo", "eastward_sea_water_velocity", "x_sea_water_velocity"},
                {"eastward_sea_water_velocity", "x_sea_water_velocity"},
            )
            has_v = _dataset_has_variable(
                dataset,
                {"vo", "northward_sea_water_velocity", "y_sea_water_velocity"},
                {"northward_sea_water_velocity", "y_sea_water_velocity"},
            )
            if not has_u or not has_v:
                result.errors.append(
                    "해류 NetCDF에는 동서 및 남북 해류 성분이 있어야 하며, "
                    "CF 변수명 또는 standard_name 속성으로 식별 가능해야 합니다."
                )
        if kind == "wind":
            has_u = _dataset_has_variable(dataset, {"uwnd", "x_wind"}, {"x_wind"})
            has_v = _dataset_has_variable(dataset, {"vwnd", "y_wind"}, {"y_wind"})
            if not has_u or not has_v:
                result.errors.append(
                    "바람 NetCDF에는 x_wind와 y_wind 성분이 있어야 하며, "
                    "CF 변수명 또는 standard_name 속성으로 식별 가능해야 합니다."
                )
    finally:
        dataset.close()
    return result


def validate_scenario_payload(payload: dict, project_root: Path | None = None) -> ValidationResult:
    result = ValidationResult()
    root = project_root or PROJECT_ROOT

    polymer = payload.get("polymer_type")
    if polymer not in ALLOWED_POLYMERS:
        result.errors.append(f"고분자 종류는 {sorted(ALLOWED_POLYMERS)} 중 하나여야 합니다.")

    salinity = payload.get("salinity_psu")
    if salinity not in ALLOWED_SALINITIES:
        result.errors.append("염분은 33 또는 40 PSU여야 합니다.")

    oil = payload.get("oil_type")
    if oil not in ALLOWED_OILS:
        result.errors.append(f"유류 종류는 {sorted(ALLOWED_OILS)} 중 하나여야 합니다.")

    release = payload.get("release", {})
    drift = payload.get("drift", {})
    data_source = payload.get("data_source", {})
    targets = payload.get("targets", {})
    runtime = payload.get("runtime", {})

    for label, value, bounds in (
        ("release.lat", release.get("lat"), (-90, 90)),
        ("release.lon", release.get("lon"), (-180, 180)),
    ):
        label_text = FIELD_LABELS.get(label, label)
        if not _is_number(value):
            result.errors.append(f"{label_text}는 유한한 숫자여야 합니다.")
        elif not bounds[0] <= float(value) <= bounds[1]:
            result.errors.append(f"{label_text}는 {bounds[0]} 이상 {bounds[1]} 이하여야 합니다.")

    try:
        datetime.fromisoformat(str(release.get("time")))
    except Exception:
        result.errors.append("방출 시각은 ISO-8601 형식의 날짜-시간 문자열이어야 합니다.")

    for label, value in (
        ("release.duration_hours", release.get("duration_hours")),
        ("release.particles", release.get("particles")),
        ("release.radius_m", release.get("radius_m")),
        ("drift.terminal_velocity", drift.get("terminal_velocity")),
        ("drift.wind_drift_factor", drift.get("wind_drift_factor")),
        ("drift.current_drift_factor", drift.get("current_drift_factor")),
        ("targets.radius_km", targets.get("radius_km")),
        ("runtime.time_step_minutes", runtime.get("time_step_minutes")),
        ("runtime.output_time_step_minutes", runtime.get("output_time_step_minutes")),
    ):
        label_text = FIELD_LABELS.get(label, label)
        if not _is_number(value):
            result.errors.append(f"{label_text}는 유한한 숫자여야 합니다.")

    if _is_number(release.get("duration_hours")) and int(release["duration_hours"]) <= 0:
        result.errors.append("지속 시간은 0보다 커야 합니다.")
    if _is_number(release.get("particles")) and int(release["particles"]) <= 0:
        result.errors.append("입자 수는 0보다 커야 합니다.")
    if _is_number(release.get("radius_m")) and float(release["radius_m"]) < 0:
        result.errors.append("방출 반경은 0 이상이어야 합니다.")
    if _is_number(targets.get("radius_km")) and float(targets["radius_km"]) < 0:
        result.errors.append("목표 반경은 0 이상이어야 합니다.")

    bbox = targets.get("interest_area_bbox")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(value) for value in bbox):
            result.errors.append("관심 영역 경계상자는 [최소 경도, 최대 경도, 최소 위도, 최대 위도] 형식이어야 합니다.")
        elif not (bbox[0] < bbox[1] and bbox[2] < bbox[3]):
            result.errors.append("관심 영역 경계상자의 범위가 올바르지 않습니다.")

    if drift.get("stokes_drift"):
        result.warnings.append("스토크스 표류가 활성화되어 있습니다. 기준 연구 설계에서는 이 옵션을 사용하지 않습니다.")
    if drift.get("vertical_mixing"):
        result.warnings.append("수직 혼합이 활성화되어 있습니다. 기준 연구 설계에서는 이 옵션을 사용하지 않습니다.")
    if drift.get("vertical_advection"):
        result.warnings.append("수직 이류가 활성화되어 있습니다. 기준 연구 설계에서는 이 옵션을 사용하지 않습니다.")

    use_demo_data = bool(data_source.get("use_demo_data"))
    if use_demo_data:
        result.info.append("데모 모드는 합성 해류 및 바람 NetCDF를 사용하며 실제 해양 관측 자료가 아닙니다.")
    else:
        current_path = resolve_project_path(data_source.get("current_path"), root)
        wind_path = resolve_project_path(data_source.get("wind_path"), root)
        if current_path is None:
            result.errors.append("실제 실행에는 해류 NetCDF 경로 또는 업로드 파일이 필요합니다.")
        if wind_path is None:
            result.errors.append("실제 실행에는 바람 NetCDF 경로 또는 업로드 파일이 필요합니다.")
        for file_path, kind in ((current_path, "current"), (wind_path, "wind")):
            if file_path is None:
                continue
            if not file_path.exists():
                result.errors.append(f"{KIND_LABELS.get(kind, kind)} NetCDF 파일을 찾을 수 없습니다: {file_path}")
            else:
                file_validation = validate_netcdf_file(file_path, kind)
                result.errors.extend(file_validation.errors)
                result.warnings.extend(file_validation.warnings)
                result.info.extend(file_validation.info)

    return result

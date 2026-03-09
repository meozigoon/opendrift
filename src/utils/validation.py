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
    try:
        dataset = xr.open_dataset(path)
    except Exception as exc:  # pragma: no cover
        result.errors.append(f"{kind} NetCDF could not be opened: {exc}")
        return result

    try:
        if "time" not in dataset.coords:
            result.errors.append(f"{kind} NetCDF is missing the time coordinate.")
        if not any(coord in dataset.coords for coord in ("lat", "latitude")):
            result.errors.append(f"{kind} NetCDF is missing a latitude coordinate.")
        if not any(coord in dataset.coords for coord in ("lon", "longitude")):
            result.errors.append(f"{kind} NetCDF is missing a longitude coordinate.")

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
                    "Current NetCDF must expose eastward/northward current components "
                    "with CF variable names or standard_name attributes."
                )
        if kind == "wind":
            has_u = _dataset_has_variable(dataset, {"uwnd", "x_wind"}, {"x_wind"})
            has_v = _dataset_has_variable(dataset, {"vwnd", "y_wind"}, {"y_wind"})
            if not has_u or not has_v:
                result.errors.append(
                    "Wind NetCDF must expose x_wind and y_wind components "
                    "with CF variable names or standard_name attributes."
                )
    finally:
        dataset.close()
    return result


def validate_scenario_payload(payload: dict, project_root: Path | None = None) -> ValidationResult:
    result = ValidationResult()
    root = project_root or PROJECT_ROOT

    polymer = payload.get("polymer_type")
    if polymer not in ALLOWED_POLYMERS:
        result.errors.append(f"polymer_type must be one of {sorted(ALLOWED_POLYMERS)}.")

    salinity = payload.get("salinity_psu")
    if salinity not in ALLOWED_SALINITIES:
        result.errors.append("salinity_psu must be 33 or 40.")

    oil = payload.get("oil_type")
    if oil not in ALLOWED_OILS:
        result.errors.append(f"oil_type must be one of {sorted(ALLOWED_OILS)}.")

    release = payload.get("release", {})
    drift = payload.get("drift", {})
    data_source = payload.get("data_source", {})
    targets = payload.get("targets", {})
    runtime = payload.get("runtime", {})

    for label, value, bounds in (
        ("release.lat", release.get("lat"), (-90, 90)),
        ("release.lon", release.get("lon"), (-180, 180)),
    ):
        if not _is_number(value):
            result.errors.append(f"{label} must be a finite number.")
        elif not bounds[0] <= float(value) <= bounds[1]:
            result.errors.append(f"{label} must be between {bounds[0]} and {bounds[1]}.")

    try:
        datetime.fromisoformat(str(release.get("time")))
    except Exception:
        result.errors.append("release.time must be an ISO-8601 datetime string.")

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
        if not _is_number(value):
            result.errors.append(f"{label} must be a finite number.")

    if _is_number(release.get("duration_hours")) and int(release["duration_hours"]) <= 0:
        result.errors.append("release.duration_hours must be greater than 0.")
    if _is_number(release.get("particles")) and int(release["particles"]) <= 0:
        result.errors.append("release.particles must be greater than 0.")
    if _is_number(release.get("radius_m")) and float(release["radius_m"]) < 0:
        result.errors.append("release.radius_m must be 0 or greater.")
    if _is_number(targets.get("radius_km")) and float(targets["radius_km"]) < 0:
        result.errors.append("targets.radius_km must be 0 or greater.")

    bbox = targets.get("interest_area_bbox")
    if bbox is not None:
        if not isinstance(bbox, list) or len(bbox) != 4 or not all(_is_number(value) for value in bbox):
            result.errors.append("targets.interest_area_bbox must be [min_lon, max_lon, min_lat, max_lat].")
        elif not (bbox[0] < bbox[1] and bbox[2] < bbox[3]):
            result.errors.append("targets.interest_area_bbox bounds are invalid.")

    if drift.get("stokes_drift"):
        result.warnings.append("stokes_drift is enabled. The baseline study design assumes stokes_drift=False.")
    if drift.get("vertical_mixing"):
        result.warnings.append("vertical_mixing is enabled. The baseline study design assumes vertical_mixing=False.")
    if drift.get("vertical_advection"):
        result.warnings.append("vertical_advection is enabled. The baseline study design assumes vertical_advection=False.")

    use_demo_data = bool(data_source.get("use_demo_data"))
    if use_demo_data:
        result.info.append("Demo mode uses synthetic current/wind NetCDF files and is not a real ocean dataset.")
    else:
        current_path = resolve_project_path(data_source.get("current_path"), root)
        wind_path = resolve_project_path(data_source.get("wind_path"), root)
        if current_path is None:
            result.errors.append("Real execution requires a current NetCDF path or uploaded file.")
        if wind_path is None:
            result.errors.append("Real execution requires a wind NetCDF path or uploaded file.")
        for file_path, kind in ((current_path, "current"), (wind_path, "wind")):
            if file_path is None:
                continue
            if not file_path.exists():
                result.errors.append(f"{kind} NetCDF not found: {file_path}")
            else:
                file_validation = validate_netcdf_file(file_path, kind)
                result.errors.extend(file_validation.errors)
                result.warnings.extend(file_validation.warnings)
                result.info.extend(file_validation.info)

    return result

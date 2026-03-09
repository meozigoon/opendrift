from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
import json

import yaml

from src.utils.paths import CONFIG_DIR, PROJECT_ROOT, resolve_project_path


DEFAULTS_PATH = CONFIG_DIR / "defaults.yaml"


@dataclass(slots=True)
class ScenarioConfig:
    scenario_name: str
    polymer_type: str
    salinity_psu: int
    oil_type: str
    release_lat: float
    release_lon: float
    release_time: str
    duration_hours: int
    particles: int
    release_radius_m: float
    terminal_velocity: float
    wind_drift_factor: float
    current_drift_factor: float
    stokes_drift: bool = False
    vertical_mixing: bool = False
    vertical_advection: bool = False
    z: float = 0.0
    temperature_c: float = 25.0
    output_name: str = ""
    current_path: str | None = None
    wind_path: str | None = None
    use_demo_data: bool = False
    target_radius_km: float = 50.0
    interest_area_bbox: list[float] | None = None
    time_step_minutes: int = 60
    output_time_step_minutes: int = 60
    log_level: str = "INFO"
    output_root: str = "data/output"
    snapshots_hours: list[int] = field(default_factory=lambda: [24, 72, 168])
    animation_frame_stride: int = 1
    export_variables: list[str] = field(default_factory=list)
    parameter_source: str = "preset"
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def release_datetime(self) -> datetime:
        return datetime.fromisoformat(self.release_time)

    @property
    def output_label(self) -> str:
        return self.output_name or self.scenario_name


def load_defaults(defaults_path: Path | None = None) -> dict[str, Any]:
    path = defaults_path or DEFAULTS_PATH
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_scenario_payload(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    defaults = defaults or load_defaults()
    preset = defaults["parameter_presets"]["PE"]["33"]["diesel"]
    return {
        "scenario_name": "pe_33psu_diesel_surface_demo",
        "output_name": "pe_33psu_diesel_surface_demo",
        "polymer_type": "PE",
        "salinity_psu": 33,
        "oil_type": "diesel",
        "release": {
            "lat": defaults["ui_defaults"]["release_lat"],
            "lon": defaults["ui_defaults"]["release_lon"],
            "time": defaults["ui_defaults"]["release_time"],
            "duration_hours": defaults["simulation"]["duration_hours"],
            "particles": defaults["simulation"]["particles"],
            "radius_m": defaults["simulation"]["release_radius_m"],
            "z": defaults["simulation"]["z"],
        },
        "drift": {
            "terminal_velocity": preset["terminal_velocity"],
            "wind_drift_factor": preset["wind_drift_factor"],
            "current_drift_factor": preset["current_drift_factor"],
            "stokes_drift": defaults["simulation"]["stokes_drift"],
            "vertical_mixing": defaults["simulation"]["vertical_mixing"],
            "vertical_advection": defaults["simulation"]["vertical_advection"],
        },
        "data_source": {
            "use_demo_data": True,
            "current_path": None,
            "wind_path": None,
        },
        "targets": {
            "radius_km": defaults["analysis"]["target_radius_km"],
            "interest_area_bbox": None,
        },
        "runtime": {
            "time_step_minutes": defaults["simulation"]["time_step_minutes"],
            "output_time_step_minutes": defaults["simulation"]["output_time_step_minutes"],
            "log_level": defaults["simulation"]["log_level"],
            "output_root": defaults["project"]["output_root"],
            "export_variables": defaults["simulation"].get("export_variables", []),
        },
        "analysis": {
            "snapshots_hours": defaults["analysis"]["snapshots_hours"],
            "animation_frame_stride": defaults["analysis"]["animation_frame_stride"],
        },
        "metadata": {
            "temperature_c": defaults["project"]["temperature_c"],
            "notes": "Synthetic demo mode. Replace with real NetCDF paths for research runs.",
        },
    }


def get_parameter_preset(defaults: dict[str, Any], polymer: str, salinity_psu: int, oil_type: str) -> dict[str, float]:
    return defaults["parameter_presets"][polymer][str(salinity_psu)][oil_type]


def normalize_payload(payload: dict[str, Any], defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    base = default_scenario_payload(defaults)
    return deep_merge(base, payload)


def resolve_scenario_payload(
    payload: dict[str, Any],
    defaults: dict[str, Any] | None = None,
    base_dir: Path | None = None,
) -> tuple[ScenarioConfig, dict[str, Any]]:
    defaults = defaults or load_defaults()
    root = base_dir or PROJECT_ROOT
    normalized = normalize_payload(payload, defaults)
    preset = get_parameter_preset(
        defaults,
        normalized["polymer_type"],
        int(normalized["salinity_psu"]),
        normalized["oil_type"],
    )

    drift = normalized["drift"]
    parameter_source = "user_override"
    for key in ("terminal_velocity", "wind_drift_factor", "current_drift_factor"):
        if drift.get(key) is None:
            drift[key] = preset[key]
            parameter_source = f"preset:{normalized['polymer_type']}/{normalized['salinity_psu']}/{normalized['oil_type']}"
    if parameter_source == "user_override" and all(drift.get(key) == preset[key] for key in preset):
        parameter_source = f"preset:{normalized['polymer_type']}/{normalized['salinity_psu']}/{normalized['oil_type']}"

    runtime = normalized["runtime"]
    analysis = normalized["analysis"]
    metadata = dict(normalized.get("metadata", {}))
    metadata.setdefault("temperature_c", defaults["project"]["temperature_c"])
    metadata["resolved_at"] = datetime.now().isoformat(timespec="seconds")
    metadata["parameter_preset"] = preset

    resolved = ScenarioConfig(
        scenario_name=str(normalized["scenario_name"]),
        polymer_type=str(normalized["polymer_type"]),
        salinity_psu=int(normalized["salinity_psu"]),
        oil_type=str(normalized["oil_type"]),
        release_lat=float(normalized["release"]["lat"]),
        release_lon=float(normalized["release"]["lon"]),
        release_time=str(normalized["release"]["time"]),
        duration_hours=int(normalized["release"]["duration_hours"]),
        particles=int(normalized["release"]["particles"]),
        release_radius_m=float(normalized["release"]["radius_m"]),
        terminal_velocity=float(drift["terminal_velocity"]),
        wind_drift_factor=float(drift["wind_drift_factor"]),
        current_drift_factor=float(drift["current_drift_factor"]),
        stokes_drift=bool(drift["stokes_drift"]),
        vertical_mixing=bool(drift["vertical_mixing"]),
        vertical_advection=bool(drift["vertical_advection"]),
        z=float(normalized["release"].get("z", defaults["simulation"]["z"])),
        temperature_c=float(metadata["temperature_c"]),
        output_name=str(normalized.get("output_name") or normalized["scenario_name"]),
        current_path=str(resolve_project_path(normalized["data_source"].get("current_path"), root)) if normalized["data_source"].get("current_path") else None,
        wind_path=str(resolve_project_path(normalized["data_source"].get("wind_path"), root)) if normalized["data_source"].get("wind_path") else None,
        use_demo_data=bool(normalized["data_source"].get("use_demo_data")),
        target_radius_km=float(normalized["targets"]["radius_km"]),
        interest_area_bbox=normalized["targets"].get("interest_area_bbox"),
        time_step_minutes=int(runtime["time_step_minutes"]),
        output_time_step_minutes=int(runtime["output_time_step_minutes"]),
        log_level=str(runtime["log_level"]).upper(),
        output_root=str(runtime.get("output_root", defaults["project"]["output_root"])),
        snapshots_hours=[int(hour) for hour in analysis["snapshots_hours"]],
        animation_frame_stride=int(analysis.get("animation_frame_stride", defaults["analysis"]["animation_frame_stride"])),
        export_variables=list(runtime.get("export_variables", defaults["simulation"].get("export_variables", []))),
        parameter_source=parameter_source,
        metadata=metadata,
    )
    return resolved, normalized


def scenario_to_dict(scenario: ScenarioConfig) -> dict[str, Any]:
    payload = asdict(scenario)
    return {
        "scenario_name": payload["scenario_name"],
        "output_name": payload["output_name"],
        "polymer_type": payload["polymer_type"],
        "salinity_psu": payload["salinity_psu"],
        "oil_type": payload["oil_type"],
        "release": {
            "lat": payload["release_lat"],
            "lon": payload["release_lon"],
            "time": payload["release_time"],
            "duration_hours": payload["duration_hours"],
            "particles": payload["particles"],
            "radius_m": payload["release_radius_m"],
            "z": payload["z"],
        },
        "drift": {
            "terminal_velocity": payload["terminal_velocity"],
            "wind_drift_factor": payload["wind_drift_factor"],
            "current_drift_factor": payload["current_drift_factor"],
            "stokes_drift": payload["stokes_drift"],
            "vertical_mixing": payload["vertical_mixing"],
            "vertical_advection": payload["vertical_advection"],
        },
        "data_source": {
            "use_demo_data": payload["use_demo_data"],
            "current_path": payload["current_path"],
            "wind_path": payload["wind_path"],
        },
        "targets": {
            "radius_km": payload["target_radius_km"],
            "interest_area_bbox": payload["interest_area_bbox"],
        },
        "runtime": {
            "time_step_minutes": payload["time_step_minutes"],
            "output_time_step_minutes": payload["output_time_step_minutes"],
            "log_level": payload["log_level"],
            "output_root": payload["output_root"],
            "export_variables": payload["export_variables"],
        },
        "analysis": {
            "snapshots_hours": payload["snapshots_hours"],
            "animation_frame_stride": payload["animation_frame_stride"],
        },
        "metadata": payload["metadata"],
        "parameter_source": payload["parameter_source"],
    }


def load_scenario_file(path: Path, defaults: dict[str, Any] | None = None) -> tuple[ScenarioConfig, dict[str, Any]]:
    if path.suffix.lower() in {".yaml", ".yml"}:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
    return resolve_scenario_payload(payload, defaults=defaults, base_dir=path.parent)

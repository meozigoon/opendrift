from __future__ import annotations

import streamlit as st

from src.simulation.config_loader import default_scenario_payload, load_defaults


def _set_state_value(key: str, value, overwrite: bool) -> None:
    if overwrite or key not in st.session_state:
        st.session_state[key] = value


def apply_payload_to_state(payload: dict, overwrite: bool = True) -> None:
    bbox = payload.get("targets", {}).get("interest_area_bbox")
    _set_state_value("form_scenario_name", payload.get("scenario_name", ""), overwrite)
    _set_state_value("form_output_name", payload.get("output_name", ""), overwrite)
    _set_state_value("form_polymer_type", payload.get("polymer_type", "PE"), overwrite)
    _set_state_value("form_salinity_psu", int(payload.get("salinity_psu", 33)), overwrite)
    _set_state_value("form_oil_type", payload.get("oil_type", "diesel"), overwrite)
    _set_state_value("form_release_lat", float(payload.get("release", {}).get("lat", 35.0)), overwrite)
    _set_state_value("form_release_lon", float(payload.get("release", {}).get("lon", 129.0)), overwrite)
    _set_state_value("form_release_time", payload.get("release", {}).get("time", "2024-01-01T00:00:00"), overwrite)
    _set_state_value("form_duration_hours", int(payload.get("release", {}).get("duration_hours", 168)), overwrite)
    _set_state_value("form_particles", int(payload.get("release", {}).get("particles", 300)), overwrite)
    _set_state_value("form_radius_m", float(payload.get("release", {}).get("radius_m", 5000.0)), overwrite)
    _set_state_value("form_z", float(payload.get("release", {}).get("z", 0.0)), overwrite)
    _set_state_value("form_terminal_velocity", float(payload.get("drift", {}).get("terminal_velocity", 0.0)), overwrite)
    _set_state_value("form_wind_drift_factor", float(payload.get("drift", {}).get("wind_drift_factor", 0.03)), overwrite)
    _set_state_value("form_current_drift_factor", float(payload.get("drift", {}).get("current_drift_factor", 1.0)), overwrite)
    _set_state_value("form_stokes_drift", bool(payload.get("drift", {}).get("stokes_drift", False)), overwrite)
    _set_state_value("form_vertical_mixing", bool(payload.get("drift", {}).get("vertical_mixing", False)), overwrite)
    _set_state_value("form_vertical_advection", bool(payload.get("drift", {}).get("vertical_advection", False)), overwrite)
    _set_state_value("form_use_demo_data", bool(payload.get("data_source", {}).get("use_demo_data", True)), overwrite)
    _set_state_value("form_current_path", payload.get("data_source", {}).get("current_path") or "", overwrite)
    _set_state_value("form_wind_path", payload.get("data_source", {}).get("wind_path") or "", overwrite)
    _set_state_value("form_target_radius_km", float(payload.get("targets", {}).get("radius_km", 50.0)), overwrite)
    _set_state_value("form_interest_enabled", bbox is not None, overwrite)
    _set_state_value("form_interest_min_lon", float(bbox[0]) if bbox else 0.0, overwrite)
    _set_state_value("form_interest_max_lon", float(bbox[1]) if bbox else 0.0, overwrite)
    _set_state_value("form_interest_min_lat", float(bbox[2]) if bbox else 0.0, overwrite)
    _set_state_value("form_interest_max_lat", float(bbox[3]) if bbox else 0.0, overwrite)


def build_payload_from_state(defaults: dict | None = None) -> dict:
    defaults = defaults or load_defaults()
    bbox = None
    if st.session_state.get("form_interest_enabled"):
        bbox = [
            float(st.session_state["form_interest_min_lon"]),
            float(st.session_state["form_interest_max_lon"]),
            float(st.session_state["form_interest_min_lat"]),
            float(st.session_state["form_interest_max_lat"]),
        ]
    return {
        "scenario_name": st.session_state["form_scenario_name"],
        "output_name": st.session_state["form_output_name"],
        "polymer_type": st.session_state["form_polymer_type"],
        "salinity_psu": int(st.session_state["form_salinity_psu"]),
        "oil_type": st.session_state["form_oil_type"],
        "release": {
            "lat": float(st.session_state["form_release_lat"]),
            "lon": float(st.session_state["form_release_lon"]),
            "time": st.session_state["form_release_time"],
            "duration_hours": int(st.session_state["form_duration_hours"]),
            "particles": int(st.session_state["form_particles"]),
            "radius_m": float(st.session_state["form_radius_m"]),
            "z": float(st.session_state["form_z"]),
        },
        "drift": {
            "terminal_velocity": float(st.session_state["form_terminal_velocity"]),
            "wind_drift_factor": float(st.session_state["form_wind_drift_factor"]),
            "current_drift_factor": float(st.session_state["form_current_drift_factor"]),
            "stokes_drift": bool(st.session_state["form_stokes_drift"]),
            "vertical_mixing": bool(st.session_state["form_vertical_mixing"]),
            "vertical_advection": bool(st.session_state["form_vertical_advection"]),
        },
        "data_source": {
            "use_demo_data": bool(st.session_state["form_use_demo_data"]),
            "current_path": st.session_state["form_current_path"] or None,
            "wind_path": st.session_state["form_wind_path"] or None,
        },
        "targets": {
            "radius_km": float(st.session_state["form_target_radius_km"]),
            "interest_area_bbox": bbox,
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
            "notes": "Saved from Streamlit UI.",
        },
    }


def init_state() -> None:
    defaults = load_defaults()
    apply_payload_to_state(default_scenario_payload(defaults), overwrite=False)
    st.session_state.setdefault("form_initialized", True)
    st.session_state.setdefault("active_result_dir", None)
    st.session_state.setdefault("last_run_logs", [])
    st.session_state.setdefault("comparison_artifacts", {})

from __future__ import annotations

import logging

from opendrift.models.plastdrift import PlastDrift

from src.simulation.config_loader import ScenarioConfig


def create_model(scenario: ScenarioConfig) -> PlastDrift:
    loglevel = getattr(logging, scenario.log_level.upper(), logging.INFO)
    model = PlastDrift(loglevel=loglevel)
    settings = {
        "general:simulation_name": scenario.scenario_name,
        "general:time_step_minutes": scenario.time_step_minutes,
        "general:time_step_output_minutes": scenario.output_time_step_minutes,
        "environment:fallback:land_binary_mask": 0,
        "drift:vertical_mixing": scenario.vertical_mixing,
        "drift:vertical_advection": scenario.vertical_advection,
        "drift:stokes_drift": scenario.stokes_drift,
        "seed:z": scenario.z,
        "seed:terminal_velocity": scenario.terminal_velocity,
        "seed:wind_drift_factor": scenario.wind_drift_factor,
        "seed:current_drift_factor": scenario.current_drift_factor,
    }
    for key, value in settings.items():
        model.set_config(key, value)
    return model

from __future__ import annotations

from opendrift.models.plastdrift import PlastDrift

from src.simulation.config_loader import ScenarioConfig


def seed_model(model: PlastDrift, scenario: ScenarioConfig) -> None:
    model.seed_elements(
        lon=scenario.release_lon,
        lat=scenario.release_lat,
        time=scenario.release_datetime,
        radius=scenario.release_radius_m,
        number=scenario.particles,
        z=scenario.z,
        terminal_velocity=scenario.terminal_velocity,
        wind_drift_factor=scenario.wind_drift_factor,
        current_drift_factor=scenario.current_drift_factor,
    )

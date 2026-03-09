from src.simulation.config_loader import default_scenario_payload, load_defaults, resolve_scenario_payload


def test_resolve_scenario_payload_uses_defaults() -> None:
    defaults = load_defaults()
    payload = default_scenario_payload(defaults)
    scenario, normalized = resolve_scenario_payload(payload, defaults)
    assert scenario.scenario_name == "pe_33psu_diesel_surface_demo"
    assert scenario.temperature_c == 25.0
    assert scenario.stokes_drift is False
    assert normalized["analysis"]["snapshots_hours"] == [24, 72, 168]


def test_resolve_scenario_payload_accepts_override() -> None:
    defaults = load_defaults()
    payload = default_scenario_payload(defaults)
    payload["polymer_type"] = "PET"
    payload["salinity_psu"] = 40
    payload["oil_type"] = "kerosene"
    payload["drift"]["terminal_velocity"] = -0.0035
    scenario, _ = resolve_scenario_payload(payload, defaults)
    assert scenario.polymer_type == "PET"
    assert scenario.salinity_psu == 40
    assert scenario.terminal_velocity == -0.0035
    assert scenario.parameter_source == "user_override"

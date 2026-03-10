from src.simulation.config_loader import default_scenario_payload, load_defaults
from src.utils.validation import validate_scenario_payload


def test_demo_payload_is_valid() -> None:
    defaults = load_defaults()
    payload = default_scenario_payload(defaults)
    result = validate_scenario_payload(payload)
    assert result.ok
    assert result.info


def test_real_payload_requires_files() -> None:
    defaults = load_defaults()
    payload = default_scenario_payload(defaults)
    payload["data_source"]["use_demo_data"] = False
    payload["data_source"]["current_path"] = None
    payload["data_source"]["wind_path"] = None
    result = validate_scenario_payload(payload)
    assert not result.ok
    assert any("해류 NetCDF" in message for message in result.errors)

from pathlib import Path

from src.simulation.config_loader import default_scenario_payload, load_defaults, resolve_scenario_payload
from src.simulation.runner import run_scenario


def test_runner_smoke(tmp_path: Path) -> None:
    defaults = load_defaults()
    payload = default_scenario_payload(defaults)
    payload["scenario_name"] = "smoke_demo"
    payload["output_name"] = "smoke_demo"
    payload["release"]["duration_hours"] = 3
    payload["release"]["particles"] = 8
    payload["release"]["radius_m"] = 500
    payload["runtime"]["output_root"] = str(tmp_path)
    payload["analysis"]["snapshots_hours"] = [1, 2, 3]
    scenario, normalized = resolve_scenario_payload(payload, defaults)
    result = run_scenario(scenario, normalized, unique_output_dir=False)
    assert result.result_path.exists()
    assert (result.output_dir / "summary.csv").exists()
    assert (result.output_dir / "metrics.csv").exists()
    assert (result.output_dir / "trajectory_map.png").exists()
    assert (result.output_dir / "animation.gif").exists()
    assert (result.output_dir / "results_bundle.zip").exists()

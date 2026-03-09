from __future__ import annotations

import argparse
from pathlib import Path

from src.simulation.config_loader import load_defaults, load_scenario_file
from src.simulation.runner import run_scenario


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an OpenDrift PlastDrift scenario.")
    parser.add_argument("--config", required=True, help="Scenario JSON/YAML path.")
    parser.add_argument("--validate-only", action="store_true", help="Resolve the scenario and exit without running.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    defaults = load_defaults()
    scenario, raw_payload = load_scenario_file(Path(args.config), defaults)
    if args.validate_only:
        print(f"Scenario validated: {scenario.scenario_name}")
        return 0
    result = run_scenario(scenario, raw_payload)
    print(f"Completed: {result.output_dir}")
    print(f"Bundle: {result.bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

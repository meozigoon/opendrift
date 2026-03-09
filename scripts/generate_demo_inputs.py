from __future__ import annotations

import argparse
from pathlib import Path

from src.simulation.config_loader import default_scenario_payload, load_defaults, resolve_scenario_payload
from src.simulation.readers import create_demo_inputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate synthetic current/wind NetCDF files for demo mode.")
    parser.add_argument("--output-dir", required=True, help="Output directory for demo NetCDF files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    defaults = load_defaults()
    scenario, _ = resolve_scenario_payload(default_scenario_payload(defaults), defaults)
    current_path, wind_path = create_demo_inputs(Path(args.output_dir), scenario)
    print(f"Current demo file: {current_path}")
    print(f"Wind demo file: {wind_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

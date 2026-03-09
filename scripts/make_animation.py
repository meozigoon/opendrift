from __future__ import annotations

import argparse
from pathlib import Path

import xarray as xr

from src.analysis.snapshot import build_animation_gif
from src.simulation.config_loader import resolve_scenario_payload
from src.utils.file_utils import read_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild the GIF animation for an existing result directory.")
    parser.add_argument("--result-dir", required=True, help="Result directory containing result.nc and resolved_scenario.json.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result_dir = Path(args.result_dir)
    scenario, _ = resolve_scenario_payload(read_json(result_dir / "resolved_scenario.json"))
    with xr.open_dataset(result_dir / "result.nc") as dataset_file:
        dataset = dataset_file.load()
    output = build_animation_gif(dataset, scenario, result_dir / "animation.gif", frame_stride=scenario.animation_frame_stride)
    dataset.close()
    print(f"Animation rebuilt: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

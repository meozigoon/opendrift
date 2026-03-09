from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analysis.report_builder import build_comparison_report
from src.simulation.config_loader import load_defaults, load_scenario_file
from src.simulation.runner import run_scenario
from src.utils.paths import REPORT_SUMMARIES_DIR


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run multiple PlastDrift scenarios in sequence.")
    parser.add_argument("--dir", required=True, help="Directory containing scenario JSON/YAML files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    scenario_dir = Path(args.dir)
    defaults = load_defaults()
    outputs = []
    for path in sorted(list(scenario_dir.glob("*.json")) + list(scenario_dir.glob("*.yaml")) + list(scenario_dir.glob("*.yml"))):
        scenario, raw_payload = load_scenario_file(path, defaults)
        result = run_scenario(scenario, raw_payload)
        outputs.append(result.output_dir)
        print(f"Completed: {path.name} -> {result.output_dir}")

    comparison = build_comparison_report(outputs)
    summary_csv = Path(comparison["comparison_summary_csv"])
    REPORT_SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    batch_summary = pd.read_csv(summary_csv)
    batch_summary.to_csv(REPORT_SUMMARIES_DIR / "batch_summary.csv", index=False)
    print(f"Batch summary: {REPORT_SUMMARIES_DIR / 'batch_summary.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

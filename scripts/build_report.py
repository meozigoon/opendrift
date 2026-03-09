from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.analysis.report_builder import build_markdown_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild the Markdown report for an existing result directory.")
    parser.add_argument("--result-dir", required=True, help="Result directory containing summary.csv and metrics.csv.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result_dir = Path(args.result_dir)
    summary_df = pd.read_csv(result_dir / "summary.csv")
    metrics_df = pd.read_csv(result_dir / "metrics.csv", parse_dates=["timestamp"])
    output = build_markdown_report(result_dir, summary_df, metrics_df)
    print(f"Report rebuilt: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

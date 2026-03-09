from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from src.utils.file_utils import build_manifest, make_results_bundle, write_json


def export_tables(output_dir: Path, summary_df: pd.DataFrame, metrics_df: pd.DataFrame, centroid_df: pd.DataFrame) -> dict[str, Path]:
    paths = {
        "summary_csv": output_dir / "summary.csv",
        "metrics_csv": output_dir / "metrics.csv",
        "centroid_csv": output_dir / "centroid_trajectory.csv",
    }
    summary_df.to_csv(paths["summary_csv"], index=False)
    metrics_df.to_csv(paths["metrics_csv"], index=False)
    centroid_df.to_csv(paths["centroid_csv"], index=False)
    return paths


def export_scenario_copies(output_dir: Path, raw_payload: dict, resolved_payload: dict) -> dict[str, Path]:
    raw_path = output_dir / "scenario_config_copy.json"
    resolved_path = output_dir / "resolved_scenario.json"
    write_json(raw_path, raw_payload)
    write_json(resolved_path, resolved_payload)
    return {"scenario_copy": raw_path, "resolved_scenario": resolved_path}


def export_manifest(output_dir: Path, warnings: list[str], notes: list[str] | None = None) -> Path:
    payload = {
        "warnings": warnings,
        "notes": notes or [],
        "files": build_manifest(output_dir),
    }
    path = output_dir / "manifest.json"
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    return path


def export_bundle(output_dir: Path) -> Path:
    return make_results_bundle(output_dir)

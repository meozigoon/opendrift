from __future__ import annotations

from pathlib import Path

from src.simulation.config_loader import load_defaults, load_scenario_file, normalize_payload
from src.utils.file_utils import read_json, write_json
from src.utils.paths import SCENARIO_DIR, list_result_dirs, slugify


def list_saved_scenarios(scenario_dir: Path | None = None) -> list[Path]:
    root = scenario_dir or SCENARIO_DIR
    if not root.exists():
        return []
    files = sorted(root.glob("*.json")) + sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
    unique_files: dict[str, Path] = {}
    for file_path in files:
        unique_files[str(file_path.resolve())] = file_path
    return list(unique_files.values())


def load_saved_scenario(path: Path) -> dict:
    if path.suffix.lower() in {".yaml", ".yml"}:
        _, payload = load_scenario_file(path)
        return payload
    return normalize_payload(read_json(path), load_defaults())


def save_scenario_payload(payload: dict, scenario_dir: Path | None = None, file_name: str | None = None) -> Path:
    root = scenario_dir or SCENARIO_DIR
    root.mkdir(parents=True, exist_ok=True)
    normalized = normalize_payload(payload, load_defaults())
    stem = file_name or normalized.get("output_name") or normalized.get("scenario_name") or "scenario"
    path = root / f"{slugify(stem)}.json"
    write_json(path, normalized)
    return path
def list_available_results() -> list[Path]:
    return list_result_dirs()

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "configs"
SCENARIO_DIR = CONFIG_DIR / "scenarios"
DATA_DIR = PROJECT_ROOT / "data"
INPUT_DIR = DATA_DIR / "input"
UPLOAD_DIR = INPUT_DIR / "uploads"
OUTPUT_DIR = DATA_DIR / "output"
SAMPLE_DIR = DATA_DIR / "sample"
REPORT_DIR = PROJECT_ROOT / "reports"
REPORT_FIGURES_DIR = REPORT_DIR / "figures"
REPORT_SUMMARIES_DIR = REPORT_DIR / "summaries"


def ensure_project_dirs() -> None:
    for path in (
        CONFIG_DIR,
        SCENARIO_DIR,
        INPUT_DIR,
        UPLOAD_DIR,
        OUTPUT_DIR,
        SAMPLE_DIR,
        REPORT_DIR,
        REPORT_FIGURES_DIR,
        REPORT_SUMMARIES_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    cleaned = cleaned.strip("._")
    return cleaned or "scenario"


def timestamp_tag() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def resolve_project_path(path_str: str | None, base_dir: Path | None = None) -> Path | None:
    if not path_str:
        return None
    path = Path(path_str)
    if path.is_absolute():
        return path
    root = base_dir or PROJECT_ROOT
    return (root / path).resolve()


def make_output_dir(name: str, output_root: Path | None = None, unique: bool = True) -> Path:
    ensure_project_dirs()
    root = output_root or OUTPUT_DIR
    root.mkdir(parents=True, exist_ok=True)
    candidate = root / slugify(name)
    if unique and candidate.exists():
        candidate = root / f"{slugify(name)}_{timestamp_tag()}"
    candidate.mkdir(parents=True, exist_ok=True)
    return candidate


def list_result_dirs(output_root: Path | None = None) -> list[Path]:
    root = output_root or OUTPUT_DIR
    if not root.exists():
        return []
    results = [
        path
        for path in root.iterdir()
        if path.is_dir() and (path / "resolved_scenario.json").exists()
    ]
    return sorted(results, key=lambda item: item.stat().st_mtime, reverse=True)

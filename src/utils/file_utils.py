from __future__ import annotations

from pathlib import Path
import json
import shutil
import zipfile

from src.utils.paths import PROJECT_ROOT, slugify


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def copy_file_if_needed(source: Path, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return destination


def save_uploaded_file(uploaded_file: object, destination_dir: Path, prefix: str) -> Path:
    destination_dir.mkdir(parents=True, exist_ok=True)
    filename = getattr(uploaded_file, "name", f"{prefix}.nc")
    destination = destination_dir / f"{slugify(prefix)}_{slugify(filename)}"
    buffer = getattr(uploaded_file, "getbuffer", None)
    if callable(buffer):
        destination.write_bytes(bytes(buffer()))
    else:
        reader = getattr(uploaded_file, "read")
        destination.write_bytes(reader())
    return destination


def list_files_recursive(root: Path) -> list[Path]:
    return sorted([path for path in root.rglob("*") if path.is_file()])


def build_manifest(root: Path) -> list[dict[str, str | int]]:
    files = []
    for path in list_files_recursive(root):
        files.append(
            {
                "path": str(path.relative_to(root)),
                "size_bytes": path.stat().st_size,
            }
        )
    return files


def make_results_bundle(output_dir: Path, bundle_name: str = "results_bundle.zip") -> Path:
    bundle_path = output_dir / bundle_name
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in list_files_recursive(output_dir):
            if path == bundle_path:
                continue
            archive.write(path, arcname=str(path.relative_to(output_dir)))
    return bundle_path


def project_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path.resolve())

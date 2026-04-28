#!/usr/bin/env python3
from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


DEFAULT_CAPTURE_CHAIN_MANIFEST = (
    "research/prognostics/contracts/mlpe_field_trial_v1/capture_chain/"
    "mlpe_field_trial_capture_chain_manifest_v1.csv"
)

MANIFEST_COLUMNS = [
    "artifact_key",
    "path_kind",
    "static_path",
    "producer_script",
    "producer_output_constant",
    "artifact_name",
    "description",
]


def normalize_text(value: object) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.lower() == "nan" else text


def resolve_path(repo_root: Path, value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def load_manifest(repo_root: Path, manifest_path: str | Path = DEFAULT_CAPTURE_CHAIN_MANIFEST) -> dict[str, dict[str, str]]:
    path = resolve_path(repo_root, manifest_path)
    if not path.exists():
        raise FileNotFoundError(f"missing MLPE chain manifest: {path}")
    with path.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    manifest: dict[str, dict[str, str]] = {}
    for row in rows:
        key = normalize_text(row.get("artifact_key"))
        if not key:
            continue
        manifest[key] = {col: normalize_text(row.get(col)) for col in MANIFEST_COLUMNS}
    return manifest


def load_module_constant(repo_root: Path, producer_script: str, constant_name: str) -> str:
    script_path = resolve_path(repo_root, producer_script)
    if not script_path.exists():
        raise FileNotFoundError(f"missing producer script: {script_path}")
    module_name = f"_mlpe_chain_manifest_{script_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import producer script: {script_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, constant_name):
        raise AttributeError(f"{producer_script} has no constant {constant_name}")
    return normalize_text(getattr(module, constant_name))


def resolve_manifest_artifact(
    repo_root: Path,
    artifact_key: str,
    manifest_path: str | Path = DEFAULT_CAPTURE_CHAIN_MANIFEST,
) -> Path:
    manifest = load_manifest(repo_root, manifest_path)
    if artifact_key not in manifest:
        raise KeyError(f"missing MLPE chain artifact key: {artifact_key}")
    row = manifest[artifact_key]
    static_path = row.get("static_path", "")
    if static_path:
        base = resolve_path(repo_root, static_path)
    else:
        producer_script = row.get("producer_script", "")
        output_constant = row.get("producer_output_constant", "")
        if not producer_script or not output_constant:
            raise ValueError(f"manifest row for {artifact_key} needs static_path or producer output constant")
        base = resolve_path(repo_root, load_module_constant(repo_root, producer_script, output_constant))
    artifact_name = row.get("artifact_name", "")
    return base / artifact_name if artifact_name else base


def resolve_capture_chain_dependency(
    repo_root: Path,
    explicit_path: str | Path | None,
    artifact_key: str,
    manifest_path: str | Path = DEFAULT_CAPTURE_CHAIN_MANIFEST,
) -> Path:
    text = normalize_text(explicit_path)
    if text:
        return resolve_path(repo_root, text)
    return resolve_manifest_artifact(repo_root, artifact_key, manifest_path)

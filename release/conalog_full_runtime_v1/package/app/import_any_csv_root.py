#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timedelta
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recursively scan an arbitrary CSV root, infer site buckets from folder structure, "
            "and stage the files into a normalized <output-root>/<site>/raw layout."
        )
    )
    parser.add_argument("--input-root", type=Path, required=True, help="Root folder to recursively scan for CSV files.")
    parser.add_argument("--output-root", type=Path, required=True, help="Normalized staging root to populate.")
    parser.add_argument("--pattern", default="*.csv", help="Filename glob pattern. Defaults to *.csv.")
    parser.add_argument(
        "--stable-minutes",
        type=int,
        default=0,
        help="Only copy files older than this many minutes. Defaults to 0 (copy all discovered CSVs).",
    )
    parser.add_argument(
        "--clear-output",
        action="store_true",
        help="Delete the output root before staging. Useful for repeated imports.",
    )
    parser.add_argument("--manifest-path", type=Path, default=None, help="Optional JSON manifest output path.")
    parser.add_argument("--env-bat-path", type=Path, default=None, help="Optional .bat env file for wrapper scripts.")
    return parser.parse_args()


def normalize_text(value: object) -> str:
    return str(value).strip()


def normalize_site_name(raw_name: str, fallback: str) -> str:
    text = normalize_text(raw_name)
    text = re.sub(r"[,\r\n\t]+", "_", text)
    text = re.sub(r"\s+", " ", text)
    text = text.strip(" .")
    return text or fallback


def infer_site_name(input_root: Path, csv_path: Path) -> str:
    relative = csv_path.relative_to(input_root)
    parts = list(relative.parts[:-1])
    lowered = [part.lower() for part in parts]

    if "data" in lowered:
        idx = lowered.index("data")
        if idx + 1 < len(parts):
            return normalize_site_name(parts[idx + 1], "site")

    if "raw" in lowered:
        idx = lowered.index("raw")
        if idx - 1 >= 0:
            return normalize_site_name(parts[idx - 1], "site")

    if parts:
        return normalize_site_name(parts[0], normalize_site_name(input_root.name, "site"))

    return normalize_site_name(input_root.name, "site")


def pick_destination_name(target_dir: Path, source_file: Path) -> str:
    candidate = source_file.name
    target = target_dir / candidate
    if not target.exists():
        return candidate
    digest = hashlib.sha256(str(source_file).encode("utf-8")).hexdigest()[:8]
    return f"{source_file.stem}__{digest}{source_file.suffix}"


def copy_file_atomic(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_suffix(destination.suffix + ".__copying__")
    shutil.copy2(source, temp_path)
    temp_path.replace(destination)


def discover_csv_files(input_root: Path, pattern: str) -> list[Path]:
    return sorted(path for path in input_root.rglob(pattern) if path.is_file() and path.suffix.lower() == ".csv")


def write_env_bat(path: Path, payload: dict[str, object]) -> None:
    lines = [
        "@echo off",
        f'set "IMPORTED_DATA_ROOT={payload["output_root"]}"',
        f'set "IMPORTED_SITES={",".join(payload["sites"])}"',
        f'set "IMPORTED_CSV_COUNT={payload["copied_file_count"]}"',
        f'set "IMPORTED_SOURCE_MODE={payload["mode_ko"]}"',
        f'set "IMPORTED_MANIFEST_PATH={payload["manifest_path"]}"',
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_root = args.input_root.expanduser().resolve()
    output_root = args.output_root.expanduser().resolve()
    manifest_path = (
        args.manifest_path.expanduser().resolve()
        if args.manifest_path is not None
        else output_root / "import_any_csv_manifest_v1.json"
    )

    if not input_root.exists():
        raise SystemExit(f"input root does not exist: {input_root}")

    if args.clear_output and output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    csv_files = discover_csv_files(input_root, args.pattern)
    if not csv_files:
        raise SystemExit(f"no csv files found under: {input_root}")

    stable_cutoff = None
    if int(args.stable_minutes) > 0:
        stable_cutoff = datetime.now().astimezone() - timedelta(minutes=int(args.stable_minutes))

    copied_file_count = 0
    skipped_recent_count = 0
    collision_count = 0
    sites_to_files: dict[str, list[str]] = {}
    site_copy_count: dict[str, int] = {}

    for source in csv_files:
        if stable_cutoff is not None:
            last_modified = datetime.fromtimestamp(source.stat().st_mtime).astimezone()
            if last_modified > stable_cutoff:
                skipped_recent_count += 1
                continue

        site = infer_site_name(input_root, source)
        target_dir = output_root / site / "raw"
        destination_name = pick_destination_name(target_dir, source)
        if destination_name != source.name:
            collision_count += 1
        destination = target_dir / destination_name
        copy_file_atomic(source, destination)

        copied_file_count += 1
        sites_to_files.setdefault(site, []).append(source.name)
        site_copy_count[site] = site_copy_count.get(site, 0) + 1

    if copied_file_count == 0:
        raise SystemExit("all csv files were skipped by the stability window")

    payload: dict[str, object] = {
        "generated_at_local": datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z"),
        "input_root": str(input_root),
        "output_root": str(output_root),
        "manifest_path": str(manifest_path),
        "pattern": args.pattern,
        "stable_minutes": int(args.stable_minutes),
        "mode_ko": (
            "stable snapshot import"
            if int(args.stable_minutes) > 0
            else "full recursive import"
        ),
        "sites": sorted(site_copy_count),
        "site_copy_count": {site: int(site_copy_count[site]) for site in sorted(site_copy_count)},
        "copied_file_count": int(copied_file_count),
        "skipped_recent_count": int(skipped_recent_count),
        "collision_count": int(collision_count),
        "site_examples": {
            site: sites_to_files[site][:5]
            for site in sorted(sites_to_files)
        },
        "note_ko": (
            "이 manifest는 임의 폴더 구조의 CSV를 runtime pack이 기대하는 site/raw 구조로 staging 한 결과를 기록한다. "
            "site 이름은 data/<site>/raw, <site>/raw, 또는 최상위 하위 폴더명을 우선 사용한다."
        ),
    }

    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.env_bat_path is not None:
        write_env_bat(args.env_bat_path.expanduser().resolve(), payload)

    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import pandas as pd


DETAIL_OUTPUT_NAME = "repo_mirror_boundary_manifest_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_mirror_boundary_summary_v1.csv"
JSON_OUTPUT_NAME = "repo_mirror_boundary_summary_v1.json"

DETAIL_COLS = [
    "mirror_family",
    "boundary_type",
    "relative_path",
    "source_path",
    "packaged_path",
    "source_exists",
    "packaged_exists",
    "source_sha256",
    "packaged_sha256",
    "content_equal",
    "sync_status",
    "edit_policy",
    "sync_direction",
    "validation_required",
    "note_ko",
]

SUMMARY_COLS = ["kind", "key", "count"]


MIRROR_FAMILIES = [
    {
        "mirror_family": "runtime_research_mirror",
        "boundary_type": "source_to_package_mirror",
        "source_root": Path("research/prognostics"),
        "packaged_root": Path("release/conalog_full_runtime_v1/package/research/prognostics"),
        "edit_policy": "edit_source_first_then_sync_package_mirror",
        "sync_direction": "research/prognostics -> release/conalog_full_runtime_v1/package/research/prognostics",
        "validation_required": "py_compile_source_and_package_mirror_runtime_smoke",
        "note_ko": "runtime package에 포함된 research/prognostics mirror.",
    },
    {
        "mirror_family": "runtime_panel_engine_mirror",
        "boundary_type": "source_to_package_mirror",
        "source_root": Path("pv_ae"),
        "packaged_root": Path("release/conalog_full_runtime_v1/package/pv_ae"),
        "edit_policy": "edit_pv_ae_source_first_then_sync_package_mirror",
        "sync_direction": "pv_ae -> release/conalog_full_runtime_v1/package/pv_ae",
        "validation_required": "py_compile_panel_engine_source_and_package_mirror_runtime_smoke",
        "note_ko": "runtime package에 포함된 pv_ae mirror.",
    },
    {
        "mirror_family": "final_delivery_docs_mirror",
        "boundary_type": "source_doc_to_delivery_mirror",
        "source_root": Path("docs"),
        "packaged_root": Path("release/final_delivery_v1/package/docs"),
        "edit_policy": "edit_source_doc_first_then_sync_final_delivery_doc_when_source_exists",
        "sync_direction": "docs -> release/final_delivery_v1/package/docs",
        "validation_required": "final_delivery_pack_smoke_or_doc_diff_check",
        "note_ko": "final_delivery package docs mirror; some packaged metrics have no docs source pair.",
    },
]

PACKAGE_SURFACES = [
    {
        "mirror_family": "runtime_package_app_surface",
        "boundary_type": "package_surface_without_direct_source_pair",
        "packaged_root": Path("release/conalog_full_runtime_v1/package/app"),
        "edit_policy": "treat_as_package_surface_validate_with_runtime_smoke",
        "sync_direction": "package_surface",
        "validation_required": "py_compile_and_runtime_pack_smoke",
        "note_ko": "packaged runtime app surface. Some files are package-specific entrypoints.",
    },
    {
        "mirror_family": "runtime_packaged_artifacts",
        "boundary_type": "generated_release_artifact",
        "packaged_root": Path("release/conalog_full_runtime_v1/package/artifacts"),
        "edit_policy": "regenerate_preferred_over_manual_edit",
        "sync_direction": "builder/output -> release artifact",
        "validation_required": "artifact_load_check_and_pack_summary",
        "note_ko": "runtime release generated artifacts.",
    },
    {
        "mirror_family": "final_delivery_examples",
        "boundary_type": "generated_delivery_example",
        "packaged_root": Path("release/final_delivery_v1/package/examples"),
        "edit_policy": "regenerate_preferred_over_manual_edit",
        "sync_direction": "builder/output -> final_delivery example",
        "validation_required": "final_delivery_pack_smoke",
        "note_ko": "final_delivery packaged example outputs.",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a source/package mirror boundary manifest so source files, package mirrors, "
            "package-only surfaces, and generated release artifacts are not treated as the same role."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the current project root.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where mirror-boundary outputs will be written.",
    )
    parser.add_argument(
        "--owner-branch",
        default="codex/post-merge-base-j",
        help="Branch or workstream name to record in JSON summary.",
    )
    parser.add_argument(
        "--include-source-only",
        action="store_true",
        help="Also emit source files that are not present in the packaged mirror. Defaults off to keep the manifest package-facing.",
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def iter_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix != ".pyc"
        and path.name != ".DS_Store"
    )


def rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def status_for_pair(source_exists: bool, packaged_exists: bool, content_equal: str) -> str:
    if source_exists and packaged_exists and content_equal == "true":
        return "in_sync"
    if source_exists and packaged_exists:
        return "content_drift"
    if packaged_exists and not source_exists:
        return "packaged_only_no_source_pair"
    if source_exists and not packaged_exists:
        return "source_only_not_packaged"
    return "missing_both"


def build_mirror_rows(repo_root: Path, *, include_source_only: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for family in MIRROR_FAMILIES:
        source_root = repo_root / family["source_root"]
        packaged_root = repo_root / family["packaged_root"]
        relatives = {p.relative_to(packaged_root) for p in iter_files(packaged_root)}
        if include_source_only:
            relatives.update(p.relative_to(source_root) for p in iter_files(source_root))
        for relative in sorted(relatives):
            source_path = source_root / relative
            packaged_path = packaged_root / relative
            source_exists = source_path.exists()
            packaged_exists = packaged_path.exists()
            source_hash = sha256_file(source_path) if source_exists else ""
            packaged_hash = sha256_file(packaged_path) if packaged_exists else ""
            content_equal = "true" if source_exists and packaged_exists and source_hash == packaged_hash else "false"
            rows.append(
                {
                    "mirror_family": family["mirror_family"],
                    "boundary_type": family["boundary_type"],
                    "relative_path": relative.as_posix(),
                    "source_path": rel(source_path, repo_root) if source_exists else "",
                    "packaged_path": rel(packaged_path, repo_root) if packaged_exists else "",
                    "source_exists": str(source_exists).lower(),
                    "packaged_exists": str(packaged_exists).lower(),
                    "source_sha256": source_hash,
                    "packaged_sha256": packaged_hash,
                    "content_equal": content_equal,
                    "sync_status": status_for_pair(source_exists, packaged_exists, content_equal),
                    "edit_policy": family["edit_policy"],
                    "sync_direction": family["sync_direction"],
                    "validation_required": family["validation_required"],
                    "note_ko": family["note_ko"],
                }
            )
    return rows


def build_surface_rows(repo_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for surface in PACKAGE_SURFACES:
        packaged_root = repo_root / surface["packaged_root"]
        for packaged_path in iter_files(packaged_root):
            relative = packaged_path.relative_to(packaged_root)
            rows.append(
                {
                    "mirror_family": surface["mirror_family"],
                    "boundary_type": surface["boundary_type"],
                    "relative_path": relative.as_posix(),
                    "source_path": "",
                    "packaged_path": rel(packaged_path, repo_root),
                    "source_exists": "false",
                    "packaged_exists": "true",
                    "source_sha256": "",
                    "packaged_sha256": sha256_file(packaged_path),
                    "content_equal": "false",
                    "sync_status": surface["boundary_type"],
                    "edit_policy": surface["edit_policy"],
                    "sync_direction": surface["sync_direction"],
                    "validation_required": surface["validation_required"],
                    "note_ko": surface["note_ko"],
                }
            )
    return rows


def build_detail(repo_root: Path, *, include_source_only: bool) -> pd.DataFrame:
    rows = build_mirror_rows(repo_root, include_source_only=include_source_only)
    rows.extend(build_surface_rows(repo_root))
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(detail_df: pd.DataFrame) -> pd.DataFrame:
    counters = {
        "mirror_family": Counter(detail_df["mirror_family"]) if not detail_df.empty else Counter(),
        "boundary_type": Counter(detail_df["boundary_type"]) if not detail_df.empty else Counter(),
        "sync_status": Counter(detail_df["sync_status"]) if not detail_df.empty else Counter(),
        "content_equal": Counter(detail_df["content_equal"]) if not detail_df.empty else Counter(),
        "edit_policy": Counter(detail_df["edit_policy"]) if not detail_df.empty else Counter(),
    }
    rows: list[dict[str, object]] = []
    for kind, counter in counters.items():
        for key, count in sorted(counter.items()):
            rows.append({"kind": kind, "key": key, "count": count})
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def write_json(output_dir: Path, owner_branch: str, include_source_only: bool, detail_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    def counts(kind: str) -> dict[str, int]:
        selected = summary_df.loc[summary_df["kind"].eq(kind)]
        return {str(row["key"]): int(row["count"]) for _, row in selected.iterrows()}

    payload = {
        "owner_branch": owner_branch,
        "source_only_scan_enabled": bool(include_source_only),
        "boundary_row_total": int(len(detail_df)),
        "mirror_family_counts": counts("mirror_family"),
        "sync_status_counts": counts("sync_status"),
        "content_equal_counts": counts("content_equal"),
        "next_lane": "active_builder_entrypoint_registry",
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    detail_df = build_detail(repo_root, include_source_only=args.include_source_only)
    summary_df = build_summary(detail_df)
    detail_df.to_csv(output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json(output_dir, args.owner_branch, args.include_source_only, detail_df, summary_df)


if __name__ == "__main__":
    main()

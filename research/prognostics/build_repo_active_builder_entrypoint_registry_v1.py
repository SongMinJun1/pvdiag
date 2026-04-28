#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd


REGISTRY_OUTPUT_NAME = "repo_active_builder_entrypoint_registry_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_active_builder_entrypoint_summary_v1.csv"
JSON_OUTPUT_NAME = "repo_active_builder_entrypoint_summary_v1.json"

REGISTRY_COLS = [
    "entrypoint_id",
    "script_kind",
    "script_path",
    "stem_key",
    "paired_script_path",
    "pair_status",
    "package_mirror_path",
    "package_mirror_status",
    "doc_ref_count",
    "example_doc_ref",
    "git_status_code",
    "registry_status",
    "recommended_action",
    "validation_command",
    "note_ko",
]

SUMMARY_COLS = ["kind", "key", "count"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a registry for research/prognostics build/smoke entrypoints so active, "
            "paired, packaged, documented, and review-needed scripts are not read as one flat list."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root. Defaults to the current project root.",
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=None,
        help="Docs root to scan for references. Defaults to <repo-root>/docs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where registry outputs will be written.",
    )
    parser.add_argument(
        "--owner-branch",
        default="codex/post-merge-base-j",
        help="Branch or workstream name to record in JSON summary.",
    )
    return parser.parse_args()


def run_git_status(repo_root: Path) -> dict[str, str]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    rows: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        rows[path.strip().strip('"')] = line[:2]
    return rows


def script_kind(path: Path) -> str:
    if path.name.startswith("build_"):
        return "builder"
    if path.name.startswith("smoke_test_"):
        return "smoke"
    return "other"


def stem_key(path: Path) -> str:
    name = path.name
    if name.startswith("build_"):
        return name.removeprefix("build_").removesuffix(".py")
    if name.startswith("smoke_test_"):
        return name.removeprefix("smoke_test_").removesuffix(".py")
    return path.stem


def paired_name(path: Path) -> str:
    key = stem_key(path)
    if script_kind(path) == "builder":
        return f"smoke_test_{key}.py"
    if script_kind(path) == "smoke":
        return f"build_{key}.py"
    return ""


def load_doc_index(docs_root: Path) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    if not docs_root.exists():
        return index
    for doc in sorted(docs_root.glob("*.md")):
        text = doc.read_text(encoding="utf-8")
        index[doc.name] = text
    return index


def doc_refs_for(filename: str, docs: dict[str, str]) -> list[str]:
    refs: list[str] = []
    for doc_name, text in docs.items():
        if filename in text:
            refs.append(doc_name)
    return refs


def classify_registry_status(
    *,
    kind: str,
    pair_exists: bool,
    mirror_exists: bool,
    doc_ref_count: int,
) -> tuple[str, str, str]:
    if mirror_exists:
        return (
            "packaged_runtime_entrypoint",
            "keep_source_first_and_sync_package_mirror",
            "package mirror exists, so source/package boundary applies.",
        )
    if doc_ref_count > 0 and pair_exists:
        return (
            "documented_paired_entrypoint",
            "keep_as_documented_entrypoint",
            "docs reference this entrypoint and the build/smoke pair exists.",
        )
    if doc_ref_count > 0:
        return (
            "documented_unpaired_entrypoint",
            "review_pairing_or_explain_why_unpaired",
            "docs reference this entrypoint but the expected build/smoke pair is missing.",
        )
    if pair_exists:
        return (
            "paired_unreferenced_entrypoint",
            "review_if_current_or_archive",
            "build/smoke pair exists but docs do not currently reference this filename.",
        )
    if kind == "builder":
        return (
            "unpaired_builder_review",
            "pair_with_smoke_or_mark_archive",
            "builder has no expected smoke pair and no current doc reference.",
        )
    return (
        "unpaired_smoke_review",
        "pair_with_builder_or_mark_fixture_only",
        "smoke has no expected builder pair and no current doc reference.",
    )


def build_registry(repo_root: Path, docs_root: Path) -> pd.DataFrame:
    source_root = repo_root / "research" / "prognostics"
    package_root = repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics"
    docs = load_doc_index(docs_root)
    status_map = run_git_status(repo_root)
    scripts = sorted(source_root.glob("build_*.py")) + sorted(source_root.glob("smoke_test_*.py"))
    script_names = {path.name for path in scripts}
    rows: list[dict[str, object]] = []
    for path in scripts:
        kind = script_kind(path)
        key = stem_key(path)
        pair = paired_name(path)
        pair_exists = pair in script_names
        mirror_path = package_root / path.name
        mirror_exists = mirror_path.exists()
        refs = doc_refs_for(path.name, docs)
        rel_path = path.relative_to(repo_root).as_posix()
        registry_status, action, note = classify_registry_status(
            kind=kind,
            pair_exists=pair_exists,
            mirror_exists=mirror_exists,
            doc_ref_count=len(refs),
        )
        validation = f"python3 {rel_path}" if kind == "smoke" else f"python3 -m py_compile {rel_path}"
        rows.append(
            {
                "entrypoint_id": path.stem,
                "script_kind": kind,
                "script_path": rel_path,
                "stem_key": key,
                "paired_script_path": f"research/prognostics/{pair}" if pair else "",
                "pair_status": "pair_exists" if pair_exists else "pair_missing",
                "package_mirror_path": mirror_path.relative_to(repo_root).as_posix() if mirror_exists else "",
                "package_mirror_status": "mirror_exists" if mirror_exists else "no_package_mirror",
                "doc_ref_count": len(refs),
                "example_doc_ref": refs[0] if refs else "",
                "git_status_code": status_map.get(rel_path, ""),
                "registry_status": registry_status,
                "recommended_action": action,
                "validation_command": validation,
                "note_ko": note,
            }
        )
    return pd.DataFrame(rows, columns=REGISTRY_COLS)


def build_summary(registry_df: pd.DataFrame) -> pd.DataFrame:
    counters = {
        "script_kind": Counter(registry_df["script_kind"]) if not registry_df.empty else Counter(),
        "pair_status": Counter(registry_df["pair_status"]) if not registry_df.empty else Counter(),
        "package_mirror_status": Counter(registry_df["package_mirror_status"]) if not registry_df.empty else Counter(),
        "registry_status": Counter(registry_df["registry_status"]) if not registry_df.empty else Counter(),
        "recommended_action": Counter(registry_df["recommended_action"]) if not registry_df.empty else Counter(),
        "git_status_code": Counter(registry_df["git_status_code"]) if not registry_df.empty else Counter(),
    }
    rows: list[dict[str, object]] = []
    for kind, counter in counters.items():
        for key, count in sorted(counter.items()):
            rows.append({"kind": kind, "key": key, "count": count})
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def write_json(output_dir: Path, owner_branch: str, registry_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    def counts(kind: str) -> dict[str, int]:
        selected = summary_df.loc[summary_df["kind"].eq(kind)]
        return {str(row["key"]): int(row["count"]) for _, row in selected.iterrows()}

    payload = {
        "owner_branch": owner_branch,
        "entrypoint_total": int(len(registry_df)),
        "builder_total": int(registry_df["script_kind"].eq("builder").sum()) if not registry_df.empty else 0,
        "smoke_total": int(registry_df["script_kind"].eq("smoke").sum()) if not registry_df.empty else 0,
        "pair_missing_total": int(registry_df["pair_status"].eq("pair_missing").sum()) if not registry_df.empty else 0,
        "package_mirror_total": int(registry_df["package_mirror_status"].eq("mirror_exists").sum()) if not registry_df.empty else 0,
        "documented_total": int(registry_df["doc_ref_count"].gt(0).sum()) if not registry_df.empty else 0,
        "registry_status_counts": counts("registry_status"),
        "recommended_action_counts": counts("recommended_action"),
        "next_lane": "common_cause_synchrony_axis",
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    docs_root = args.docs_root.resolve() if args.docs_root else repo_root / "docs"
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    registry_df = build_registry(repo_root, docs_root)
    summary_df = build_summary(registry_df)
    registry_df.to_csv(output_dir / REGISTRY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json(output_dir, args.owner_branch, registry_df, summary_df)


if __name__ == "__main__":
    main()

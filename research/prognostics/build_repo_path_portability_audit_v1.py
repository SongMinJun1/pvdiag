#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


DETAIL_OUTPUT_NAME = "repo_path_portability_detail_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_path_portability_summary_v1.csv"
FILE_KIND_OUTPUT_NAME = "repo_path_portability_file_kind_v1.csv"
NOTE_OUTPUT_NAME = "repo_path_portability_note_v1.md"
JSON_OUTPUT_NAME = "repo_path_portability_summary_v1.json"

DEFAULT_SCAN_ROOTS = [
    "docs",
    "research",
    "pv_ae",
    "release/conalog_full_runtime_v1",
]

TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    "__pycache__",
}

EXCLUDED_REL_PREFIXES = [
    Path("release/conalog_full_runtime_v1/package/runtime/windows_x64/python"),
    Path("release/conalog_full_runtime_v1/package/runtime/windows_x64/wheelhouse"),
    Path("release/conalog_full_runtime_v1/package/runtime/windows_x64/cache"),
]

PATH_PATTERNS = [
    (
        "worktree_absolute",
        re.compile(r"/Users/b9gc/pvdiag_worktrees/[^\s`'\"),\]}<>]*"),
        "high",
        "stale_transient_worktree_reference",
        "replace_with_repo_relative_or_regenerate_from_repro_command",
    ),
    (
        "repo_absolute",
        re.compile(r"/Users/b9gc/pvdiag(?!_worktrees)(?:/[^\s`'\"),\]}<>]*)?"),
        "medium",
        "local_machine_repo_reference",
        "prefer_repo_relative_path_or_explicit_repo_root_cli_arg",
    ),
    (
        "private_tmp",
        re.compile(r"/private/tmp/[^\s`'\"),\]}<>]*"),
        "medium",
        "volatile_temp_evidence_reference",
        "keep_as_historical_evidence_pointer_or_rebuild_into_named_output_dir",
    ),
]

DETAIL_COLUMNS = [
    "match_kind",
    "risk_level",
    "file_kind",
    "relative_path",
    "line_no",
    "match_index",
    "matched_text",
    "context_excerpt",
    "portability_role",
    "recommended_action",
]

SUMMARY_COLUMNS = ["kind", "key", "count"]
FILE_KIND_COLUMNS = ["file_kind", "match_kind", "files", "matches"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Scan repo-facing docs/research/runtime surfaces for local absolute paths "
            "and volatile /private/tmp evidence references."
        )
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[2],
        help="Repository root to scan. Defaults to this checkout.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for portability audit outputs.",
    )
    parser.add_argument(
        "--scan-root",
        action="append",
        dest="scan_roots",
        default=None,
        help="Repo-relative root to scan. May be repeated. Defaults to docs/research/pv_ae/release runtime.",
    )
    parser.add_argument(
        "--max-file-bytes",
        type=int,
        default=5_000_000,
        help="Skip individual text-like files larger than this byte limit. Defaults to 5MB.",
    )
    parser.add_argument(
        "--top-files",
        type=int,
        default=25,
        help="Number of top files by match count to include in the markdown note.",
    )
    return parser.parse_args()


def repo_rel(path: Path, repo_root: Path) -> str:
    return path.relative_to(repo_root).as_posix()


def starts_with_path(path: Path, prefix: Path) -> bool:
    return path == prefix or prefix in path.parents


def should_skip_path(path: Path, repo_root: Path, max_file_bytes: int) -> str:
    rel = path.relative_to(repo_root)
    if any(part in EXCLUDED_DIR_NAMES for part in rel.parts):
        return "excluded_dir"
    if any(starts_with_path(rel, prefix) for prefix in EXCLUDED_REL_PREFIXES):
        return "excluded_runtime_payload"
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return "non_text_suffix"
    try:
        if path.stat().st_size > max_file_bytes:
            return "file_too_large"
    except OSError:
        return "stat_error"
    return ""


def iter_scan_files(repo_root: Path, scan_roots: list[str], max_file_bytes: int) -> tuple[list[Path], Counter[str]]:
    files: list[Path] = []
    skipped: Counter[str] = Counter()
    for root_text in scan_roots:
        root = repo_root / root_text
        if not root.exists():
            skipped["missing_scan_root"] += 1
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            reason = should_skip_path(path, repo_root, max_file_bytes)
            if reason:
                skipped[reason] += 1
                continue
            files.append(path)
    return files, skipped


def classify_file_kind(relative_path: str) -> str:
    if relative_path.startswith("docs/"):
        return "repo_doc"
    if relative_path.startswith("research/prognostics/"):
        return "research_prognostics"
    if relative_path.startswith("research/"):
        return "research_other"
    if relative_path.startswith("pv_ae/"):
        return "source_engine"
    if relative_path.startswith("release/conalog_full_runtime_v1/package/_share/"):
        return "runtime_package_share_output"
    if relative_path.startswith("release/conalog_full_runtime_v1/package/artifacts/"):
        return "runtime_package_artifact"
    if relative_path.startswith("release/conalog_full_runtime_v1/package/runtime/"):
        return "runtime_embedded_payload"
    if relative_path.startswith("release/conalog_full_runtime_v1/package/"):
        return "runtime_package_surface"
    if relative_path.startswith("release/conalog_full_runtime_v1/"):
        return "runtime_release_surface"
    return "other"


def excerpt_line(line: str, start: int, end: int, radius: int = 90) -> str:
    left = max(0, start - radius)
    right = min(len(line), end + radius)
    excerpt = line[left:right].strip()
    return " ".join(excerpt.split())


def scan_file(path: Path, repo_root: Path) -> list[dict[str, object]]:
    relative = repo_rel(path, repo_root)
    file_kind = classify_file_kind(relative)
    rows: list[dict[str, object]] = []
    match_index = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for line_no, line in enumerate(lines, start=1):
        for match_kind, pattern, risk_level, portability_role, recommended_action in PATH_PATTERNS:
            for match in pattern.finditer(line):
                match_index += 1
                rows.append(
                    {
                        "match_kind": match_kind,
                        "risk_level": risk_level,
                        "file_kind": file_kind,
                        "relative_path": relative,
                        "line_no": line_no,
                        "match_index": match_index,
                        "matched_text": match.group(0),
                        "context_excerpt": excerpt_line(line, match.start(), match.end()),
                        "portability_role": portability_role,
                        "recommended_action": recommended_action,
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def build_summary_rows(
    detail_rows: list[dict[str, object]],
    skipped: Counter[str],
    scan_file_count: int,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {"kind": "total", "key": "matches", "count": len(detail_rows)},
        {"kind": "total", "key": "scanned_files", "count": scan_file_count},
    ]
    for key, count in sorted(Counter(str(row["match_kind"]) for row in detail_rows).items()):
        rows.append({"kind": "match_kind", "key": key, "count": count})
    for key, count in sorted(Counter(str(row["risk_level"]) for row in detail_rows).items()):
        rows.append({"kind": "risk_level", "key": key, "count": count})
    for key, count in sorted(Counter(str(row["file_kind"]) for row in detail_rows).items()):
        rows.append({"kind": "file_kind", "key": key, "count": count})
    file_counts = Counter(str(row["relative_path"]) for row in detail_rows)
    for key, count in sorted(file_counts.items(), key=lambda x: (-x[1], x[0]))[:50]:
        rows.append({"kind": "top_file", "key": key, "count": count})
    for key, count in sorted(skipped.items()):
        rows.append({"kind": "skipped", "key": key, "count": count})
    return rows


def build_file_kind_rows(detail_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for row in detail_rows:
        key = (str(row["file_kind"]), str(row["match_kind"]))
        bucket = grouped.setdefault(
            key,
            {
                "file_kind": key[0],
                "match_kind": key[1],
                "files_set": set(),
                "matches": 0,
            },
        )
        bucket["files_set"].add(str(row["relative_path"]))
        bucket["matches"] = int(bucket["matches"]) + 1
    out: list[dict[str, object]] = []
    for item in grouped.values():
        out.append(
            {
                "file_kind": item["file_kind"],
                "match_kind": item["match_kind"],
                "files": len(item["files_set"]),
                "matches": item["matches"],
            }
        )
    return sorted(
        out,
        key=lambda row: (
            -int(row["matches"]),
            str(row["file_kind"]),
            str(row["match_kind"]),
        ),
    )


def build_note(
    detail_rows: list[dict[str, object]],
    summary_rows: list[dict[str, object]],
    output_dir: Path,
    repo_root: Path,
    top_files: int,
) -> str:
    by_kind = Counter(str(row["match_kind"]) for row in detail_rows)
    by_risk = Counter(str(row["risk_level"]) for row in detail_rows)
    top = [
        row
        for row in summary_rows
        if row["kind"] == "top_file"
    ][:top_files]

    lines = [
        "# Repo Path Portability Audit V1",
        "",
        "## Purpose",
        "- Detect local absolute repo paths, transient worktree paths, and volatile "
        "`/private/tmp` evidence references before they leak into stable runtime/package surfaces.",
        "- This is an audit/reporting guard only. It does not rewrite historical "
        "evidence pointers and does not change runtime semantics.",
        "",
        "## Scope",
        f"- repo_root: `{repo_root}`",
        f"- detail: `{output_dir / DETAIL_OUTPUT_NAME}`",
        f"- summary: `{output_dir / SUMMARY_OUTPUT_NAME}`",
        f"- file_kind_summary: `{output_dir / FILE_KIND_OUTPUT_NAME}`",
        "",
        "## Counts",
        f"- total_matches: {len(detail_rows)}",
    ]
    for key in sorted(by_kind):
        lines.append(f"- {key}: {by_kind[key]}")
    for key in sorted(by_risk):
        lines.append(f"- risk_{key}: {by_risk[key]}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "- `repo_absolute` usually means a command, doc link, or generated metadata "
            "still depends on `/Users/b9gc/pvdiag` instead of a repo-relative path or "
            "explicit `--repo-root`.",
            "- `worktree_absolute` is the highest cleanup priority because old "
            "`/Users/b9gc/pvdiag_worktrees/...` paths are intentionally transient.",
            "- `private_tmp` often points to historical evidence outputs. Do not bulk "
            "rewrite these unless the replacement artifact and repro command are recorded.",
            "- Runtime pack JSON metadata absolute-path churn was already handled separately; "
            "this audit keeps the remaining docs/research/package surface visible.",
            "",
            "## Top Files",
        ]
    )
    if not top:
        lines.append("- No path portability matches found.")
    else:
        for row in top:
            lines.append(f"- `{row['key']}`: {row['count']}")
    lines.extend(
        [
            "",
            "## Next Action",
            "- Use this output as a triage map: fix live commands and stale worktree paths "
            "first, preserve historical `/private/tmp` evidence references unless a stable "
            "artifact replacement exists.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    scan_roots = args.scan_roots or DEFAULT_SCAN_ROOTS

    files, skipped = iter_scan_files(repo_root, scan_roots, args.max_file_bytes)
    detail_rows: list[dict[str, object]] = []
    for path in files:
        detail_rows.extend(scan_file(path, repo_root))

    summary_rows = build_summary_rows(detail_rows, skipped, len(files))
    file_kind_rows = build_file_kind_rows(detail_rows)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / DETAIL_OUTPUT_NAME, detail_rows, DETAIL_COLUMNS)
    write_csv(output_dir / SUMMARY_OUTPUT_NAME, summary_rows, SUMMARY_COLUMNS)
    write_csv(output_dir / FILE_KIND_OUTPUT_NAME, file_kind_rows, FILE_KIND_COLUMNS)
    (output_dir / NOTE_OUTPUT_NAME).write_text(
        build_note(detail_rows, summary_rows, output_dir, repo_root, args.top_files),
        encoding="utf-8",
    )
    (output_dir / JSON_OUTPUT_NAME).write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "repo_root": str(repo_root),
                "scan_roots": scan_roots,
                "outputs": {
                    "detail": str(output_dir / DETAIL_OUTPUT_NAME),
                    "summary": str(output_dir / SUMMARY_OUTPUT_NAME),
                    "file_kind_summary": str(output_dir / FILE_KIND_OUTPUT_NAME),
                    "note": str(output_dir / NOTE_OUTPUT_NAME),
                },
                "match_kind_counts": dict(Counter(str(row["match_kind"]) for row in detail_rows)),
                "risk_level_counts": dict(Counter(str(row["risk_level"]) for row in detail_rows)),
                "skipped_counts": dict(skipped),
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"wrote {len(detail_rows)} rows to {output_dir / DETAIL_OUTPUT_NAME}")


if __name__ == "__main__":
    main()

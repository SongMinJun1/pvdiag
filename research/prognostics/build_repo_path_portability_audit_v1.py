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
SELF_LITERAL_SKIP_MARKER = "pp-self"

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
        re.compile(r"/Users/b9gc/pvdiag_worktrees/[^\s`'\"),\]}<>]*"),  # pp-self
        "high",
        "stale_transient_worktree_reference",
        "replace_with_repo_relative_or_regenerate_from_repro_command",
    ),
    (
        "repo_absolute",
        re.compile(r"/Users/b9gc/pvdiag(?!_worktrees)(?:/[^\s`'\"),\]}<>]*)?"),  # pp-self
        "medium",
        "local_machine_repo_reference",
        "prefer_repo_relative_path_or_explicit_repo_root_cli_arg",
    ),
    (
        "private_tmp",
        re.compile(r"/private/tmp/[^\s`'\"),\]}<>]*"),  # pp-self
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
    "match_role",
    "triage_priority",
    "triage_action",
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


def classify_temp_default_match(context: str) -> dict[str, str]:
    if "default_output_dir" in context or "--output-dir" in context:
        return {
            "match_role": "research_temp_output_default_reference",
            "triage_priority": "p2_temp_output_default_reference",
            "triage_action": "prefer_required_cli_output_dir_for_reusable_builders",
        }
    if "default_" in context and any(
        key in context
        for key in (
            "input",
            "validation",
            "schema",
            "allowed_values",
            "packet",
            "capture",
            "watchlist",
            "preflight",
            "checklist",
            "clearance",
            "attachment",
            "request",
            "guard",
            "candidate",
            "summary",
            "materialization",
            "sidecar",
            "runtime_root",
            "br107_root",
            "br108_root",
        )
    ):
        return {
            "match_role": "research_temp_input_artifact_default_reference",
            "triage_priority": "p1_temp_input_default_reference",
            "triage_action": "require_explicit_input_or_resolve_from_tracked_manifest",
        }
    if "default_" in context and "dir" in context:
        return {
            "match_role": "research_temp_directory_default_reference",
            "triage_priority": "p1_temp_input_default_reference",
            "triage_action": "inspect_directory_role_before_replacing_default",
        }
    if "default=path(" in context or "default=\"/private/tmp/" in context:
        return {
            "match_role": "research_temp_cli_default_reference",
            "triage_priority": "p2_temp_cli_default_reference",
            "triage_action": "inspect_cli_argument_role_before_replacing_default",
        }
    return {
        "match_role": "research_temp_default_reference",
        "triage_priority": "p1_live_temp_default_reference",
        "triage_action": "replace_default_with_required_input_or_cli_output_dir",
    }


def classify_private_tmp_match(relative_path: str, context_excerpt: str, file_kind: str) -> dict[str, str]:
    context = context_excerpt.lower()
    if file_kind == "repo_doc":
        return {
            "match_role": "historical_temp_evidence_reference",
            "triage_priority": "p2_historical_evidence_reference",
            "triage_action": "preserve_if_historical_evidence_else_materialize_stable_output",
        }
    if relative_path.startswith("research/prognostics/smoke_test_"):
        return {
            "match_role": "test_fixture_temp_reference",
            "triage_priority": "p3_test_fixture_reference",
            "triage_action": "preserve_test_fixture_unless_it_masks_live_default",
        }
    if "startswith(\"/private/tmp/" in context or "startswith('/private/tmp/" in context:  # pp-self
        return {
            "match_role": "intentional_temp_path_detection_literal",
            "triage_priority": "p3_intentional_detection_literal",
            "triage_action": "preserve_detection_literal_or_mark_self_noise_if_scanner_related",
        }
    if "default_" in context or "default=path(" in context or "default=\"/private/tmp/" in context:  # pp-self
        return classify_temp_default_match(context)
    if "primary_artifact_path" in context:
        return {
            "match_role": "embedded_manifest_temp_artifact_reference",
            "triage_priority": "p2_embedded_manifest_reference",
            "triage_action": "preserve_until_manifest_is_rebuilt_with_stable_artifact_paths",
        }
    if context.strip().startswith("\"--") or context.strip().startswith("'--") or "python3 " in context:
        return {
            "match_role": "embedded_repro_command_temp_reference",
            "triage_priority": "p2_historical_repro_reference",
            "triage_action": "preserve_if_historical_repro_else_refresh_to_repo_relative",
        }
    return {
        "match_role": "temp_reference_in_research_code",
        "triage_priority": "p1_live_temp_reference",
        "triage_action": "inspect_then_replace_with_cli_arg_or_manifest_input",
    }


def classify_match(
    match_kind: str,
    matched_text: str,
    file_kind: str,
    relative_path: str,
    context_excerpt: str,
) -> dict[str, str]:
    if match_kind == "worktree_absolute":
        return {
            "match_role": "stale_worktree_reference",
            "triage_priority": "p0_stale_worktree",
            "triage_action": "replace_with_repo_relative_or_regenerate_from_repro_command",
        }

    if match_kind == "private_tmp":
        return classify_private_tmp_match(relative_path, context_excerpt, file_kind)

    if match_kind != "repo_absolute":
        return {
            "match_role": "unclassified_path_reference",
            "triage_priority": "p2_review",
            "triage_action": "inspect_before_rewrite",
        }

    repo_priority = "p1_repo_absolute_live_surface"
    repo_action_override = ""
    if file_kind == "repo_doc":
        repo_priority = "p2_historical_repro_reference"
        repo_action_override = "preserve_if_historical_repro_else_refresh_to_repo_relative"

    repo_suffix = matched_text.removeprefix("/Users/b9gc/pvdiag").lstrip("/")  # pp-self
    if not repo_suffix:
        return {
            "match_role": "repo_root_absolute_reference",
            "triage_priority": repo_priority,
            "triage_action": repo_action_override or "prefer_explicit_repo_root_or_pwd",
        }
    if repo_suffix.startswith("data/"):
        return {
            "match_role": "repo_data_absolute_reference",
            "triage_priority": repo_priority,
            "triage_action": repo_action_override
            or "prefer_data_or_explicit_data_root_when_command_is_current",
        }
    if repo_suffix.startswith("docs/"):
        return {
            "match_role": "repo_doc_absolute_reference",
            "triage_priority": "p3_doc_reference",
            "triage_action": "prefer_repo_relative_doc_path_when_touching_doc",
        }
    if repo_suffix.startswith("research/"):
        return {
            "match_role": "repo_research_absolute_reference",
            "triage_priority": repo_priority,
            "triage_action": repo_action_override
            or "prefer_repo_relative_or_repo_root_arg_for_live_research_command",
        }
    if repo_suffix.startswith("release/"):
        return {
            "match_role": "repo_release_absolute_reference",
            "triage_priority": repo_priority,
            "triage_action": repo_action_override
            or "prefer_repo_relative_release_path_or_runtime_root_arg",
        }
    if repo_suffix.startswith("pv_ae/"):
        return {
            "match_role": "repo_source_absolute_reference",
            "triage_priority": repo_priority,
            "triage_action": repo_action_override
            or "prefer_repo_relative_source_path_or_package_lookup",
        }
    return {
        "match_role": "repo_absolute_reference",
        "triage_priority": repo_priority,
        "triage_action": repo_action_override or "prefer_repo_relative_path_or_explicit_repo_root_cli_arg",
    }


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
        if SELF_LITERAL_SKIP_MARKER in line:
            continue
        for match_kind, pattern, risk_level, portability_role, recommended_action in PATH_PATTERNS:
            for match in pattern.finditer(line):
                match_index += 1
                excerpt = excerpt_line(line, match.start(), match.end())
                triage = classify_match(match_kind, match.group(0), file_kind, relative, excerpt)
                rows.append(
                    {
                        "match_kind": match_kind,
                        "risk_level": risk_level,
                        "file_kind": file_kind,
                        "relative_path": relative,
                        "line_no": line_no,
                        "match_index": match_index,
                        "matched_text": match.group(0),
                        "context_excerpt": excerpt,
                        "match_role": triage["match_role"],
                        "triage_priority": triage["triage_priority"],
                        "triage_action": triage["triage_action"],
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
    for key, count in sorted(Counter(str(row["match_role"]) for row in detail_rows).items()):
        rows.append({"kind": "match_role", "key": key, "count": count})
    for key, count in sorted(Counter(str(row["triage_priority"]) for row in detail_rows).items()):
        rows.append({"kind": "triage_priority", "key": key, "count": count})
    for key, count in sorted(Counter(str(row["triage_action"]) for row in detail_rows).items()):
        rows.append({"kind": "triage_action", "key": key, "count": count})
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
    by_role = Counter(str(row["match_role"]) for row in detail_rows)
    by_priority = Counter(str(row["triage_priority"]) for row in detail_rows)
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
        "`/private/tmp` evidence references before they leak into stable runtime/package surfaces.",  # pp-self
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
    lines.extend(["", "## Triage Priorities"])
    if not by_priority:
        lines.append("- No triage priorities found.")
    else:
        for key in sorted(by_priority):
            lines.append(f"- {key}: {by_priority[key]}")
    lines.extend(["", "## Triage Roles"])
    if not by_role:
        lines.append("- No triage roles found.")
    else:
        for key in sorted(by_role):
            lines.append(f"- {key}: {by_role[key]}")
    lines.extend(
        [
            "",
            "## Interpretation",
            "- `repo_absolute` usually means a command, doc link, or generated metadata "
            "still depends on `/Users/b9gc/pvdiag` instead of a repo-relative path or ",  # pp-self
            "explicit `--repo-root`.",
            "- `worktree_absolute` is the highest cleanup priority because old "
            "`/Users/b9gc/pvdiag_worktrees/...` paths are intentionally transient.",  # pp-self
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
            "artifact replacement exists.",  # pp-self
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
                "match_role_counts": dict(Counter(str(row["match_role"]) for row in detail_rows)),
                "triage_priority_counts": dict(
                    Counter(str(row["triage_priority"]) for row in detail_rows)
                ),
                "triage_action_counts": dict(
                    Counter(str(row["triage_action"]) for row in detail_rows)
                ),
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

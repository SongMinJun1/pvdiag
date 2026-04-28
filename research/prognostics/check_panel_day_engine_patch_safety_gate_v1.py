#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import subprocess
from pathlib import Path

import pandas as pd


ENGINE_SOURCE = "pv_ae/panel_day_engine.py"
ENGINE_PACKAGE = "release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py"
DETAIL_OUTPUT_NAME = "panel_day_engine_patch_safety_gate_v1.csv"
SUMMARY_OUTPUT_NAME = "panel_day_engine_patch_safety_gate_summary_v1.csv"
VALIDATION_COMMANDS = [
    "python3 -m py_compile pv_ae/panel_day_engine.py",
    "python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py",
    "python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/panel_engine_patch_safety_rerun --sites conalog --prefer-existing-site-outs on",
]
RELATED_TERMS = [
    "panel_day_engine",
    "panel engine",
    "pv_ae/panel_day_engine.py",
    "panel_engine_patch_safety_gate",
]
DETAIL_COLS = [
    "gate_id",
    "severity",
    "applies_flag",
    "pass_flag",
    "status",
    "evidence_paths",
    "requirement",
    "remediation",
]


@dataclass(frozen=True)
class ChangedEntry:
    path: str
    status: str

    @property
    def deleted(self) -> bool:
        return self.status.upper().startswith("D")


SUMMARY_COLS = [
    "engine_change_detected",
    "source_engine_changed",
    "package_engine_changed",
    "changed_path_count",
    "pass_gate_count",
    "fail_gate_count",
    "warn_gate_count",
    "not_applicable_gate_count",
    "overall_status",
    "required_validation_commands",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check whether a proposed pv_ae/panel_day_engine.py patch has the minimum "
            "documentation, shadow, smoke, mirror, and validation safety rails."
        )
    )
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--base-ref",
        default="HEAD",
        help="Git ref used when --changed-paths-file is not provided. Defaults to HEAD.",
    )
    parser.add_argument(
        "--changed-paths-file",
        type=Path,
        default=None,
        help="Optional newline-delimited path list for synthetic or precomputed checks.",
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    return parser.parse_args()


def normalize_path(value: str) -> str:
    return value.strip().lstrip("./")


def parse_changed_entry(line: str, default_status: str = "M") -> ChangedEntry | None:
    value = line.strip()
    if not value:
        return None
    parts = value.split("\t")
    if len(parts) >= 2 and parts[0] and parts[0][0].upper() in {"A", "C", "D", "M", "R", "T", "U"}:
        status = parts[0].upper()
        path = parts[-1]
    else:
        status = default_status
        path = value
    path = normalize_path(path)
    if not path:
        return None
    return ChangedEntry(path=path, status=status)


def read_changed_entries(args: argparse.Namespace) -> list[ChangedEntry]:
    if args.changed_paths_file is not None:
        if not args.changed_paths_file.exists():
            raise SystemExit(f"missing changed paths file: {args.changed_paths_file}")
        entries = [
            entry
            for line in args.changed_paths_file.read_text(encoding="utf-8").splitlines()
            if (entry := parse_changed_entry(line)) is not None
        ]
        return sorted({entry.path: entry for entry in entries}.values(), key=lambda entry: entry.path)

    entries_by_path: dict[str, ChangedEntry] = {}
    commands = [
        (["git", "diff", "--name-status", args.base_ref, "--"], "M"),
        (["git", "ls-files", "--others", "--exclude-standard"], "A"),
    ]
    for command, default_status in commands:
        completed = subprocess.run(command, cwd=args.repo_root, text=True, capture_output=True)
        if completed.returncode != 0:
            raise SystemExit(completed.stderr or completed.stdout)
        for line in completed.stdout.splitlines():
            entry = parse_changed_entry(line, default_status=default_status)
            if entry is not None:
                entries_by_path[entry.path] = entry
    return sorted(entries_by_path.values(), key=lambda entry: entry.path)


def match_paths(paths: list[str], predicate) -> list[str]:
    return sorted(path for path in paths if predicate(path))


def is_required_evidence_path(path: str) -> bool:
    return (
        (path.startswith("research/prognostics/build_") and path.endswith(".py"))
        or path.startswith("research/prognostics/smoke_test_")
        or path.startswith("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_")
        or path.startswith("docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_")
        or path
        in {
            ENGINE_SOURCE,
            ENGINE_PACKAGE,
            "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md",
            "docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md",
            "ONEPAGER.md",
            "data_dictionary_paper.md",
        }
    )


def existing_paths(repo_root: Path, paths: list[str]) -> list[str]:
    return sorted(path for path in paths if (repo_root / path).is_file())


def related_existing_paths(repo_root: Path, paths: list[str]) -> list[str]:
    matched: list[str] = []
    for path in existing_paths(repo_root, paths):
        file_path = repo_root / path
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            content = ""
        haystack = f"{path}\n{content}".lower()
        if any(term.lower() in haystack for term in RELATED_TERMS):
            matched.append(path)
    return sorted(matched)


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def row(
    gate_id: str,
    severity: str,
    applies: bool,
    passed: bool,
    evidence: list[str],
    requirement: str,
    remediation: str,
) -> dict[str, object]:
    if not applies:
        status = "not_applicable"
        pass_flag = 1
    elif passed:
        status = "pass"
        pass_flag = 1
    else:
        status = "fail" if severity == "required" else "warn"
        pass_flag = 0 if severity == "required" else 1
    return {
        "gate_id": gate_id,
        "severity": severity,
        "applies_flag": int(applies),
        "pass_flag": pass_flag,
        "status": status,
        "evidence_paths": "|".join(evidence),
        "requirement": requirement,
        "remediation": remediation,
    }


def build_detail(entries: list[ChangedEntry], repo_root: Path) -> pd.DataFrame:
    paths = sorted({entry.path for entry in entries})
    active_paths = sorted({entry.path for entry in entries if not entry.deleted})
    deleted_paths = sorted({entry.path for entry in entries if entry.deleted})
    source_engine = ENGINE_SOURCE in paths
    package_engine = ENGINE_PACKAGE in paths
    active_source_engine = ENGINE_SOURCE in active_paths
    active_package_engine = ENGINE_PACKAGE in active_paths
    engine_changed = source_engine or package_engine
    branch_docs = related_existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p.startswith("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_") and p.endswith(".md")),
    )
    decision_logs = related_existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p.startswith("docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_") and p.endswith(".md")),
    )
    shadow_builders = related_existing_paths(
        repo_root,
        match_paths(
            active_paths,
            lambda p: p.startswith("research/prognostics/build_")
            and p.endswith(".py")
            and any(token in Path(p).name for token in ["shadow", "simulation", "safety", "gate", "forensic", "audit", "gap", "seed", "review"]),
        ),
    )
    smoke_tests = related_existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p.startswith("research/prognostics/smoke_test_") and p.endswith(".py")),
    )
    active_register = existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p == "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md"),
    )
    gate7 = existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p == "docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md"),
    )
    public_docs = related_existing_paths(
        repo_root,
        match_paths(active_paths, lambda p: p in {"ONEPAGER.md", "data_dictionary_paper.md"} or p.startswith("paper_pack/")),
    )
    data_paths = match_paths(active_paths, lambda p: p.startswith("data/") and ("/raw/" in p or "/out/" in p))
    deleted_gate_evidence = match_paths(
        deleted_paths,
        is_required_evidence_path,
    )
    source_hash = sha256_file(repo_root / ENGINE_SOURCE)
    package_hash = sha256_file(repo_root / ENGINE_PACKAGE)
    source_package_hash_equal = source_hash is not None and package_hash is not None and source_hash == package_hash

    rows = [
        row(
            "G00_engine_change_detection",
            "info",
            True,
            True,
            [path for path in paths if path in {ENGINE_SOURCE, ENGINE_PACKAGE}],
            "Detect whether the source or packaged panel engine is touched.",
            "No action needed; downstream gates apply only when engine code changes.",
        ),
        row(
            "G01_branch_doc_present",
            "required",
            engine_changed,
            bool(branch_docs),
            branch_docs,
            "Engine patches need a branch note explaining intent, evidence, and safety boundary.",
            "Add docs/OPS_CONALOG_RUNTIME_BRANCH_BR_YYYYMMDD_NNN_*.md.",
        ),
        row(
            "G02_decision_log_present",
            "required",
            engine_changed,
            bool(decision_logs),
            decision_logs,
            "Engine patches need a decision log that records why the change is allowed.",
            "Add docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_YYYYMMDD_NNN_V1.md.",
        ),
        row(
            "G03_shadow_or_safety_builder_present",
            "required",
            engine_changed,
            bool(shadow_builders),
            shadow_builders,
            "Before or with an engine patch, include a reproducible shadow/safety/audit builder.",
            "Add a research/prognostics/build_* shadow, safety, gate, audit, gap, seed, or review script.",
        ),
        row(
            "G04_smoke_test_present",
            "required",
            engine_changed,
            bool(smoke_tests),
            smoke_tests,
            "Engine patches need a synthetic smoke test that proves the intended contract.",
            "Add or update a research/prognostics/smoke_test_*.py file.",
        ),
        row(
            "G05_active_register_updated",
            "required",
            engine_changed,
            bool(active_register),
            active_register,
            "Engine patches need the active branch register updated so the roadmap does not drift.",
            "Update docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md.",
        ),
        row(
            "G06_gate7_order_updated",
            "required",
            engine_changed,
            bool(gate7),
            gate7,
            "Engine patches need Gate 7 order updated or reaffirmed.",
            "Update docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md.",
        ),
        row(
            "G07_public_behavior_doc_present",
            "required",
            engine_changed,
            bool(public_docs),
            public_docs,
            "Algorithm behavior changes must update ONEPAGER.md, data_dictionary_paper.md, or paper_pack docs.",
            "Update ONEPAGER.md or the paper/data-dictionary documentation, or split the patch until behavior change is absent.",
        ),
        row(
            "G08_source_package_pair_changed_together",
            "required",
            engine_changed,
            active_source_engine and active_package_engine,
            [path for path in paths if path in {ENGINE_SOURCE, ENGINE_PACKAGE}],
            "Source and packaged panel engines must move together; package-only and source-only drift are both blocked.",
            f"Update both {ENGINE_SOURCE} and {ENGINE_PACKAGE}, or split the patch with an explicit non-release decision.",
        ),
        row(
            "G09_source_package_content_equal",
            "required",
            active_source_engine and active_package_engine,
            source_package_hash_equal,
            [path for path in paths if path in {ENGINE_SOURCE, ENGINE_PACKAGE}],
            "Source and packaged panel engines must be byte-identical after the patch.",
            "Copy the accepted source engine into the packaged mirror, then rerun the safety gate.",
        ),
        row(
            "G10_no_deleted_required_evidence",
            "required",
            engine_changed and bool(deleted_gate_evidence),
            not deleted_gate_evidence,
            deleted_gate_evidence,
            "Deleted safety evidence, docs, smoke, public behavior docs, or engine files cannot satisfy the gate.",
            "Restore the required evidence file or replace it with a related active file in the same patch.",
        ),
        row(
            "G11_no_large_data_paths",
            "required",
            engine_changed or bool(data_paths),
            not data_paths,
            data_paths,
            "Engine safety patches must not bundle data/<site>/raw or data/<site>/out files.",
            "Remove large/generated data paths from the patch and keep outputs in /private/tmp or a small artifact note.",
        ),
    ]
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(entries: list[ChangedEntry], detail_df: pd.DataFrame) -> pd.DataFrame:
    paths = sorted({entry.path for entry in entries})
    source_engine = ENGINE_SOURCE in paths
    package_engine = ENGINE_PACKAGE in paths
    engine_changed = source_engine or package_engine
    fail_count = int(detail_df["status"].eq("fail").sum())
    warn_count = int(detail_df["status"].eq("warn").sum())
    overall = "pass" if fail_count == 0 else "fail"
    return pd.DataFrame(
        [
            {
                "engine_change_detected": int(engine_changed),
                "source_engine_changed": int(source_engine),
                "package_engine_changed": int(package_engine),
                "changed_path_count": int(len(paths)),
                "pass_gate_count": int(detail_df["status"].eq("pass").sum()),
                "fail_gate_count": fail_count,
                "warn_gate_count": warn_count,
                "not_applicable_gate_count": int(detail_df["status"].eq("not_applicable").sum()),
                "overall_status": overall,
                "required_validation_commands": " && ".join(VALIDATION_COMMANDS),
            }
        ],
        columns=SUMMARY_COLS,
    )


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    entries = read_changed_entries(args)
    detail_df = build_detail(entries, args.repo_root)
    summary_df = build_summary(entries, detail_df)
    detail_df.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()

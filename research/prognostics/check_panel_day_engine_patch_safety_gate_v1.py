#!/usr/bin/env python3
from __future__ import annotations

import argparse
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


def read_changed_paths(args: argparse.Namespace) -> list[str]:
    if args.changed_paths_file is not None:
        if not args.changed_paths_file.exists():
            raise SystemExit(f"missing changed paths file: {args.changed_paths_file}")
        paths = [normalize_path(line) for line in args.changed_paths_file.read_text(encoding="utf-8").splitlines()]
        return sorted({path for path in paths if path})

    paths: set[str] = set()
    commands = [
        ["git", "diff", "--name-only", args.base_ref, "--"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ]
    for command in commands:
        completed = subprocess.run(command, cwd=args.repo_root, text=True, capture_output=True)
        if completed.returncode != 0:
            raise SystemExit(completed.stderr or completed.stdout)
        for line in completed.stdout.splitlines():
            path = normalize_path(line)
            if path:
                paths.add(path)
    return sorted(paths)


def match_paths(paths: list[str], predicate) -> list[str]:
    return sorted(path for path in paths if predicate(path))


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


def build_detail(paths: list[str]) -> pd.DataFrame:
    source_engine = ENGINE_SOURCE in paths
    package_engine = ENGINE_PACKAGE in paths
    engine_changed = source_engine or package_engine
    branch_docs = match_paths(paths, lambda p: p.startswith("docs/OPS_CONALOG_RUNTIME_BRANCH_BR_") and p.endswith(".md"))
    decision_logs = match_paths(paths, lambda p: p.startswith("docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_") and p.endswith(".md"))
    shadow_builders = match_paths(
        paths,
        lambda p: p.startswith("research/prognostics/build_")
        and p.endswith(".py")
        and any(token in Path(p).name for token in ["shadow", "simulation", "safety", "gate", "forensic", "audit", "gap", "seed", "review"]),
    )
    smoke_tests = match_paths(paths, lambda p: p.startswith("research/prognostics/smoke_test_") and p.endswith(".py"))
    active_register = match_paths(paths, lambda p: p == "docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md")
    gate7 = match_paths(paths, lambda p: p == "docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md")
    public_docs = match_paths(paths, lambda p: p in {"ONEPAGER.md", "data_dictionary_paper.md"} or p.startswith("paper_pack/"))
    data_paths = match_paths(paths, lambda p: p.startswith("data/") and ("/raw/" in p or "/out/" in p))

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
            "G08_source_package_sync_present",
            "required",
            source_engine,
            package_engine,
            [path for path in paths if path in {ENGINE_SOURCE, ENGINE_PACKAGE}],
            "Source engine changes must include package mirror sync in the same safety packet.",
            f"Update {ENGINE_PACKAGE} or explicitly split into a source-only non-release patch with a separate mirror-sync decision.",
        ),
        row(
            "G09_no_large_data_paths",
            "required",
            engine_changed or bool(data_paths),
            not data_paths,
            data_paths,
            "Engine safety patches must not bundle data/<site>/raw or data/<site>/out files.",
            "Remove large/generated data paths from the patch and keep outputs in /private/tmp or a small artifact note.",
        ),
    ]
    return pd.DataFrame(rows, columns=DETAIL_COLS)


def build_summary(paths: list[str], detail_df: pd.DataFrame) -> pd.DataFrame:
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
    paths = read_changed_paths(args)
    detail_df = build_detail(paths)
    summary_df = build_summary(paths, detail_df)
    detail_df.to_csv(args.output_dir / DETAIL_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(args.output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    main()

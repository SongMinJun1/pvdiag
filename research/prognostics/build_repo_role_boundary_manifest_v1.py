#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
from collections import Counter
from pathlib import Path

import pandas as pd


MANIFEST_OUTPUT_NAME = "repo_role_boundary_manifest_v1.csv"
STATUS_OUTPUT_NAME = "repo_role_boundary_status_v1.csv"
SUMMARY_OUTPUT_NAME = "repo_role_boundary_summary_v1.csv"
JSON_OUTPUT_NAME = "repo_role_boundary_summary_v1.json"

MANIFEST_COLS = [
    "role_id",
    "path_pattern",
    "role_family",
    "artifact_layer",
    "canonical_owner",
    "source_of_truth",
    "sync_direction",
    "edit_policy",
    "commit_policy",
    "validation_required",
    "cleanup_lane",
    "cleanup_action",
    "risk_if_mixed_ko",
    "note_ko",
]

STATUS_COLS = [
    "status_code",
    "path",
    "top_level",
    "role_id",
    "role_family",
    "artifact_layer",
    "canonical_owner",
    "cleanup_action",
    "commit_policy",
    "validation_required",
    "matched_pattern",
]

SUMMARY_COLS = ["kind", "key", "count"]


ROLE_RULES: list[dict[str, str]] = [
    {
        "role_id": "runtime_decision_docs",
        "path_pattern": "docs/OPS_CONALOG_RUNTIME_*",
        "role_family": "docs",
        "artifact_layer": "source_doc",
        "canonical_owner": "docs/runtime_decision",
        "source_of_truth": "yes",
        "sync_direction": "source_only",
        "edit_policy": "direct_doc_edit_allowed",
        "commit_policy": "docs_lane",
        "validation_required": "git_diff_check",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "keep_as_current_runtime_decision_record",
        "risk_if_mixed_ko": "runtime 판단 근거와 임시 evidence가 같은 문서처럼 보일 수 있다.",
        "note_ko": "runtime decision, branch note, gate 문서의 현재 source.",
    },
    {
        "role_id": "stable_mapping_docs",
        "path_pattern": "docs/OPS_CONALOG_STABLE_*",
        "role_family": "docs",
        "artifact_layer": "source_doc",
        "canonical_owner": "docs/stable_mapping",
        "source_of_truth": "yes",
        "sync_direction": "source_only",
        "edit_policy": "boundary_note_only_without_new_decision",
        "commit_policy": "docs_lane",
        "validation_required": "git_diff_check",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "keep_as_stable_contract_record",
        "risk_if_mixed_ko": "stable contract와 runtime redesign 결정이 같은 층으로 읽힐 수 있다.",
        "note_ko": "stable/runtime 경계 문서.",
    },
    {
        "role_id": "paper_or_operator_summary_doc",
        "path_pattern": "ONEPAGER.md",
        "role_family": "docs",
        "artifact_layer": "source_doc",
        "canonical_owner": "docs/operator_summary",
        "source_of_truth": "yes",
        "sync_direction": "source_only",
        "edit_policy": "summary_edit_allowed_when_behavior_or_policy_changes",
        "commit_policy": "docs_lane",
        "validation_required": "git_diff_check",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "keep_as_human_summary",
        "risk_if_mixed_ko": "요약 문서가 runtime artifact schema 변경과 섞여 보일 수 있다.",
        "note_ko": "논문/운영 설명용 상위 요약.",
    },
    {
        "role_id": "generic_docs",
        "path_pattern": "docs/**",
        "role_family": "docs",
        "artifact_layer": "source_doc",
        "canonical_owner": "docs/general",
        "source_of_truth": "yes",
        "sync_direction": "source_only",
        "edit_policy": "direct_doc_edit_allowed",
        "commit_policy": "docs_lane",
        "validation_required": "git_diff_check",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "classify_before_moving_or_merging",
        "risk_if_mixed_ko": "일반 문서와 decision/gate 문서의 무게가 같아 보일 수 있다.",
        "note_ko": "specific rule에 걸리지 않는 docs 하위 문서.",
    },
    {
        "role_id": "panel_engine_source",
        "path_pattern": "pv_ae/**",
        "role_family": "source_code",
        "artifact_layer": "core_engine",
        "canonical_owner": "pv_ae",
        "source_of_truth": "yes",
        "sync_direction": "source_to_release_mirror_when_packaging",
        "edit_policy": "explicit_algorithm_scope_only",
        "commit_policy": "engine_semantics_lane",
        "validation_required": "py_compile_and_runtime_smoke",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "protect_from_docs_or_packaging_cleanup",
        "risk_if_mixed_ko": "엔진 의미 변경이 문서/패키징 정리와 섞이면 결과 변화 원인을 추적하기 어렵다.",
        "note_ko": "core panel engine; 이번 정리에서는 수정 대상이 아니다.",
    },
    {
        "role_id": "research_runtime_logic",
        "path_pattern": "research/prognostics/runtime_rawonly_chain_common_v1.py",
        "role_family": "source_code",
        "artifact_layer": "runtime_logic_source",
        "canonical_owner": "research/prognostics",
        "source_of_truth": "yes",
        "sync_direction": "source_to_release_mirror_when_packaging",
        "edit_policy": "explicit_runtime_semantics_scope_only",
        "commit_policy": "runtime_semantics_lane",
        "validation_required": "py_compile_and_runtime_smoke",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "protect_from_builder_registry_cleanup",
        "risk_if_mixed_ko": "runtime semantics와 helper/builder 정리가 한 커밋에 섞일 수 있다.",
        "note_ko": "raw-only runtime common logic source.",
    },
    {
        "role_id": "research_builders",
        "path_pattern": "research/prognostics/build_*.py",
        "role_family": "source_code",
        "artifact_layer": "builder_entrypoint",
        "canonical_owner": "research/prognostics",
        "source_of_truth": "yes",
        "sync_direction": "source_to_outputs_or_release_when_needed",
        "edit_policy": "builder_contract_edit_allowed",
        "commit_policy": "builder_registry_lane",
        "validation_required": "py_compile_and_relevant_smoke",
        "cleanup_lane": "active_builder_entrypoint_registry",
        "cleanup_action": "mark_active_archive_or_deprecated",
        "risk_if_mixed_ko": "현재 진입점과 예전 실험 helper가 같은 무게로 보인다.",
        "note_ko": "source builder scripts.",
    },
    {
        "role_id": "research_smoke_tests",
        "path_pattern": "research/prognostics/smoke_test_*.py",
        "role_family": "source_code",
        "artifact_layer": "smoke_test",
        "canonical_owner": "research/prognostics",
        "source_of_truth": "yes",
        "sync_direction": "source_only",
        "edit_policy": "test_contract_edit_allowed",
        "commit_policy": "validation_lane",
        "validation_required": "run_smoke_test",
        "cleanup_lane": "active_builder_entrypoint_registry",
        "cleanup_action": "pair_with_active_builder_or_mark_fixture_only",
        "risk_if_mixed_ko": "어떤 smoke가 현재 계약을 지키는지 불분명해진다.",
        "note_ko": "source smoke tests.",
    },
    {
        "role_id": "research_support_modules",
        "path_pattern": "research/prognostics/*.py",
        "role_family": "source_code",
        "artifact_layer": "support_module",
        "canonical_owner": "research/prognostics",
        "source_of_truth": "yes",
        "sync_direction": "source_to_release_mirror_when_packaging_if_used",
        "edit_policy": "scoped_source_edit_allowed",
        "commit_policy": "source_support_lane",
        "validation_required": "py_compile_and_adjacent_smoke",
        "cleanup_lane": "mixed_scope_disentangle",
        "cleanup_action": "classify_as_source_support_before_packaging",
        "risk_if_mixed_ko": "support module과 one-off 분석 스크립트가 구분되지 않을 수 있다.",
        "note_ko": "specific build/smoke rule에 걸리지 않는 research module.",
    },
    {
        "role_id": "local_operator_app",
        "path_pattern": "app/**",
        "role_family": "source_code",
        "artifact_layer": "local_operator_entry",
        "canonical_owner": "app",
        "source_of_truth": "yes",
        "sync_direction": "source_to_release_operator_surface_when_packaging",
        "edit_policy": "operator_surface_edit_allowed",
        "commit_policy": "operator_surface_lane",
        "validation_required": "py_compile_and_ops_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "keep_separate_from_packaged_app_copy",
        "risk_if_mixed_ko": "로컬 실행 진입점과 배포 패키지 진입점의 책임이 섞인다.",
        "note_ko": "local operator app entrypoints.",
    },
    {
        "role_id": "packaged_operator_app",
        "path_pattern": "release/conalog_full_runtime_v1/package/app/**",
        "role_family": "release_package",
        "artifact_layer": "packaged_operator_entry",
        "canonical_owner": "release/conalog_full_runtime_v1",
        "source_of_truth": "package_surface",
        "sync_direction": "package_surface_validated_from_source_or_pack_builder",
        "edit_policy": "package_surface_edit_with_pack_validation",
        "commit_policy": "packaging_lane",
        "validation_required": "py_compile_and_runtime_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "document_if_source_or_package_is_primary_for_file",
        "risk_if_mixed_ko": "source app과 packaged app 중 어느 쪽을 고쳐야 하는지 흔들린다.",
        "note_ko": "packaged runtime app entrypoints.",
    },
    {
        "role_id": "packaged_research_mirror",
        "path_pattern": "release/conalog_full_runtime_v1/package/research/prognostics/**",
        "role_family": "release_package",
        "artifact_layer": "source_mirror",
        "canonical_owner": "research/prognostics",
        "source_of_truth": "mirror",
        "sync_direction": "research_source_to_package_mirror",
        "edit_policy": "do_not_edit_first_unless_package_hotfix_is_declared",
        "commit_policy": "packaging_mirror_lane",
        "validation_required": "source_mirror_diff_and_runtime_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "treat_as_generated_or_synced_mirror",
        "risk_if_mixed_ko": "source builder와 packaged mirror를 둘 다 원본처럼 고칠 수 있다.",
        "note_ko": "runtime package mirror of research/prognostics.",
    },
    {
        "role_id": "packaged_engine_mirror",
        "path_pattern": "release/conalog_full_runtime_v1/package/pv_ae/**",
        "role_family": "release_package",
        "artifact_layer": "source_mirror",
        "canonical_owner": "pv_ae",
        "source_of_truth": "mirror",
        "sync_direction": "pv_ae_source_to_package_mirror",
        "edit_policy": "do_not_edit_first_unless_package_hotfix_is_declared",
        "commit_policy": "packaging_mirror_lane",
        "validation_required": "source_mirror_diff_and_runtime_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "treat_as_engine_mirror",
        "risk_if_mixed_ko": "core engine source와 package mirror가 동시에 원본처럼 보인다.",
        "note_ko": "runtime package mirror of pv_ae.",
    },
    {
        "role_id": "packaged_operator_scripts",
        "path_pattern": "release/conalog_full_runtime_v1/package/bin/**",
        "role_family": "release_package",
        "artifact_layer": "operator_script",
        "canonical_owner": "release/conalog_full_runtime_v1",
        "source_of_truth": "package_surface",
        "sync_direction": "package_surface_only",
        "edit_policy": "operator_script_edit_with_pack_validation",
        "commit_policy": "packaging_lane",
        "validation_required": "runtime_pack_smoke_or_manual_windows_note",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "keep_as_operator_entry_surface",
        "risk_if_mixed_ko": "Windows/operator script 변경이 엔진 의미 변경처럼 보일 수 있다.",
        "note_ko": "packaged operator command scripts.",
    },
    {
        "role_id": "packaged_artifacts",
        "path_pattern": "release/conalog_full_runtime_v1/package/artifacts/**",
        "role_family": "release_package",
        "artifact_layer": "generated_artifact",
        "canonical_owner": "release/conalog_full_runtime_v1",
        "source_of_truth": "generated_from_runtime_pack",
        "sync_direction": "builder_to_release_artifact",
        "edit_policy": "regenerate_preferred_over_manual_edit",
        "commit_policy": "generated_artifact_lane",
        "validation_required": "artifact_load_check_and_pack_summary",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "treat_as_generated_release_output",
        "risk_if_mixed_ko": "생성 산출물과 source rule 변경이 같은 책임처럼 보인다.",
        "note_ko": "runtime packaged generated artifacts.",
    },
    {
        "role_id": "packaged_runtime_bundle",
        "path_pattern": "release/conalog_full_runtime_v1/package/runtime/**",
        "role_family": "release_package",
        "artifact_layer": "binary_runtime_bundle",
        "canonical_owner": "release/conalog_full_runtime_v1",
        "source_of_truth": "binary_bundle",
        "sync_direction": "bundle_build_or_lfs_lane",
        "edit_policy": "do_not_touch_in_code_cleanup",
        "commit_policy": "runtime_bundle_lane",
        "validation_required": "lfs_or_bundle_manifest_check",
        "cleanup_lane": "runtime_bundle_boundary",
        "cleanup_action": "separate_from_code_review_scope",
        "risk_if_mixed_ko": "대용량 runtime bundle이 코드 리뷰/정리 범위를 흐린다.",
        "note_ko": "Windows runtime and binary bundle lane.",
    },
    {
        "role_id": "release_runtime_surface",
        "path_pattern": "release/conalog_full_runtime_v1/**",
        "role_family": "release_package",
        "artifact_layer": "runtime_release_surface",
        "canonical_owner": "release/conalog_full_runtime_v1",
        "source_of_truth": "release_surface",
        "sync_direction": "source_or_builder_to_release",
        "edit_policy": "release_surface_edit_with_pack_validation",
        "commit_policy": "packaging_lane",
        "validation_required": "runtime_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "classify_as_release_surface_before_source_change",
        "risk_if_mixed_ko": "release 문서/요약과 source code 변경이 한 층처럼 보인다.",
        "note_ko": "runtime release catch-all.",
    },
    {
        "role_id": "final_delivery_docs_mirror",
        "path_pattern": "release/final_delivery_v1/package/docs/**",
        "role_family": "final_delivery",
        "artifact_layer": "packaged_doc_mirror",
        "canonical_owner": "docs",
        "source_of_truth": "mirror",
        "sync_direction": "source_docs_to_final_delivery",
        "edit_policy": "regenerate_or_sync_from_source_doc_preferred",
        "commit_policy": "final_delivery_lane",
        "validation_required": "final_delivery_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "treat_as_packaged_doc_mirror",
        "risk_if_mixed_ko": "source docs와 final delivery docs mirror가 동시에 원본처럼 보인다.",
        "note_ko": "final_delivery packaged docs mirror.",
    },
    {
        "role_id": "final_delivery_examples",
        "path_pattern": "release/final_delivery_v1/package/examples/**",
        "role_family": "final_delivery",
        "artifact_layer": "packaged_example",
        "canonical_owner": "release/final_delivery_v1",
        "source_of_truth": "generated_example",
        "sync_direction": "builder_to_final_delivery",
        "edit_policy": "regenerate_preferred_over_manual_edit",
        "commit_policy": "final_delivery_lane",
        "validation_required": "final_delivery_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "treat_as_generated_example",
        "risk_if_mixed_ko": "예제 산출물이 source truth처럼 읽힐 수 있다.",
        "note_ko": "final_delivery packaged examples.",
    },
    {
        "role_id": "final_delivery_surface",
        "path_pattern": "release/final_delivery_v1/**",
        "role_family": "final_delivery",
        "artifact_layer": "delivery_surface",
        "canonical_owner": "release/final_delivery_v1",
        "source_of_truth": "delivery_surface",
        "sync_direction": "source_or_builder_to_final_delivery",
        "edit_policy": "delivery_surface_edit_with_pack_validation",
        "commit_policy": "final_delivery_lane",
        "validation_required": "final_delivery_pack_smoke",
        "cleanup_lane": "source_vs_packaged_mirror_boundary",
        "cleanup_action": "classify_as_final_delivery_surface",
        "risk_if_mixed_ko": "final delivery 표면이 runtime source 변경과 섞일 수 있다.",
        "note_ko": "final delivery catch-all.",
    },
    {
        "role_id": "generated_outputs_workspace",
        "path_pattern": "outputs/**",
        "role_family": "workspace_noncanonical",
        "artifact_layer": "local_generated_output",
        "canonical_owner": "workspace",
        "source_of_truth": "no",
        "sync_direction": "do_not_sync_by_default",
        "edit_policy": "do_not_commit_without_decision",
        "commit_policy": "ignore_or_promote_by_decision",
        "validation_required": "none_until_promoted",
        "cleanup_lane": "workspace_boundary_cleanup",
        "cleanup_action": "move_ignore_or_promote_explicitly",
        "risk_if_mixed_ko": "로컬 재생성 산출물이 공식 release artifact처럼 보인다.",
        "note_ko": "repo-root local outputs.",
    },
    {
        "role_id": "nested_repo_workspace",
        "path_pattern": "pvdiag/**",
        "role_family": "workspace_noncanonical",
        "artifact_layer": "nested_repo",
        "canonical_owner": "workspace",
        "source_of_truth": "no",
        "sync_direction": "do_not_sync",
        "edit_policy": "move_or_remove_after_backup_decision",
        "commit_policy": "never_commit_as_nested_repo",
        "validation_required": "backup_or_remote_check_before_cleanup",
        "cleanup_lane": "workspace_boundary_cleanup",
        "cleanup_action": "quarantine_nested_repo",
        "risk_if_mixed_ko": "중첩 repo가 실제 source tree 일부처럼 보인다.",
        "note_ko": "nested pvdiag repo under repo root.",
    },
    {
        "role_id": "repo_git_attributes",
        "path_pattern": ".gitattributes",
        "role_family": "repo_config",
        "artifact_layer": "git_lfs_config",
        "canonical_owner": "repo_root",
        "source_of_truth": "yes",
        "sync_direction": "repo_config_only",
        "edit_policy": "repo_config_edit_with_lfs_awareness",
        "commit_policy": "repo_config_lane",
        "validation_required": "git_lfs_or_diff_check",
        "cleanup_lane": "runtime_bundle_boundary",
        "cleanup_action": "keep_with_binary_bundle_policy",
        "risk_if_mixed_ko": "LFS 설정이 일반 문서/코드 변경처럼 다뤄질 수 있다.",
        "note_ko": "repo root git attributes and LFS policy.",
    },
]

UNKNOWN_ROLE = {
    "role_id": "unclassified",
    "path_pattern": "*",
    "role_family": "unclassified",
    "artifact_layer": "unknown",
    "canonical_owner": "unknown",
    "source_of_truth": "unknown",
    "sync_direction": "unknown",
    "edit_policy": "inspect_before_edit",
    "commit_policy": "do_not_batch_without_classification",
    "validation_required": "inspect",
    "cleanup_lane": "mixed_scope_disentangle",
    "cleanup_action": "classify_before_action",
    "risk_if_mixed_ko": "역할이 정의되지 않아 다른 lane에 섞일 수 있다.",
    "note_ko": "No role rule matched.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a repo role/boundary manifest so mixed scopes can be read by role "
            "before any cleanup, mirror sync, or new evidence-axis work."
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
        help="Directory where role/boundary outputs will be written.",
    )
    parser.add_argument(
        "--owner-branch",
        default="codex/post-merge-base-j",
        help="Branch or workstream name to record in the JSON summary.",
    )
    return parser.parse_args()


def normalize_status_path(raw_path: str) -> str:
    path = raw_path
    if " -> " in path:
        path = path.split(" -> ", 1)[1]
    return path.strip().strip('"').rstrip("/")


def run_git_status(repo_root: Path) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    rows: list[tuple[str, str]] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        rows.append((line[:2], normalize_status_path(line[3:])))
    return rows


def path_matches(path: str, pattern: str) -> bool:
    clean_path = path.rstrip("/")
    clean_pattern = pattern.rstrip("/")
    if clean_pattern.endswith("/**"):
        base = clean_pattern[:-3]
        return clean_path == base or clean_path.startswith(base + "/")
    if "*" in clean_pattern or "?" in clean_pattern or "[" in clean_pattern:
        return fnmatch.fnmatchcase(clean_path, clean_pattern)
    return clean_path == clean_pattern


def classify_path(path: str) -> dict[str, str]:
    for rule in ROLE_RULES:
        if path_matches(path, rule["path_pattern"]):
            return rule
    return UNKNOWN_ROLE


def build_manifest() -> pd.DataFrame:
    return pd.DataFrame(ROLE_RULES + [UNKNOWN_ROLE], columns=MANIFEST_COLS)


def build_status_manifest(repo_root: Path) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for status_code, path in run_git_status(repo_root):
        rule = classify_path(path)
        rows.append(
            {
                "status_code": status_code,
                "path": path,
                "top_level": path.split("/", 1)[0],
                "role_id": rule["role_id"],
                "role_family": rule["role_family"],
                "artifact_layer": rule["artifact_layer"],
                "canonical_owner": rule["canonical_owner"],
                "cleanup_action": rule["cleanup_action"],
                "commit_policy": rule["commit_policy"],
                "validation_required": rule["validation_required"],
                "matched_pattern": rule["path_pattern"],
            }
        )
    return pd.DataFrame(rows, columns=STATUS_COLS)


def build_summary(status_df: pd.DataFrame, manifest_df: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    counters = {
        "status_code": Counter(status_df["status_code"]) if not status_df.empty else Counter(),
        "role_id": Counter(status_df["role_id"]) if not status_df.empty else Counter(),
        "role_family": Counter(status_df["role_family"]) if not status_df.empty else Counter(),
        "artifact_layer": Counter(status_df["artifact_layer"]) if not status_df.empty else Counter(),
        "cleanup_action": Counter(status_df["cleanup_action"]) if not status_df.empty else Counter(),
        "commit_policy": Counter(status_df["commit_policy"]) if not status_df.empty else Counter(),
        "manifest_role_family": Counter(manifest_df["role_family"]),
    }
    for kind, counter in counters.items():
        for key, count in sorted(counter.items()):
            rows.append({"kind": kind, "key": key, "count": count})
    return pd.DataFrame(rows, columns=SUMMARY_COLS)


def write_json_summary(output_dir: Path, owner_branch: str, status_df: pd.DataFrame, manifest_df: pd.DataFrame, summary_df: pd.DataFrame) -> None:
    def to_counts(kind: str) -> dict[str, int]:
        selected = summary_df.loc[summary_df["kind"].eq(kind)]
        return {str(row["key"]): int(row["count"]) for _, row in selected.iterrows()}

    payload = {
        "owner_branch": owner_branch,
        "manifest_role_total": int(len(manifest_df)),
        "dirty_entry_total": int(len(status_df)),
        "unclassified_dirty_entry_total": int(status_df["role_id"].eq("unclassified").sum()) if not status_df.empty else 0,
        "first_cleanup_lane": "mixed_scope_disentangle",
        "next_cleanup_lanes": [
            "source_vs_packaged_mirror_boundary",
            "active_builder_entrypoint_registry",
        ],
        "status_code_counts": to_counts("status_code"),
        "dirty_role_counts": to_counts("role_id"),
        "dirty_role_family_counts": to_counts("role_family"),
        "dirty_commit_policy_counts": to_counts("commit_policy"),
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_df = build_manifest()
    status_df = build_status_manifest(repo_root)
    summary_df = build_summary(status_df, manifest_df)

    manifest_df.to_csv(output_dir / MANIFEST_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    status_df.to_csv(output_dir / STATUS_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    summary_df.to_csv(output_dir / SUMMARY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json_summary(output_dir, args.owner_branch, status_df, manifest_df, summary_df)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path
import re

import pandas as pd


DIRTY_OUTPUT_NAME = "repo_organization_dirty_summary_v1.csv"
SURFACE_OUTPUT_NAME = "repo_organization_surface_inventory_v1.csv"
DOCREF_OUTPUT_NAME = "repo_organization_doc_tmp_root_inventory_v1.csv"
LANE_OUTPUT_NAME = "repo_organization_cleanup_lanes_v1.csv"
JSON_OUTPUT_NAME = "repo_organization_inventory_summary_v1.json"

DIRTY_COLS = ["kind", "key", "count"]
SURFACE_COLS = ["surface_family", "path", "file_count", "note_ko"]
DOCREF_COLS = ["root_name", "root_class", "ref_count", "example_doc"]
LANE_COLS = ["cleanup_lane", "current_status", "why_now_ko", "immediate_action_ko", "blocking_scope_ko"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a repo-wide organization inventory so cleanup can proceed in explicit lanes "
            "before more feature work is added."
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
        help="Docs root to scan for /private/tmp references. Defaults to <repo-root>/docs.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where inventory outputs will be written.",
    )
    return parser.parse_args()


def run_git_status(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "status", "--short"],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=True,
    )
    return [line for line in completed.stdout.splitlines() if line.strip()]


def build_dirty_summary(repo_root: Path) -> pd.DataFrame:
    lines = run_git_status(repo_root)
    status_counter: Counter[str] = Counter()
    top_counter: Counter[str] = Counter()
    for line in lines:
        code = line[:2]
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        top = path.split("/", 1)[0]
        status_counter[code] += 1
        top_counter[top] += 1
    rows: list[dict[str, object]] = []
    for key, count in sorted(status_counter.items()):
        rows.append({"kind": "status_code", "key": key, "count": count})
    for key, count in top_counter.most_common():
        rows.append({"kind": "top_level", "key": key, "count": count})
    return pd.DataFrame(rows, columns=DIRTY_COLS)


def file_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for item in path.rglob("*") if item.is_file())


def build_surface_inventory(repo_root: Path) -> pd.DataFrame:
    surfaces = [
        ("source_docs", repo_root / "docs", "runtime/stable/final-delivery decision docs"),
        ("source_research", repo_root / "research" / "prognostics", "source builders, smoke tests, audit helpers"),
        ("source_panel_engine", repo_root / "pv_ae", "panel engine and model code"),
        ("release_runtime_research", repo_root / "release" / "conalog_full_runtime_v1" / "package" / "research" / "prognostics", "runtime package mirror of research/prognostics"),
        ("release_runtime_panel_engine", repo_root / "release" / "conalog_full_runtime_v1" / "package" / "pv_ae", "runtime package mirror of pv_ae"),
        ("release_runtime_bin", repo_root / "release" / "conalog_full_runtime_v1" / "package" / "bin", "runtime operator entry scripts"),
        ("release_runtime_artifacts", repo_root / "release" / "conalog_full_runtime_v1" / "package" / "artifacts", "runtime packaged artifacts"),
        ("release_runtime_windows_bundle", repo_root / "release" / "conalog_full_runtime_v1" / "package" / "runtime" / "windows_x64", "heavy packaged runtime bundle"),
        ("final_delivery_docs", repo_root / "release" / "final_delivery_v1" / "package" / "docs", "final_delivery packaged docs mirror"),
        ("final_delivery_examples", repo_root / "release" / "final_delivery_v1" / "package" / "examples", "final_delivery packaged examples"),
    ]
    rows = [
        {
            "surface_family": family,
            "path": str(path),
            "file_count": file_count(path),
            "note_ko": note,
        }
        for family, path, note in surfaces
    ]
    return pd.DataFrame(rows, columns=SURFACE_COLS)


def classify_tmp_root(name: str) -> str:
    if name.startswith("br0"):
        return "historical_br"
    if name in {
        "conalog_mlpe_seed_expand_check",
        "evidence_axis_expansion_opportunity_scan",
        "group_off_report_lane_entry_blocker_check",
        "report_entry_friction_axis_sidecar_check",
        "recovery_recurrence_axis_sidecar_check",
        "evidence_manifest_pack_check",
    }:
        return "current_evidence"
    if name.startswith("pvdiag_") or name == "pvdiag_postmerge_j":
        return "bookkeeping_or_worktree"
    return "other"


def build_doc_tmp_root_inventory(docs_root: Path) -> pd.DataFrame:
    pattern = re.compile(r"(/private/tmp/[^)\]\\\s>`\"]+)")
    rows: list[dict[str, object]] = []
    grouped: dict[str, list[str]] = {}
    for path in sorted(docs_root.glob("OPS_CONALOG_RUNTIME_*")):
        text = path.read_text(encoding="utf-8")
        for match in pattern.findall(text):
            cleaned = match.rstrip('`,"')
            parts = Path(cleaned).parts
            if len(parts) >= 4:
                root_name = parts[3]
            else:
                root_name = Path(cleaned).name
            grouped.setdefault(root_name, []).append(path.name)
    for root_name in sorted(grouped):
        rows.append(
            {
                "root_name": root_name,
                "root_class": classify_tmp_root(root_name),
                "ref_count": len(grouped[root_name]),
                "example_doc": grouped[root_name][0],
            }
        )
    return pd.DataFrame(rows, columns=DOCREF_COLS)


def build_cleanup_lanes() -> pd.DataFrame:
    rows = [
        {
            "cleanup_lane": "mixed_scope_disentangle",
            "current_status": "needs_role_split",
            "why_now_ko": "지금 헷갈리는 핵심은 branch 자체보다 docs/release/research/pv_ae 역할이 한꺼번에 섞여 보인다는 점이다.",
            "immediate_action_ko": "active work를 역할 단위로 다시 읽는 기준과 표식을 먼저 고정한다.",
            "blocking_scope_ko": "새 작업을 시작할 때 무엇이 core인지, mirror인지, docs인지 바로 구분되지 않는다.",
        },
        {
            "cleanup_lane": "source_vs_packaged_mirror_boundary",
            "current_status": "needs_boundary_lock",
            "why_now_ko": "source, runtime package, final_delivery mirror가 따로 움직여 같은 의미가 여러 surface에 분산된다.",
            "immediate_action_ko": "어떤 층이 source of truth이고 어떤 층이 generated mirror인지 경계를 잠근다.",
            "blocking_scope_ko": "한 번 수정할 때 어디까지 동기화해야 하는지 흔들린다.",
        },
        {
            "cleanup_lane": "active_builder_entrypoint_registry",
            "current_status": "needs_registry",
            "why_now_ko": "panel_day_engine 계열 build/smoke helper 수가 매우 많고 current line과 archive line이 섞여 있다.",
            "immediate_action_ko": "active/current builder와 archival helper를 구분하는 entrypoint registry를 만든다.",
            "blocking_scope_ko": "비슷한 이름의 script가 많아 다음 작업 진입점이 불분명해진다.",
        },
        {
            "cleanup_lane": "historical_vs_current_boundary",
            "current_status": "documented_not_reindexed",
            "why_now_ko": "historical BR temp roots가 docs에 남아 있지만 current manifest에는 안 묶여 있다.",
            "immediate_action_ko": "historical archive와 current work line을 분리해서 읽는 manifest를 둔다.",
            "blocking_scope_ko": "과거 validation/packet 결과를 다시 찾을 때 경로 회상이 필요하다.",
        },
        {
            "cleanup_lane": "runtime_bundle_boundary",
            "current_status": "heavy_bundle_separate_lane",
            "why_now_ko": "windows runtime bundle 파일 수가 많고 LFS/binary 관리축이 별도로 존재한다.",
            "immediate_action_ko": "runtime bundle을 code/doc/evidence lane과 분리된 배포 축으로 읽는다.",
            "blocking_scope_ko": "release 관리와 코드 리뷰 범위가 쉽게 섞인다.",
        },
        {
            "cleanup_lane": "workspace_boundary_cleanup",
            "current_status": "needs_noncanonical_split",
            "why_now_ko": "outputs/, nested pvdiag/, bookkeeping files가 남아 있다.",
            "immediate_action_ko": "non-canonical workspace clutter를 별도 cleanup backlog로 고정한다.",
            "blocking_scope_ko": "repo root를 볼 때 실제 작업물과 잔재가 섞여 보인다.",
        },
    ]
    return pd.DataFrame(rows, columns=LANE_COLS)


def write_json_summary(output_dir: Path, dirty_df: pd.DataFrame, surface_df: pd.DataFrame, docref_df: pd.DataFrame, lane_df: pd.DataFrame) -> None:
    status_rows = dirty_df.loc[dirty_df["kind"].eq("status_code")].set_index("key")["count"].to_dict()
    top_rows = dirty_df.loc[dirty_df["kind"].eq("top_level")].set_index("key")["count"].to_dict()
    payload = {
        "dirty_status_counts": status_rows,
        "dirty_top_level_counts": top_rows,
        "surface_count": int(len(surface_df)),
        "runtime_docs_count": int(top_rows.get("docs", 0)),
        "panel_build_total": int(surface_df.loc[surface_df["surface_family"].eq("source_research"), "file_count"].iloc[0]) if not surface_df.empty else 0,
        "doc_tmp_root_total": int(len(docref_df)),
        "doc_tmp_root_class_counts": docref_df["root_class"].value_counts().to_dict(),
        "cleanup_lane_total": int(len(lane_df)),
    }
    (output_dir / JSON_OUTPUT_NAME).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    docs_root = args.docs_root.resolve() if args.docs_root else repo_root / "docs"
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    dirty_df = build_dirty_summary(repo_root)
    surface_df = build_surface_inventory(repo_root)
    docref_df = build_doc_tmp_root_inventory(docs_root)
    lane_df = build_cleanup_lanes()

    dirty_df.to_csv(output_dir / DIRTY_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    surface_df.to_csv(output_dir / SURFACE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    docref_df.to_csv(output_dir / DOCREF_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    lane_df.to_csv(output_dir / LANE_OUTPUT_NAME, index=False, encoding="utf-8-sig")
    write_json_summary(output_dir, dirty_df, surface_df, docref_df, lane_df)


if __name__ == "__main__":
    main()

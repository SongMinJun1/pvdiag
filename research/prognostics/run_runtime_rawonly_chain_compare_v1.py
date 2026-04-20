#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from research.prognostics import runtime_rawonly_chain_common_v1 as common


AUDIT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_fault_event_audit_v1.py"
VERDICT_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_final_verdict_v1.py"
HEURISTIC_SCRIPT = REPO_ROOT / "research" / "prognostics" / "build_panel_day_engine_runtime_heuristic_v1.py"
REFERENCE_FAULT6_PATH = REPO_ROOT / "release" / "conalog_full_runtime_v1" / "package" / "artifacts" / "fault6_fixed_result_table_v1.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run the raw-only runtime chain (audit -> final verdict -> heuristic) in a workspace and compare "
            "the resulting fault table against the current fixed fault6 reference."
        )
    )
    parser.add_argument("--root", type=Path, default=REPO_ROOT, help="Repository root.")
    parser.add_argument("--output-root", type=Path, required=True, help="Folder where workspace and compare outputs will be written.")
    parser.add_argument("--sites", default="conalog,gangui,ktc_ess", help="Comma-separated site list.")
    parser.add_argument(
        "--reuse-existing-site-outs-root",
        type=Path,
        default=REPO_ROOT / "data",
        help="Root containing <site>/out trees. Defaults to repo data root.",
    )
    return parser.parse_args()


def run(cmd: list[str], cwd: Path) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def normalize_sites(raw_sites: str) -> list[str]:
    sites = [token.strip() for token in str(raw_sites).split(",") if token.strip()]
    if not sites:
        raise SystemExit("at least one site must be provided")
    return sites


def stage_workspace(workspace_root: Path, reuse_root: Path, sites: list[str]) -> None:
    if workspace_root.exists():
        shutil.rmtree(workspace_root)
    for site in sites:
        source = reuse_root / site / "out"
        target = workspace_root / "data" / site / "out"
        if not source.exists():
            raise SystemExit(f"missing site out dir for raw-only chain compare: {source}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source, target, dirs_exist_ok=True)


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    workspace_root = output_root / "workspace"
    sites = normalize_sites(args.sites)
    reuse_root = args.reuse_existing_site_outs_root.resolve()

    stage_workspace(workspace_root, reuse_root, sites)
    for script in [AUDIT_SCRIPT, VERDICT_SCRIPT, HEURISTIC_SCRIPT]:
        run([sys.executable, str(script), "--root", str(workspace_root)], cwd=root)

    fault_df = common.build_fault_table_from_outputs(
        workspace_root=workspace_root,
        verdict_name=common.RUNTIME_VERDICT_OUTPUT_NAME,
        heuristic_name=common.RUNTIME_HEURISTIC_OUTPUT_NAME,
    )
    preview_df = common.build_fault_preview(workspace_root, fault_df)
    compare = common.compare_fault_table_to_reference(fault_df, REFERENCE_FAULT6_PATH)

    result_dir = output_root / "result"
    result_dir.mkdir(parents=True, exist_ok=True)
    fault_path = result_dir / "fault_panel_result_raw_only_v1.csv"
    preview_path = result_dir / "fault_panel_result_raw_only_preview_v1.csv"
    summary_path = output_root / "runtime_rawonly_chain_compare_v1.json"
    fault_df.to_csv(fault_path, index=False, encoding="utf-8-sig")
    preview_df.to_csv(preview_path, index=False, encoding="utf-8-sig")

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "workspace_root": str(workspace_root),
        "sites": sites,
        "reuse_existing_site_outs_root": str(reuse_root),
        "generated_outputs": {
            "runtime_audit": str(workspace_root / "_share" / common.RUNTIME_AUDIT_OUTPUT_NAME),
            "runtime_verdict": str(workspace_root / "_share" / common.RUNTIME_VERDICT_OUTPUT_NAME),
            "runtime_heuristic": str(workspace_root / "_share" / common.RUNTIME_HEURISTIC_OUTPUT_NAME),
            "fault_panel_result_raw_only_v1": str(fault_path),
            "fault_panel_result_raw_only_preview_v1": str(preview_path),
        },
        "reference_compare": compare,
        "note_ko": (
            "이 compare는 raw-only strict chain을 workspace에서 다시 계산한 뒤, "
            "현재 fixed fault6 결과와 row key / decision columns / full columns 차이를 비교한다."
        ),
    }
    summary_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] runtime raw-only chain compare: {summary_path}")
    print(f"[OK] row_key_match={compare.get('row_key_match')}")
    print(f"[OK] decision_columns_match={compare.get('decision_columns_match')}")


if __name__ == "__main__":
    main()

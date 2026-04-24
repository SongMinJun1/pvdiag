#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_evidence_manifest_v1.csv"
SUMMARY_NAME = "panel_day_engine_evidence_manifest_summary_v1.csv"
JSON_NAME = "panel_day_engine_evidence_pack_manifest_v1.json"
PACK_ROOT = "evidence_pack_root"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(root: Path) -> dict[str, Path]:
    result_root = root / "result"
    group_off_root = root / "group_off"
    opportunity_root = root / "opportunity"
    report_entry_root = root / "report_entry"
    recovery_root = root / "recovery"

    write_text(result_root / "fault_panel_result_current_v1.csv", "site,panel_id,고장 기준일\nconalog,panel.1,2025-01-01\n")
    write_text(result_root / "fault_panel_result_precursor_report_v1.csv", "site,panel_id,전조날짜\nconalog,panel.2,2025-01-02\n")
    write_text(result_root / "fault_panel_result_raw_only_fault_signal_report_v1.csv", "site,panel_id,신호 기준일\nconalog,panel.3,2025-01-03\n")
    write_text(result_root / "live_chain_summary_v1.json", '{"ok": true}\n')
    write_text(group_off_root / "group_off_report_lane_blocker_table_v1.csv", "panel_id,blocker_type\npanel.4,no_report_lane_entry\n")
    write_text(group_off_root / "group_off_report_lane_blocker_summary_v1.csv", "blocker_type,panels\nno_report_lane_entry,1\n")
    write_text(opportunity_root / "evidence_axis_opportunity_summary_v1.csv", "axis,panels\nreport_entry_friction,10\n")
    write_text(report_entry_root / "panel_day_engine_report_entry_friction_axis_v1.csv", "panel_id,blocker_type\npanel.5,rawonly_date_displaced\n")
    write_text(report_entry_root / "panel_day_engine_report_entry_friction_axis_summary_v1.csv", "direct_flag_family,panels\ngroup_off_date,1\n")
    write_text(recovery_root / "panel_day_engine_recovery_recurrence_axis_v1.csv", "panel_id,recovery_bucket\npanel.6,re_drop_cycle\n")
    write_text(recovery_root / "panel_day_engine_recovery_recurrence_axis_summary_v1.csv", "site,panels\nconalog,1\n")
    return {
        "result_root": result_root,
        "group_off_root": group_off_root,
        "opportunity_root": opportunity_root,
        "report_entry_root": report_entry_root,
        "recovery_root": recovery_root,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_evidence_manifest_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        roots = build_fixture(tmp_root)
        out_dir = tmp_root / "out"
        cmd = [
            sys.executable,
            str(script),
            "--result-root",
            str(roots["result_root"]),
            "--group-off-root",
            str(roots["group_off_root"]),
            "--opportunity-root",
            str(roots["opportunity_root"]),
            "--report-entry-root",
            str(roots["report_entry_root"]),
            "--recovery-root",
            str(roots["recovery_root"]),
            "--output-dir",
            str(out_dir),
            "--owner-branch",
            "codex/test-branch",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        manifest_payload = json.loads((out_dir / JSON_NAME).read_text(encoding="utf-8"))

        required_cols = {
            "evidence_family",
            "judgment_role",
            "artifact_path",
            "artifact_kind",
            "canonical_or_temp",
            "owner_branch",
            "latest_decision_log",
            "repro_command",
            "artifact_exists",
            "pack_path",
        }
        assert_true(required_cols.issubset(detail_df.columns), f"missing columns: {required_cols - set(detail_df.columns)}")
        assert_true((detail_df["owner_branch"] == "codex/test-branch").all(), detail_df.to_string())

        existing_report_entry = detail_df.loc[
            detail_df["evidence_family"].eq("report_entry_friction_axis") & detail_df["artifact_exists"].eq(1)
        ]
        assert_true(len(existing_report_entry) == 2, existing_report_entry.to_string())
        for pack_path in existing_report_entry["pack_path"].tolist():
            assert_true(bool(pack_path), "missing pack_path for existing artifact")
            resolved = Path(pack_path)
            assert_true(resolved.exists(), f"pack artifact missing: {resolved}")

        group_off_modes = detail_df.loc[
            detail_df["evidence_family"].eq("group_off_report_lane_blocker"),
            "repro_mode",
        ].unique().tolist()
        assert_true(group_off_modes == ["manual_oneoff"], str(group_off_modes))

        report_entry_summary = summary_df.loc[
            summary_df["evidence_family"].eq("report_entry_friction_axis"),
            "existing_artifacts",
        ]
        assert_true(int(report_entry_summary.sum()) == 2, summary_df.to_string())
        assert_true(manifest_payload["owner_branch"] == "codex/test-branch", manifest_payload)
        assert_true("report_entry_friction_axis" in manifest_payload["families"], manifest_payload)
        assert_true((out_dir / PACK_ROOT).exists(), "missing pack root")


if __name__ == "__main__":
    main()

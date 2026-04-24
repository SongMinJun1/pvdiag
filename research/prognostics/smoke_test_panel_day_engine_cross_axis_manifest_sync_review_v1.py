#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_cross_axis_manifest_sync_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_cross_axis_manifest_sync_review_summary_v1.csv"
SYNC_NAME = "panel_day_engine_cross_axis_manifest_sync_status_v1.csv"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    friction_root = root / "friction"
    recovery_root = root / "recovery"
    common_root = root / "common"
    manifest_root = root / "manifest"
    role_root = root / "role"
    mirror_root = root / "mirror"
    builder_root = root / "builder"

    write_csv(
        friction_root / "panel_day_engine_report_entry_friction_axis_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "direct_flag_family": "group_off_date",
                "blocker_type": "rawonly_date_displaced",
                "best_report_lane": "raw_signal",
                "direct_row_count": 2,
                "group_off_row_count": 2,
                "site_event_soft_row_count": 0,
                "site_event_hard_row_count": 0,
            },
            {
                "site": "conalog",
                "panel_id": "panel.c",
                "direct_flag_family": "site_event",
                "blocker_type": "no_report_lane_entry",
                "best_report_lane": "none",
                "direct_row_count": 1,
                "group_off_row_count": 0,
                "site_event_soft_row_count": 1,
                "site_event_hard_row_count": 0,
            },
        ],
        columns=[
            "site",
            "panel_id",
            "direct_flag_family",
            "blocker_type",
            "best_report_lane",
            "direct_row_count",
            "group_off_row_count",
            "site_event_soft_row_count",
            "site_event_hard_row_count",
        ],
    )
    write_csv(
        recovery_root / "panel_day_engine_recovery_recurrence_axis_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "recovery_bucket": "re_drop_cycle",
                "best_report_lane": "rawonly_current",
                "recovery_row_count": 3,
                "re_drop_row_count": 1,
                "recovered_sustained_row_count": 1,
            },
            {
                "site": "conalog",
                "panel_id": "panel.b",
                "recovery_bucket": "persistent_non_recovery",
                "best_report_lane": "precursor",
                "recovery_row_count": 0,
                "re_drop_row_count": 0,
                "recovered_sustained_row_count": 0,
            },
        ],
        columns=[
            "site",
            "panel_id",
            "recovery_bucket",
            "best_report_lane",
            "recovery_row_count",
            "re_drop_row_count",
            "recovered_sustained_row_count",
        ],
    )
    write_csv(
        common_root / "panel_day_engine_common_cause_synchrony_axis_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "panel.a",
                "synchrony_bucket": "group_off_synchrony",
                "best_report_lane": "rawonly_current",
                "common_cause_row_count": 2,
                "site_event_row_count": 0,
                "group_off_row_count": 2,
                "subgroup_common_cause_row_count": 0,
                "prefault_B_overlap_row_count": 0,
                "co_drop_hint_row_count": 0,
                "max_co_drop_frac": 0.25,
            },
            {
                "site": "conalog",
                "panel_id": "panel.b",
                "synchrony_bucket": "panel_local_or_weak_synchrony",
                "best_report_lane": "precursor",
                "common_cause_row_count": 0,
                "site_event_row_count": 0,
                "group_off_row_count": 0,
                "subgroup_common_cause_row_count": 0,
                "prefault_B_overlap_row_count": 0,
                "co_drop_hint_row_count": 0,
                "max_co_drop_frac": 0.10,
            },
            {
                "site": "conalog",
                "panel_id": "panel.c",
                "synchrony_bucket": "subgroup_synchrony_candidate",
                "best_report_lane": "none",
                "common_cause_row_count": 1,
                "site_event_row_count": 0,
                "group_off_row_count": 0,
                "subgroup_common_cause_row_count": 1,
                "prefault_B_overlap_row_count": 0,
                "co_drop_hint_row_count": 0,
                "max_co_drop_frac": 0.20,
            },
        ],
        columns=[
            "site",
            "panel_id",
            "synchrony_bucket",
            "best_report_lane",
            "common_cause_row_count",
            "site_event_row_count",
            "group_off_row_count",
            "subgroup_common_cause_row_count",
            "prefault_B_overlap_row_count",
            "co_drop_hint_row_count",
            "max_co_drop_frac",
        ],
    )

    manifest_rows = []
    for family in ["report_entry_friction_axis", "recovery_recurrence_axis", "common_cause_synchrony_axis"]:
        for artifact_name in ["detail.csv", "summary.csv"]:
            manifest_rows.append(
                {
                    "evidence_family": family,
                    "artifact_name": artifact_name,
                    "artifact_exists": 1,
                }
            )
    write_csv(
        manifest_root / "panel_day_engine_evidence_manifest_v1.csv",
        manifest_rows,
        columns=["evidence_family", "artifact_name", "artifact_exists"],
    )
    write_csv(role_root / "repo_role_boundary_manifest_v1.csv", [{"role_id": "source_code"}], columns=["role_id"])
    write_csv(mirror_root / "repo_mirror_boundary_manifest_v1.csv", [{"mirror_family": "runtime"}], columns=["mirror_family"])
    write_csv(
        builder_root / "repo_active_builder_entrypoint_registry_v1.csv",
        [{"entrypoint_id": "build_x", "script_kind": "builder"}],
        columns=["entrypoint_id", "script_kind"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_cross_axis_manifest_sync_review_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture(tmp_root)
        out_dir = tmp_root / "out"
        cmd = [
            sys.executable,
            str(script),
            "--friction-root",
            str(tmp_root / "friction"),
            "--recovery-root",
            str(tmp_root / "recovery"),
            "--common-cause-root",
            str(tmp_root / "common"),
            "--manifest-root",
            str(tmp_root / "manifest"),
            "--role-root",
            str(tmp_root / "role"),
            "--mirror-root",
            str(tmp_root / "mirror"),
            "--builder-registry-root",
            str(tmp_root / "builder"),
            "--output-dir",
            str(out_dir),
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        sync_df = pd.read_csv(out_dir / SYNC_NAME, encoding="utf-8-sig")
        assert_true(len(detail_df) == 3, detail_df.to_string())

        bucket_map = {row["panel_id"]: row["review_focus_bucket"] for row in detail_df.to_dict(orient="records")}
        assert_true(bucket_map["panel.a"] == "strong_common_cause_hold_review", str(bucket_map))
        assert_true(bucket_map["panel.b"] == "local_signal_morphology_review", str(bucket_map))
        assert_true(bucket_map["panel.c"] == "subgroup_or_breadth_context_review", str(bucket_map))
        assert_true(int(summary_df["panels"].sum()) == 3, summary_df.to_string())
        assert_true((sync_df["sync_status"] == "synced").sum() == 3, sync_df.to_string())
        assert_true((sync_df["sync_status"] == "available_cleanup_map").sum() == 3, sync_df.to_string())


if __name__ == "__main__":
    main()

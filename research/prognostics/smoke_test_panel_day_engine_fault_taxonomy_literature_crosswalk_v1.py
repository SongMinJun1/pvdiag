#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

ALLOWED_EVAL_BUCKETS = {
    "precursor_bearing_detectable_now",
    "precursor_capable_but_not_detectable_now",
    "abrupt_or_no_precursor_now",
    "non_panel_or_common_cause",
    "unknown_needs_review",
}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    write_text(tmp_root / "pv_ae" / "panel_day_engine.py", "# synthetic detector core\n")
    write_text(tmp_root / "docs" / "OPS_GPVS_FAULT_FAMILY_F1.md", "# gpvs fault family\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md", "# eligibility\n")
    write_text(tmp_root / "docs" / "OPS_COMMON_CAUSE_PRECURSOR_AUDIT_V1.md", "# common cause precursor\n")

    share_dir = tmp_root / "_share"
    write_csv(
        share_dir / "panel_day_engine_fault_taxonomy_v1.csv",
        [
            {
                "fault_family_id": "electrical_fault_like_progressive_local",
                "fault_family_name_ko": "전기 점진형",
                "family_group_ko": "개별 전기 fault",
                "precursor_capable_flag": 1,
                "onset_labelable_flag": 1,
                "recommended_eval_bucket": "precursor_bearing",
                "evidence_source_files": "eligibility",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "electrical_fault_like_abrupt_local",
                "fault_family_name_ko": "전기 급작형",
                "family_group_ko": "개별 전기 fault",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 1,
                "recommended_eval_bucket": "abrupt_or_no_precursor",
                "evidence_source_files": "eligibility",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "electrical_fault_like_unknown_local_temporality",
                "fault_family_name_ko": "전기 미정형",
                "family_group_ko": "개별 전기 fault",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 1,
                "recommended_eval_bucket": "unknown_needs_review",
                "evidence_source_files": "eligibility",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "group_or_inverter_side_like",
                "fault_family_name_ko": "그룹/인버터형",
                "family_group_ko": "공통원인형",
                "precursor_capable_flag": 1,
                "onset_labelable_flag": 0,
                "recommended_eval_bucket": "unknown_needs_review",
                "evidence_source_files": "common cause",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "none_visible_or_unconfirmed",
                "fault_family_name_ko": "none visible",
                "family_group_ko": "불확정",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 0,
                "recommended_eval_bucket": "abrupt_or_no_precursor",
                "evidence_source_files": "review",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "recurring_chronic_monitor_like",
                "fault_family_name_ko": "monitor",
                "family_group_ko": "run pattern",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 0,
                "recommended_eval_bucket": "unknown_needs_review",
                "evidence_source_files": "label pack",
                "rationale_ko": "synthetic",
            },
            {
                "fault_family_id": "isolated_unexplained",
                "fault_family_name_ko": "isolated",
                "family_group_ko": "run pattern",
                "precursor_capable_flag": 0,
                "onset_labelable_flag": 0,
                "recommended_eval_bucket": "unknown_needs_review",
                "evidence_source_files": "label pack",
                "rationale_ko": "synthetic",
            },
        ],
        [
            "fault_family_id",
            "fault_family_name_ko",
            "family_group_ko",
            "precursor_capable_flag",
            "onset_labelable_flag",
            "recommended_eval_bucket",
            "evidence_source_files",
            "rationale_ko",
        ],
    )

    write_csv(
        share_dir / "panel_day_engine_branch_inventory_v1.csv",
        [
            {
                "file_path": "pv_ae/panel_day_engine.py",
                "artifact_class": "core",
                "layer_name": "detector",
                "purpose_ko": "detector core",
                "source_of_truth_flag": 1,
                "active_for_next_phase_flag": 1,
                "note_ko": "synthetic",
            },
            {
                "file_path": "docs/OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md",
                "artifact_class": "documentation",
                "layer_name": "label_truth",
                "purpose_ko": "eligibility",
                "source_of_truth_flag": 0,
                "active_for_next_phase_flag": 1,
                "note_ko": "synthetic",
            },
            {
                "file_path": "docs/OPS_COMMON_CAUSE_PRECURSOR_AUDIT_V1.md",
                "artifact_class": "documentation",
                "layer_name": "detector",
                "purpose_ko": "common cause",
                "source_of_truth_flag": 0,
                "active_for_next_phase_flag": 0,
                "note_ko": "synthetic",
            },
            {
                "file_path": "docs/OPS_GPVS_FAULT_FAMILY_F1.md",
                "artifact_class": "documentation",
                "layer_name": "evaluation",
                "purpose_ko": "fault family",
                "source_of_truth_flag": 0,
                "active_for_next_phase_flag": 1,
                "note_ko": "synthetic",
            },
        ],
        [
            "file_path",
            "artifact_class",
            "layer_name",
            "purpose_ko",
            "source_of_truth_flag",
            "active_for_next_phase_flag",
            "note_ko",
        ],
    )

    write_csv(
        share_dir / "panel_day_engine_method_layer_status_v1.csv",
        [
            {"layer_name": "detector", "current_status": "paused", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
            {"layer_name": "scorer", "current_status": "exploratory", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
            {"layer_name": "operator", "current_status": "stable_baseline", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
            {"layer_name": "label_truth", "current_status": "active", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
            {"layer_name": "evaluation", "current_status": "needs_definition", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
            {"layer_name": "packaging", "current_status": "stable_baseline", "why_ko": "synthetic", "immediate_need_ko": "synthetic", "next_action_ko": "synthetic"},
        ],
        ["layer_name", "current_status", "why_ko", "immediate_need_ko", "next_action_ko"],
    )

    write_csv(
        share_dir / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "p1",
                "vendor_fault_family": "diode_like",
                "preferred_onset_stage": "episode_start_before_corroborated_signal",
                "preferred_onset_confidence": "medium",
            },
            {
                "site": "beta",
                "panel_id": "p2",
                "vendor_fault_family": "module_damage_like",
                "preferred_onset_stage": "episode_start_before_alarm",
                "preferred_onset_confidence": "strong",
            },
        ],
        ["site", "panel_id", "vendor_fault_family", "preferred_onset_stage", "preferred_onset_confidence"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_fault_taxonomy_literature_crosswalk_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_fault_taxonomy_literature_crosswalk_v1.csv",
        repo_root / "_share" / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
        repo_root / "_share" / "panel_day_engine_fault_taxonomy_eval_buckets_summary_v2.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_fault_taxonomy_literature_crosswalk_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_fault_taxonomy_literature_crosswalk_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="fault_taxonomy_literature_crosswalk_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        crosswalk_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_fault_taxonomy_literature_crosswalk_v1.csv",
            encoding="utf-8-sig",
        )
        eval_buckets_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_fault_taxonomy_eval_buckets_v2.csv",
            encoding="utf-8-sig",
        )
        summary_df = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_fault_taxonomy_eval_buckets_summary_v2.csv",
            encoding="utf-8-sig",
        )

        assert_true(len(crosswalk_df) == 7, "crosswalk should preserve taxonomy row count")
        assert_true(
            set(eval_buckets_df["eval_bucket_v2"].astype(str)).issubset(ALLOWED_EVAL_BUCKETS),
            "eval_bucket_v2 should use only allowed values",
        )
        progressive = eval_buckets_df.loc[eval_buckets_df["fault_family_id"].eq("electrical_fault_like_progressive_local")].iloc[0]
        assert_true(
            progressive["eval_bucket_v2"] == "precursor_bearing_detectable_now",
            "progressive electrical row should be detectable-now precursor bucket",
        )
        inverter_row = eval_buckets_df.loc[eval_buckets_df["fault_family_id"].eq("group_or_inverter_side_like")].iloc[0]
        assert_true(
            inverter_row["eval_bucket_v2"] == "non_panel_or_common_cause",
            "group_or_inverter row should be separated as non-panel/common-cause",
        )
        summary_map = {row["eval_bucket_v2"]: row for row in summary_df.to_dict(orient="records")}
        assert_true(
            int(summary_map["precursor_bearing_detectable_now"]["family_count"]) == 1,
            "summary should count one detectable-now precursor family in synthetic fixture",
        )
        assert_true(
            int(summary_map["abrupt_or_no_precursor_now"]["family_count"]) == 2,
            "summary should count abrupt/no-precursor synthetic rows",
        )
        assert_true(
            int(summary_map["unknown_needs_review"]["family_count"]) == 3,
            "summary should count unknown synthetic rows",
        )

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()

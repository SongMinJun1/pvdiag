#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_fault_family_judgment_candidate_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_fault_family_judgment_candidate_summary_v1.csv"
CRITERIA_NAME = "panel_day_engine_fault_family_judgment_candidate_criteria_v1.csv"
NOTE_NAME = "panel_day_engine_fault_family_judgment_candidate_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py"
    with tempfile.TemporaryDirectory(prefix="fault_family_judgment_packet_") as tmp_dir:
        root = Path(tmp_dir)
        cross = root / "cross.csv"
        pressure = root / "pressure.csv"
        threshold = root / "threshold.csv"
        subtype = root / "subtype.csv"
        out_dir = root / "out"

        write_text(
            cross,
            "\n".join(
                [
                    "site,panel_id,axis_presence_count,has_friction_axis,has_recovery_axis,has_common_cause_axis,friction_blocker_types,friction_direct_row_count,friction_group_off_row_count,friction_site_event_row_count,recovery_bucket,re_drop_row_count,recovered_sustained_row_count,synchrony_bucket,common_cause_row_count,site_event_row_count,group_off_row_count,subgroup_common_cause_row_count,max_co_drop_frac,strong_common_cause_flag,subgroup_or_breadth_context_flag,local_or_weak_synchrony_flag,report_entry_blocker_flag,recovery_morphology_pressure_flag,review_focus_bucket",
                    "conalog,panel.local,2,0,1,1,,0,0,0,re_drop_cycle,2,1,panel_local_or_weak_synchrony,0,0,0,0,0.05,0,0,1,0,1,local_signal_morphology_review",
                    "gangui,panel.common,2,0,1,1,,0,0,0,persistent_non_recovery,0,0,site_event_synchrony,4,4,0,0,0.8,1,0,0,0,1,strong_common_cause_hold_review",
                    "ktc_ess,panel.blocker,1,1,0,0,rawonly_date_displaced,1,1,0,,0,0,,0,0,0,0,0.0,0,0,1,1,0,report_entry_blocker_review",
                ]
            )
            + "\n",
        )
        write_text(
            pressure,
            "\n".join(
                [
                    "packet_case_id,site,panel_id,packet_bucket,counterexample_bucket,evidence_grade,raw_top1_ko,raw_top1_score,raw_top2_ko,raw_top3_ko,same_day_final_fault_row_count,same_day_common_cause_row_count",
                    "BR058-001,conalog,panel.local,non_target_hard_same_day_fault_family_seed,fault_family_boundary_pressure,strong_non_target_fault_family_seed,다이오드·서브스트링형,8,접속·부분개방형,열화형,1,0",
                ]
            )
            + "\n",
        )
        write_text(
            threshold,
            "\n".join(
                [
                    "axis,feature,promote_candidate,hold_or_block,reason_ko",
                    "duration,episode_signal_days,>=2,1 day only,하루짜리 이상은 약함",
                    "spatiality,same_day_site_event_count,low simultaneity,site_event_A>=20,동시 다발은 공통원인",
                ]
            )
            + "\n",
        )
        write_text(
            subtype,
            "\n".join(
                [
                    "family_key,family_label_ko,subtype_key,subtype_label_ko,primary_signature_ko,secondary_signature_ko,negative_signature_ko,minimum_evidence_shadow_ko,recommended_shadow_action,notes_ko",
                    "diode_substring,다이오드·서브스트링 계열,bypass,bypass diode,VI shape,recurrence,site-wide,VI+recurrence,manual_review_candidate,shape first",
                    "external_common_cause,외부계통·공통원인 계열,site,site-wide,simultaneity,recovery,panel-local,site/root,block_individual_precursor,common cause first",
                ]
            )
            + "\n",
        )

        cmd = [
            "python3",
            str(script),
            "--cross-axis-input",
            str(cross),
            "--pressure-input",
            str(pressure),
            "--threshold-input",
            str(threshold),
            "--subtype-input",
            str(subtype),
            "--output-dir",
            str(out_dir),
        ]
        result = subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")

        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        criteria = pd.read_csv(out_dir / CRITERIA_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(len(detail) == 3, f"unexpected detail rows: {len(detail)}")
        assert_true(len(criteria) == 2, f"unexpected criteria rows: {len(criteria)}")
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must remain blocked")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must remain blocked")
        assert_true(
            "fault_family_regression_pressure_seed" in set(detail["judgment_bucket"]),
            "pressure seed bucket missing",
        )
        assert_true(
            "block_individual_precursor_common_cause" in set(detail["judgment_bucket"]),
            "common-cause block bucket missing",
        )
        assert_true(
            "report_lane_or_gap_boundary_review" in set(detail["judgment_bucket"]),
            "report-lane blocker bucket missing",
        )
        assert_true(len(summary) >= 3, f"unexpected summary rows: {len(summary)}")
        assert_true("operator promotion allowed sum: `0`" in note, "note missing promotion guardrail")

    print("smoke ok: panel_day_engine_fault_family_judgment_candidate_packet_v1")


if __name__ == "__main__":
    main()

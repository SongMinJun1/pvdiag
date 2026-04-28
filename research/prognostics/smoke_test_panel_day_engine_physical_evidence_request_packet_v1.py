#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

import pandas as pd


REQUEST_NAME = "panel_day_engine_physical_evidence_request_packet_v1.csv"
SUMMARY_NAME = "panel_day_engine_physical_evidence_request_packet_summary_v1.csv"
NOTE_NAME = "panel_day_engine_physical_evidence_request_packet_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_physical_evidence_request_packet_v1.py"
    with tempfile.TemporaryDirectory(prefix="physical_evidence_request_packet_") as tmp_dir:
        root = Path(tmp_dir)
        confirmation = root / "confirmation.csv"
        checklist = root / "checklist.csv"
        out_dir = root / "out"
        write_text(
            confirmation,
            "\n".join(
                [
                    "confirmation_case_id,source_raw_support_case_id,site,panel_id,confirmation_bucket,candidate_fault_family_label_ko,target_vdom_signal_days,raw_daily_support_frac,raw_median_v_ratio,raw_median_i_ratio,independent_confirmation_required_axes_met,independent_confirmation_required_axes_total,operator_promotion_allowed_flag,engine_patch_candidate_flag,threshold_patch_allowed_flag",
                    "BR069-001,BR068-001,site_a,panel.gap,raw_supported_confirmation_gap_hold,접속 불량·부분 개방 계열 검토,30,0.95,0.55,1.02,0,2,0,0,0",
                    "BR069-002,BR068-002,site_a,panel.ready,independent_confirmation_packet_ready_review,접속 불량·부분 개방 계열 검토,30,0.95,0.55,1.02,2,2,0,0,0",
                ]
            )
            + "\n",
        )
        write_text(
            checklist,
            "\n".join(
                [
                    "confirmation_case_id,site,panel_id,confirmation_axis,axis_required_for_packet_flag,axis_status,satisfies_axis_flag,next_action",
                    "BR069-001,site_a,panel.gap,direct_physical_measurement,1,missing,0,attach exact-panel IV curve",
                    "BR069-001,site_a,panel.gap,maintenance_or_inspection_record,1,missing,0,attach exact-panel inspection",
                    "BR069-001,site_a,panel.gap,field_reproducibility_confirmation,0,missing,0,record exact-panel field confirmation",
                    "BR069-001,site_a,panel.gap,independent_artifact_exclusion,0,raw_or_proxy_support_present_not_independent,0,record artifact exclusion",
                    "BR069-002,site_a,panel.ready,direct_physical_measurement,1,present,1,preserve link",
                    "BR069-002,site_a,panel.ready,maintenance_or_inspection_record,1,present,1,preserve link",
                ]
            )
            + "\n",
        )
        result = subprocess.run(
            [
                "python3",
                str(script),
                "--confirmation-input",
                str(confirmation),
                "--checklist-input",
                str(checklist),
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        requests = pd.read_csv(out_dir / REQUEST_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(len(requests) == 1, f"unexpected request rows: {len(requests)}")
        row = requests.iloc[0]
        assert_true(row["evidence_request_id"] == "BR070-001", row)
        assert_true(row["request_priority"] == "high_evidence_gap_priority", row)
        assert_true(row["requested_evidence_bundle"] == "exact_panel_physical_measurement_plus_inspection", row)
        assert_true(int(row["missing_required_axis_count"]) == 2, row)
        assert_true(int(requests["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(requests["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(requests["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")
        assert_true(len(summary) == 1, f"unexpected summary rows: {len(summary)}")
        assert_true("threshold patch allowed sum: `0`" in note, "note missing threshold guardrail")
    print("smoke ok: panel_day_engine_physical_evidence_request_packet_v1")


if __name__ == "__main__":
    main()

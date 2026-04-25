#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


GAP_COLUMNS = [
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "vendor_exact_rows",
    "vendor_positive_pattern_rows",
    "vendor_likely_positive_rows",
    "vendor_rejected_rows",
    "vendor_field_confirmed_rows",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "independent_physical_or_maintenance_confirmation_met",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

VENDOR_COLUMNS = [
    "site",
    "panel_id",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "adjudication_weight",
    "vendor_note",
]

MANUAL_COLUMNS = [
    "site",
    "evidence_type",
    "description",
    "expected_family",
    "time_type",
    "time_value",
    "related_panel_count",
    "evidence_strength",
    "usable_for_exact_validation",
    "note",
]

INDEPENDENT_COLUMNS = [
    "site",
    "panel_id",
    "evidence_type",
    "evidence_status",
    "evidence_date",
    "evidence_path",
    "evidence_note",
    "reviewer",
]

CLEARANCE_COLUMNS = [
    "site",
    "panel_id",
    "clearance_axis",
    "clearance_status",
    "clearance_date",
    "clearance_evidence_path",
    "clearance_note",
    "reviewer",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def gap(idx: int, panel_id: str, bucket: str, counterexample: int = 0) -> dict[str, object]:
    return {
        "gap_review_row_id": f"BR097-VPCG-{idx:03d}",
        "evidence_request_id": f"BR095-VPER-{idx:03d}",
        "site": "fixture",
        "root_id": panel_id.split(".")[0],
        "panel_group_key": ".".join(panel_id.split(".")[:2]),
        "panel_id": panel_id,
        "request_priority": "P0_counterexample_guarded_evidence_request" if counterexample else "P0_independent_evidence_request",
        "review_bucket": bucket,
        "raw_source_trace_attached": 1,
        "vendor_exact_rows": 1,
        "vendor_positive_pattern_rows": 1 if "vendor" in bucket else 0,
        "vendor_likely_positive_rows": 0,
        "vendor_rejected_rows": 0,
        "vendor_field_confirmed_rows": 0,
        "common_cause_data_clearance_candidate": 1,
        "measurement_artifact_data_clearance_candidate": 1,
        "counterexample_clearance_required": counterexample,
        "independent_physical_or_maintenance_confirmation_met": 0,
        "evidence_ready_for_truth_use": 0,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def vendor(panel_id: str, reply_class: str, confirmed: int) -> dict[str, object]:
    return {
        "site": "fixture",
        "panel_id": panel_id,
        "vendor_reply_class": reply_class,
        "vendor_fault_family": "diode_like",
        "field_confirmed_flag": confirmed,
        "adjudication_weight": 1.0 if confirmed else 0.7,
        "vendor_note": "fixture vendor note",
    }


def independent(panel_id: str) -> dict[str, object]:
    return {
        "site": "fixture",
        "panel_id": panel_id,
        "evidence_type": "physical_measurement",
        "evidence_status": "confirmed",
        "evidence_date": "2026-04-25",
        "evidence_path": "/tmp/fixture_physical_record.pdf",
        "evidence_note": "fixture exact-panel record",
        "reviewer": "fixture",
    }


def clearance(panel_id: str, axis: str) -> dict[str, object]:
    return {
        "site": "fixture",
        "panel_id": panel_id,
        "clearance_axis": axis,
        "clearance_status": "cleared",
        "clearance_date": "2026-04-25",
        "clearance_evidence_path": f"/tmp/fixture_{axis}.md",
        "clearance_note": "fixture clearance",
        "reviewer": "fixture",
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="voltage_preserved_independent_confirmation_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        gap_dir = tmp / "gap"
        gap_dir.mkdir()
        out_dir = tmp / "out"
        vendor_input = tmp / "vendor.csv"
        manual_input = tmp / "manual.csv"
        independent_input = tmp / "independent.csv"
        clearance_input = tmp / "clearance.csv"
        panel_a = "rootA.1.0"
        panel_b = "rootB.1.0"
        panel_c = "rootC.1.0"
        gaps = [
            gap(1, panel_a, "vendor_supported_needs_physical_confirmation"),
            gap(2, panel_b, "vendor_supported_needs_physical_confirmation"),
            gap(3, panel_c, "counterexample_guarded_hold", counterexample=1),
        ]
        pd.DataFrame(gaps).reindex(columns=GAP_COLUMNS).to_csv(
            gap_dir / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        vendors = [
            vendor(panel_a, "vendor_pattern_positive", 1),
            vendor(panel_b, "vendor_pattern_positive", 0),
            vendor(panel_c, "vendor_pattern_positive", 0),
            vendor("otherRoot.1.0", "field_confirmed_positive", 1),
        ]
        pd.DataFrame(vendors).reindex(columns=VENDOR_COLUMNS).to_csv(vendor_input, index=False, encoding="utf-8-sig")
        manual = [
            {
                "site": "fixture",
                "evidence_type": "site_context",
                "description": "fixture manual context",
                "expected_family": "electrical",
                "time_type": "static",
                "time_value": "unknown",
                "related_panel_count": 1,
                "evidence_strength": "weak",
                "usable_for_exact_validation": "no",
                "note": "context only",
            }
        ]
        pd.DataFrame(manual).reindex(columns=MANUAL_COLUMNS).to_csv(manual_input, index=False, encoding="utf-8-sig")
        pd.DataFrame([independent(panel_b)]).reindex(columns=INDEPENDENT_COLUMNS).to_csv(
            independent_input,
            index=False,
            encoding="utf-8-sig",
        )
        clearance_rows = [
            clearance(panel_a, "common_cause_clearance"),
            clearance(panel_a, "measurement_artifact_clearance"),
            clearance(panel_b, "common_cause_clearance"),
            clearance(panel_b, "measurement_artifact_clearance"),
            clearance(panel_c, "common_cause_clearance"),
            clearance(panel_c, "measurement_artifact_clearance"),
        ]
        pd.DataFrame(clearance_rows).reindex(columns=CLEARANCE_COLUMNS).to_csv(
            clearance_input,
            index=False,
            encoding="utf-8-sig",
        )

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py",
            "--repo-root",
            str(repo_root),
            "--gap-review-dir",
            str(gap_dir),
            "--vendor-input",
            str(vendor_input),
            "--manual-site-input",
            str(manual_input),
            "--independent-evidence-input",
            str(independent_input),
            "--blocker-clearance-input",
            str(clearance_input),
            "--output-dir",
            str(out_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["attachment_rows"] == 3, payload)
        assert_true(payload["source_scan_rows"] == 12, payload)
        assert_true(payload["clearance_rows"] == 3, payload)
        assert_true(payload["exact_vendor_field_confirmed_rows"] == 1, payload)
        assert_true(payload["independent_confirmation_attached_rows"] == 2, payload)
        assert_true(payload["explicit_all_clearance_rows"] == 2, payload)
        assert_true(payload["truth_intake_ready_rows"] == 2, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        attachment = pd.read_csv(
            out_dir / "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv"
        )
        clearance_df = pd.read_csv(out_dir / "panel_day_engine_voltage_preserved_blocker_clearance_attachment_v1.csv")
        assert_true(int(attachment["engine_patch_allowed"].sum()) == 0, attachment)
        assert_true(
            set(clearance_df["clearance_status"]) == {
                "all_required_clearances_attached",
                "counterexample_clearance_missing",
            },
            clearance_df,
        )
        print(json.dumps({"smoke": "ok", "attachment_rows": int(len(attachment))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

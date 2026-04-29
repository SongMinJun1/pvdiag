#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


ATTACHMENT_COLUMNS = [
    "attachment_row_id",
    "evidence_request_id",
    "source_confirmation_packet_row_id",
    "source_confirmation_family_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "attachment_status",
    "source_candidate_rows_attached",
    "core_window_rows_attached",
    "core_signal_days_attached",
    "core_voltage_preserved_days_attached",
    "core_common_cause_flag_days",
    "core_measurement_artifact_hold_days",
    "raw_file_refs_total",
    "raw_file_refs_found",
    "raw_file_refs_missing",
    "raw_waveform_is_independent_confirmation",
    "physical_or_maintenance_evidence_attached",
    "common_cause_clearance_attached",
    "measurement_artifact_clearance_attached",
    "counterexample_clearance_attached",
    "evidence_ready_for_truth_use",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

DAILY_COLUMNS = [
    "evidence_request_id",
    "site",
    "root_id",
    "panel_id",
    "date",
    "raw_csv_exists",
    "voltage_preserved_core_signal",
    "common_cause_context_flag",
    "measurement_artifact_hold_flag",
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


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def attachment(
    idx: int,
    request_id: str,
    panel_id: str,
    priority: str,
    common_days: int,
    artifact_days: int,
) -> dict[str, object]:
    root_id = panel_id.split(".")[0]
    return {
        "attachment_row_id": f"BR096-VPRA-{idx:03d}",
        "evidence_request_id": request_id,
        "source_confirmation_packet_row_id": f"BR093-VPCP-{idx:03d}",
        "source_confirmation_family_id": f"BR093-VPCF-{idx:03d}",
        "site": "fixture",
        "root_id": root_id,
        "panel_group_key": ".".join(panel_id.split(".")[:2]),
        "panel_id": panel_id,
        "request_priority": priority,
        "attachment_status": "raw_source_trace_attached",
        "source_candidate_rows_attached": 2,
        "core_window_rows_attached": 3,
        "core_signal_days_attached": 3,
        "core_voltage_preserved_days_attached": 3,
        "core_common_cause_flag_days": common_days,
        "core_measurement_artifact_hold_days": artifact_days,
        "raw_file_refs_total": 3,
        "raw_file_refs_found": 3,
        "raw_file_refs_missing": 0,
        "raw_waveform_is_independent_confirmation": 0,
        "physical_or_maintenance_evidence_attached": 0,
        "common_cause_clearance_attached": 0,
        "measurement_artifact_clearance_attached": 0,
        "counterexample_clearance_attached": 0,
        "evidence_ready_for_truth_use": 0,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def daily(request_id: str, panel_id: str, date: str, common: int, artifact: int) -> dict[str, object]:
    return {
        "evidence_request_id": request_id,
        "site": "fixture",
        "root_id": panel_id.split(".")[0],
        "panel_id": panel_id,
        "date": date,
        "raw_csv_exists": 1,
        "voltage_preserved_core_signal": 1,
        "common_cause_context_flag": common,
        "measurement_artifact_hold_flag": artifact,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def vendor(panel_id: str, reply_class: str, confirmed: int) -> dict[str, object]:
    return {
        "site": "fixture",
        "panel_id": panel_id,
        "vendor_reply_class": reply_class,
        "vendor_fault_family": "diode_like" if "positive" in reply_class else "none_visible",
        "field_confirmed_flag": confirmed,
        "adjudication_weight": 0.7,
        "vendor_note": "fixture vendor note",
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="voltage_preserved_confirmation_gap_review_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        attachment_dir = tmp / "attachment"
        attachment_dir.mkdir()
        output_dir = tmp / "out"
        vendor_input = tmp / "vendor.csv"
        manual_input = tmp / "manual_site.csv"
        panel_a = "rootA.1.0"
        panel_b = "rootB.1.0"
        panel_c = "rootC.1.0"
        attachment_rows = [
            attachment(1, "BR095-VPER-001", panel_a, "P0_independent_evidence_request", 0, 0),
            attachment(2, "BR095-VPER-002", panel_b, "P0_counterexample_guarded_evidence_request", 0, 2),
            attachment(3, "BR095-VPER-003", panel_c, "P1_shape_evidence_request", 1, 0),
        ]
        pd.DataFrame(attachment_rows).reindex(columns=ATTACHMENT_COLUMNS).to_csv(
            attachment_dir / "panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        daily_rows = []
        for request_id, panel_id, common, artifact in [
            ("BR095-VPER-001", panel_a, 0, 0),
            ("BR095-VPER-002", panel_b, 0, 1),
            ("BR095-VPER-003", panel_c, 1, 0),
        ]:
            for day in ["2025-01-01", "2025-01-02", "2025-01-03"]:
                daily_rows.append(daily(request_id, panel_id, day, common, artifact))
        pd.DataFrame(daily_rows).reindex(columns=DAILY_COLUMNS).to_csv(
            attachment_dir / "panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )
        vendors = [
            vendor(panel_a, "vendor_pattern_positive", 0),
            vendor(panel_b, "vendor_pattern_positive", 0),
            vendor(panel_c, "vendor_rejected", 0),
        ]
        pd.DataFrame(vendors).reindex(columns=VENDOR_COLUMNS).to_csv(vendor_input, index=False, encoding="utf-8-sig")
        manual = [
            {
                "site": "fixture",
                "evidence_type": "site_context",
                "description": "fixture site context",
                "expected_family": "electrical",
                "time_type": "static_label",
                "time_value": "unknown",
                "related_panel_count": 3,
                "evidence_strength": "weak",
                "usable_for_exact_validation": "no",
                "note": "context only",
            }
        ]
        pd.DataFrame(manual).reindex(columns=MANUAL_COLUMNS).to_csv(manual_input, index=False, encoding="utf-8-sig")

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py",
            "--repo-root",
            str(repo_root),
            "--attachment-dir",
            str(attachment_dir),
            "--vendor-input",
            str(vendor_input),
            "--manual-site-input",
            str(manual_input),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["review_rows"] == 3, payload)
        assert_true(payload["checklist_rows"] == 18, payload)
        assert_true(payload["vendor_exact_support_rows"] == 3, payload)
        assert_true(payload["vendor_positive_or_likely_rows"] == 2, payload)
        assert_true(payload["vendor_field_confirmed_rows"] == 0, payload)
        assert_true(payload["independent_confirmation_met_rows"] == 0, payload)
        assert_true(payload["evidence_ready_for_truth_use_sum"] == 0, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)
        buckets = payload["review_bucket_counts"]
        assert_true(buckets["vendor_supported_needs_physical_confirmation"] == 1, buckets)
        assert_true(buckets["counterexample_guarded_hold"] == 1, buckets)
        assert_true(buckets["blocker_clearance_hold"] == 1, buckets)

        artifact_payload = json.loads(
            (output_dir / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.json").read_text(
                encoding="utf-8"
            )
        )
        note = (output_dir / "panel_day_engine_voltage_preserved_confirmation_gap_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(
            artifact_payload["input_resolution_sources"]["attachment_input"] == "explicit_cli",
            artifact_payload,
        )
        assert_true(
            artifact_payload["input_resolution_sources"]["daily_trace_input"] == "explicit_cli",
            artifact_payload,
        )
        assert_true("evidence input manifest: `not provided`" in note, note)
        assert_true("`attachment_input`: `explicit_cli`" in note, note)
        assert_true("`daily_trace_input`: `explicit_cli`" in note, note)

        review = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv")
        checklist = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_confirmation_gap_checklist_v1.csv")
        assert_true(int(review["engine_patch_allowed"].sum()) == 0, review)
        assert_true("direct_physical_or_maintenance_confirmation" in set(checklist["confirmation_axis"]), checklist)

        attachment_csv = attachment_dir / "panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv"
        daily_trace_csv = attachment_dir / "panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv"
        manifest_path = tmp / "confirmation_gap_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "attachment_input": str(attachment_csv),
                        "daily_trace_input": str(daily_trace_csv),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = tmp / "manifest_out"
        manifest_proc = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--vendor-input",
                str(vendor_input),
                "--manual-site-input",
                str(manual_input),
                "--output-dir",
                str(manifest_out),
            ],
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads(
            (manifest_out / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (manifest_out / "panel_day_engine_voltage_preserved_confirmation_gap_note_v1.md").read_text(
            encoding="utf-8"
        )
        manifest_review = pd.read_csv(
            manifest_out / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv",
            encoding="utf-8-sig",
        )
        assert_true(manifest_payload["review_rows"] == artifact_payload["review_rows"], manifest_payload)
        assert_true(
            manifest_payload["review_bucket_counts"] == artifact_payload["review_bucket_counts"],
            manifest_payload,
        )
        assert_true(manifest_review["review_bucket"].tolist() == review["review_bucket"].tolist(), manifest_review)
        assert_true(
            manifest_payload["input_resolution_sources"]["attachment_input"] == "input_manifest",
            manifest_payload,
        )
        assert_true(
            manifest_payload["input_resolution_sources"]["daily_trace_input"] == "input_manifest",
            manifest_payload,
        )
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`attachment_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`daily_trace_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_confirmation_gap_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "attachment_input": str(tmp / "missing_attachment.csv"),
                        "daily_trace_input": str(tmp / "missing_daily.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = tmp / "override_out"
        override_proc = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py",
                "--repo-root",
                str(repo_root),
                "--attachment-dir",
                str(attachment_dir),
                "--input-manifest",
                str(bad_manifest_path),
                "--vendor-input",
                str(vendor_input),
                "--manual-site-input",
                str(manual_input),
                "--output-dir",
                str(override_out),
            ],
            repo_root,
        )
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads(
            (override_out / "panel_day_engine_voltage_preserved_confirmation_gap_review_v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert_true(override_payload["input_resolution_sources"]["attachment_input"] == "explicit_cli", override_payload)
        assert_true(override_payload["input_resolution_sources"]["daily_trace_input"] == "explicit_cli", override_payload)

        missing_daily_manifest_path = tmp / "missing_daily_confirmation_gap_inputs.json"
        missing_daily_manifest_path.write_text(
            json.dumps({"inputs": {"attachment_input": str(attachment_csv)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_daily_proc = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_daily_manifest_path),
                "--vendor-input",
                str(vendor_input),
                "--manual-site-input",
                str(manual_input),
                "--output-dir",
                str(tmp / "missing_daily_out"),
            ],
            repo_root,
        )
        assert_true(missing_daily_proc.returncode != 0, "missing-daily manifest unexpectedly passed")
        assert_true(
            "missing `daily_trace_input`" in (missing_daily_proc.stderr + missing_daily_proc.stdout),
            missing_daily_proc.stderr,
        )

        missing_attachment_manifest_path = tmp / "missing_attachment_confirmation_gap_inputs.json"
        missing_attachment_manifest_path.write_text(
            json.dumps({"inputs": {"daily_trace_input": str(daily_trace_csv)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_attachment_proc = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_attachment_manifest_path),
                "--vendor-input",
                str(vendor_input),
                "--manual-site-input",
                str(manual_input),
                "--output-dir",
                str(tmp / "missing_attachment_out"),
            ],
            repo_root,
        )
        assert_true(missing_attachment_proc.returncode != 0, "missing-attachment manifest unexpectedly passed")
        assert_true(
            "missing `attachment_input`" in (missing_attachment_proc.stderr + missing_attachment_proc.stdout),
            missing_attachment_proc.stderr,
        )
        print(json.dumps({"smoke": "ok", "review_rows": int(len(review))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

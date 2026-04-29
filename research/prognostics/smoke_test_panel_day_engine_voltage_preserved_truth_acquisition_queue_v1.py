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
    "gap_review_row_id",
    "evidence_request_id",
    "site",
    "root_id",
    "panel_group_key",
    "panel_id",
    "request_priority",
    "review_bucket",
    "raw_source_trace_attached",
    "exact_vendor_rows",
    "exact_vendor_positive_or_likely_rows",
    "exact_vendor_rejected_rows",
    "exact_vendor_field_confirmed_rows",
    "same_site_reference_field_confirmed_rows",
    "manual_site_context_rows",
    "manual_site_exact_usable_rows",
    "exact_independent_evidence_rows",
    "independent_confirmation_attached",
    "common_cause_data_clearance_candidate",
    "measurement_artifact_data_clearance_candidate",
    "counterexample_clearance_required",
    "explicit_common_cause_clearance_attached",
    "explicit_measurement_artifact_clearance_attached",
    "explicit_counterexample_clearance_attached",
    "all_required_clearances_attached",
    "truth_intake_ready",
    "positive_truth_candidate_approved",
    "threshold_tuning_approved",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def attachment(
    idx: int,
    panel_id: str,
    bucket: str,
    vendor_positive: int,
    vendor_rejected: int,
    counterexample_required: int,
    independent_attached: int = 0,
    common_attached: int = 0,
    artifact_attached: int = 0,
    counter_attached: int = 0,
) -> dict[str, object]:
    all_clear = int(common_attached and artifact_attached and (not counterexample_required or counter_attached))
    return {
        "attachment_row_id": f"BR098-VPIC-{idx:03d}",
        "gap_review_row_id": f"BR097-VPCG-{idx:03d}",
        "evidence_request_id": f"BR095-VPER-{idx:03d}",
        "site": "fixture",
        "root_id": panel_id.split(".")[0],
        "panel_group_key": ".".join(panel_id.split(".")[:2]),
        "panel_id": panel_id,
        "request_priority": "P0_counterexample_guarded_evidence_request" if counterexample_required else "P0_independent_evidence_request",
        "review_bucket": bucket,
        "raw_source_trace_attached": 1,
        "exact_vendor_rows": int(vendor_positive or vendor_rejected),
        "exact_vendor_positive_or_likely_rows": vendor_positive,
        "exact_vendor_rejected_rows": vendor_rejected,
        "exact_vendor_field_confirmed_rows": 0,
        "same_site_reference_field_confirmed_rows": 1 if idx == 1 else 0,
        "manual_site_context_rows": 0,
        "manual_site_exact_usable_rows": 0,
        "exact_independent_evidence_rows": independent_attached,
        "independent_confirmation_attached": independent_attached,
        "common_cause_data_clearance_candidate": 1,
        "measurement_artifact_data_clearance_candidate": 1,
        "counterexample_clearance_required": counterexample_required,
        "explicit_common_cause_clearance_attached": common_attached,
        "explicit_measurement_artifact_clearance_attached": artifact_attached,
        "explicit_counterexample_clearance_attached": counter_attached,
        "all_required_clearances_attached": all_clear,
        "truth_intake_ready": 0,
        "positive_truth_candidate_approved": 0,
        "threshold_tuning_approved": 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="voltage_preserved_truth_acquisition_queue_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        attachment_dir = tmp / "attachment"
        attachment_dir.mkdir()
        output_dir = tmp / "out"
        rows = [
            attachment(1, "rootA.1.0", "vendor_supported_needs_physical_confirmation", 1, 0, 0),
            attachment(2, "rootB.1.0", "counterexample_guarded_hold", 1, 0, 1),
            attachment(3, "rootC.1.0", "vendor_supported_needs_physical_confirmation", 1, 0, 0, 1, 1, 1, 0),
        ]
        pd.DataFrame(rows).reindex(columns=ATTACHMENT_COLUMNS).to_csv(
            attachment_dir / "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv",
            index=False,
            encoding="utf-8-sig",
        )

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py",
            "--repo-root",
            str(repo_root),
            "--attachment-dir",
            str(attachment_dir),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["queue_rows"] == 10, payload)
        assert_true(payload["panel_summary_rows"] == 3, payload)
        assert_true(payload["collector_template_rows"] == 7, payload)
        assert_true(payload["independent_confirmation_queue_rows"] == 3, payload)
        assert_true(payload["common_cause_clearance_queue_rows"] == 3, payload)
        assert_true(payload["measurement_artifact_clearance_queue_rows"] == 3, payload)
        assert_true(payload["counterexample_clearance_queue_rows"] == 1, payload)
        assert_true(payload["open_required_axes"] == 7, payload)
        assert_true(payload["truth_intake_ready_rows"] == 1, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        artifact_payload = json.loads(
            (output_dir / "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.json").read_text(
                encoding="utf-8"
            )
        )
        note = (output_dir / "panel_day_engine_voltage_preserved_truth_acquisition_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(
            artifact_payload["input_resolution_sources"]["attachment_input"] == "explicit_cli",
            artifact_payload,
        )
        assert_true("evidence input manifest: `not provided`" in note, note)
        assert_true("`attachment_input`: `explicit_cli`" in note, note)

        queue = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.csv")
        panel = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_truth_acquisition_panel_summary_v1.csv")
        template = pd.read_csv(output_dir / "panel_day_engine_voltage_preserved_truth_acquisition_collector_template_v1.csv")
        assert_true(int(queue["operator_facing_change_allowed"].sum()) == 0, queue)
        assert_true("P0_counterexample_clearance" in set(queue["axis_priority"]), queue)
        assert_true(int(panel["same_site_reference_only_flag"].sum()) == 1, panel)
        assert_true(set(template["collector_status"].fillna("")) == {""}, template)

        attachment_csv = attachment_dir / "panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv"
        manifest_path = tmp / "truth_acquisition_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"attachment_input": str(attachment_csv)}},
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
                "research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--output-dir",
                str(manifest_out),
            ],
            repo_root,
        )
        assert_true(manifest_proc.returncode == 0, manifest_proc.stderr or manifest_proc.stdout)
        manifest_payload = json.loads(
            (manifest_out / "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (manifest_out / "panel_day_engine_voltage_preserved_truth_acquisition_note_v1.md").read_text(
            encoding="utf-8"
        )
        manifest_queue = pd.read_csv(
            manifest_out / "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.csv",
            encoding="utf-8-sig",
        )
        assert_true(manifest_payload["queue_rows"] == artifact_payload["queue_rows"], manifest_payload)
        assert_true(
            manifest_payload["collector_template_rows"] == artifact_payload["collector_template_rows"],
            manifest_payload,
        )
        assert_true(manifest_queue["axis_priority"].tolist() == queue["axis_priority"].tolist(), manifest_queue)
        assert_true(
            manifest_payload["input_resolution_sources"]["attachment_input"] == "input_manifest",
            manifest_payload,
        )
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`attachment_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_truth_acquisition_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"attachment_input": str(tmp / "missing_attachment.csv")}},
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
                "research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py",
                "--repo-root",
                str(repo_root),
                "--attachment-dir",
                str(attachment_dir),
                "--input-manifest",
                str(bad_manifest_path),
                "--output-dir",
                str(override_out),
            ],
            repo_root,
        )
        assert_true(override_proc.returncode == 0, override_proc.stderr or override_proc.stdout)
        override_payload = json.loads(
            (override_out / "panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert_true(override_payload["input_resolution_sources"]["attachment_input"] == "explicit_cli", override_payload)

        missing_key_manifest_path = tmp / "missing_key_truth_acquisition_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest_path),
                "--output-dir",
                str(tmp / "missing_key_out"),
            ],
            repo_root,
        )
        assert_true(missing_key_proc.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `attachment_input`" in (missing_key_proc.stderr + missing_key_proc.stdout),
            missing_key_proc.stderr,
        )
        print(json.dumps({"smoke": "ok", "queue_rows": int(len(queue))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

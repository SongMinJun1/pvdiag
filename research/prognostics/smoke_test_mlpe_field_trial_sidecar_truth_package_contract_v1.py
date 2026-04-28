#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_sidecar_truth_package_contract_v1.py"


def run_builder(*args: str) -> dict[str, object]:
    result = subprocess.run(
        ["python3", str(BUILDER), "--repo-root", str(ROOT), *args],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def materialization_rows() -> list[dict[str, object]]:
    return [
        {
            "trial_event_id": "EV_CLEAR",
            "site": "ktc_ess",
            "root_id": "R1",
            "panel_id": "P1",
            "event_date": "2026-04-25",
            "truth_candidate_role": "field_trial_candidate",
            "truth_seed_reviewer_decision": "approve_for_sidecar_package",
            "materialization_precheck_passed_flag": 1,
            "future_sidecar_truth_package_candidate_flag": 1,
            "canonical_truth_write_allowed": 0,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        },
        {
            "trial_event_id": "EV_BLOCKED",
            "site": "ktc_ess",
            "root_id": "R2",
            "panel_id": "P2",
            "event_date": "2026-04-26",
            "truth_candidate_role": "field_trial_candidate",
            "truth_seed_reviewer_decision": "defer",
            "materialization_precheck_passed_flag": 0,
            "future_sidecar_truth_package_candidate_flag": 0,
            "canonical_truth_write_allowed": 0,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        },
    ]


def clearance_rows(event_id: str, groups: list[str], blocked: set[str] | None = None) -> list[dict[str, object]]:
    blocked = blocked or set()
    rows = []
    for group in groups:
        is_blocked = int(group in blocked)
        rows.append(
            {
                "trial_event_id": event_id,
                "clearance_group": group,
                "required_flag": 1,
                "clearance_passed_flag": int(not is_blocked),
                "clearance_blocking_flag": is_blocked,
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        )
    return rows


def package_rows(good: bool = True) -> list[dict[str, object]]:
    if good:
        return [
            {
                "trial_event_id": "EV_CLEAR",
                "site": "ktc_ess",
                "root_id": "R1",
                "panel_id": "P1",
                "event_date": "2026-04-25",
                "sidecar_truth_package_id": "PKG-EV-CLEAR",
                "sidecar_package_mode": "sidecar_truth_candidate",
                "sidecar_truth_label": "confirmed_panel_fault",
                "sidecar_fault_family": "panel_physical_fault",
                "sidecar_event_type": "abrupt_fault",
                "sidecar_onset_date": "2026-04-24",
                "sidecar_fault_date": "2026-04-25",
                "source_materialization_path": "/tmp/materialization.csv",
                "source_common_cause_clearance_path": "/tmp/common.csv",
                "source_artifact_mlpe_control_clearance_path": "/tmp/artifact.csv",
                "reviewer_package_approval_flag": 1,
                "reviewer_package_note": "synthetic approval for smoke",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        ]
    return [
        {
            "trial_event_id": "EV_BAD",
            "site": "ktc_ess",
            "root_id": "R9",
            "panel_id": "",
            "event_date": "2026-04-27",
            "sidecar_truth_package_id": "",
            "sidecar_package_mode": "sidecar_truth_candidate",
            "sidecar_truth_label": "",
            "sidecar_fault_family": "panel_physical_fault",
            "sidecar_event_type": "",
            "sidecar_onset_date": "",
            "sidecar_fault_date": "",
            "source_materialization_path": "",
            "source_common_cause_clearance_path": "",
            "source_artifact_mlpe_control_clearance_path": "",
            "reviewer_package_approval_flag": 0,
            "reviewer_package_note": "",
            "canonical_truth_write_allowed": 1,
            "truth_intake_allowed": 0,
            "threshold_patch_allowed": 0,
            "engine_patch_allowed": 0,
        }
    ]


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "missing"
        missing = run_builder("--materialization-precheck", str(Path(td) / "missing_materialization.csv"), "--output-dir", str(out_dir))
        assert missing["contract_rows"] == 8
        assert missing["events"] == 0
        assert missing["sidecar_truth_package_ready_events"] == 0
        assert missing["package_blocked_rows"] == 1
        assert missing["issue_rows"] == 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        materialization = root / "materialization.csv"
        common = root / "common.csv"
        artifact = root / "artifact.csv"
        package = root / "package.csv"
        out_dir = root / "good_out"
        common_groups = ["source_evidence_ready", "peer_context_clearance", "reviewer_clearance_note"]
        artifact_groups = ["source_evidence_ready", "timestamp_quality_clearance", "reviewer_clearance_note"]

        write_csv(materialization, materialization_rows())
        write_csv(common, clearance_rows("EV_CLEAR", common_groups) + clearance_rows("EV_BLOCKED", common_groups, {"reviewer_clearance_note"}))
        write_csv(artifact, clearance_rows("EV_CLEAR", artifact_groups) + clearance_rows("EV_BLOCKED", artifact_groups, {"timestamp_quality_clearance"}))
        write_csv(package, package_rows(True))
        good = run_builder(
            "--materialization-precheck",
            str(materialization),
            "--common-cause-clearance",
            str(common),
            "--artifact-mlpe-control-clearance",
            str(artifact),
            "--sidecar-package-input",
            str(package),
            "--output-dir",
            str(out_dir),
        )
        assert good["events"] == 2
        assert good["sidecar_truth_package_ready_events"] == 1
        assert good["package_rows"] == 16
        assert good["canonical_truth_write_allowed_sum"] == 0
        assert good["truth_intake_allowed_sum"] == 0
        assert good["threshold_patch_allowed_sum"] == 0
        assert good["engine_patch_allowed_sum"] == 0

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        materialization = root / "materialization.csv"
        common = root / "common.csv"
        artifact = root / "artifact.csv"
        package = root / "package.csv"
        out_dir = root / "bad_out"
        groups = ["source_evidence_ready", "reviewer_clearance_note"]
        bad_materialization = materialization_rows()[:1]
        bad_materialization[0]["trial_event_id"] = "EV_BAD"
        write_csv(materialization, bad_materialization)
        write_csv(common, clearance_rows("EV_BAD", groups, {"reviewer_clearance_note"}))
        write_csv(artifact, clearance_rows("EV_BAD", groups, {"reviewer_clearance_note"}))
        write_csv(package, package_rows(False))
        bad = run_builder(
            "--materialization-precheck",
            str(materialization),
            "--common-cause-clearance",
            str(common),
            "--artifact-mlpe-control-clearance",
            str(artifact),
            "--sidecar-package-input",
            str(package),
            "--output-dir",
            str(out_dir),
        )
        assert bad["events"] == 1
        assert bad["sidecar_truth_package_ready_events"] == 0
        assert bad["issue_rows"] >= 6
        status_df = pd.read_csv(out_dir / "mlpe_field_trial_sidecar_truth_package_dry_run_v1.csv", encoding="utf-8-sig")
        statuses = set(status_df["sidecar_truth_package_status"])
        assert "blocked_common_cause_clearance_not_ready" in statuses
        assert "blocked_artifact_mlpe_control_clearance_not_ready" in statuses
        assert "blocked_sidecar_payload_identity_incomplete" in statuses
        assert "blocked_sidecar_truth_label_payload_incomplete" in statuses
        assert "blocked_source_evidence_provenance_missing" in statuses
        assert "blocked_write_boundary_violation" in statuses
        assert "blocked_reviewer_package_approval_missing" in statuses

    print(json.dumps({"smoke": "ok", "missing_blocked_rows": missing["package_blocked_rows"], "good_ready_events": good["sidecar_truth_package_ready_events"], "bad_ready_events": bad["sidecar_truth_package_ready_events"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py"


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


def sidecar_rows(event_id: str, label: str, family: str, blocking: bool = False) -> list[dict[str, object]]:
    groups = [
        "materialization_precheck_ready",
        "common_cause_clearance_ready",
        "artifact_mlpe_control_clearance_ready",
        "sidecar_payload_identity",
        "sidecar_truth_label_payload",
        "source_evidence_provenance_attached",
        "write_boundary_locked",
        "reviewer_package_approval_note",
    ]
    rows = []
    for group in groups:
        rows.append(
            {
                "trial_event_id": event_id,
                "site": "ktc_ess",
                "root_id": "R1" if event_id != "EV_NEG" else "R2",
                "panel_id": "P1" if event_id != "EV_NEG" else "P2",
                "event_date": "2026-04-25",
                "package_group": group,
                "required_flag": 1,
                "package_group_blocking_flag": int(blocking and group == "reviewer_package_approval_note"),
                "sidecar_truth_package_status": "sidecar_truth_package_group_passed",
                "sidecar_truth_package_id": f"PKG-{event_id}",
                "sidecar_truth_label": label,
                "sidecar_fault_family": family,
                "sidecar_event_type": "abrupt_fault" if label != "confirmed_no_fault" else "negative_control",
                "sidecar_onset_date": "2026-04-24",
                "sidecar_fault_date": "2026-04-25",
                "canonical_truth_write_allowed": 0,
                "truth_intake_allowed": 0,
                "threshold_patch_allowed": 0,
                "engine_patch_allowed": 0,
            }
        )
    return rows


def replay_row(event_id: str, detected: int, alert_date: str, family: str, confidence: float, write_flag: int = 0) -> dict[str, object]:
    return {
        "trial_event_id": event_id,
        "site": "ktc_ess",
        "root_id": "R1" if event_id != "EV_NEG" else "R2",
        "panel_id": "P1" if event_id != "EV_NEG" else "P2",
        "detected_flag": detected,
        "alert_date": alert_date,
        "predicted_fault_family": family,
        "confidence_score": confidence,
        "canonical_truth_write_allowed": write_flag,
        "truth_intake_allowed": 0,
        "threshold_patch_allowed": 0,
        "engine_patch_allowed": 0,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        out_dir = Path(td) / "missing"
        missing = run_builder("--sidecar-package", str(Path(td) / "missing_sidecar.csv"), "--output-dir", str(out_dir))
        assert missing["contract_rows"] == 10
        assert missing["events"] == 0
        assert missing["truth_replay_scorecard_ready_events"] == 0
        assert missing["scorecard_blocked_rows"] == 1
        assert missing["issue_rows"] == 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sidecar = root / "sidecar.csv"
        baseline = root / "baseline.csv"
        candidate = root / "candidate.csv"
        out_dir = root / "good_out"
        write_csv(
            sidecar,
            sidecar_rows("EV_POS", "confirmed_panel_fault", "panel_physical_fault")
            + sidecar_rows("EV_NEG", "confirmed_no_fault", "normal"),
        )
        write_csv(
            baseline,
            [
                replay_row("EV_POS", 0, "", "", 0.0),
                replay_row("EV_NEG", 1, "2026-04-24", "panel_physical_fault", 0.7),
            ],
        )
        write_csv(
            candidate,
            [
                replay_row("EV_POS", 1, "2026-04-23", "panel_physical_fault", 0.9),
                replay_row("EV_NEG", 0, "", "", 0.0),
            ],
        )
        good = run_builder(
            "--sidecar-package",
            str(sidecar),
            "--baseline-replay-input",
            str(baseline),
            "--candidate-replay-input",
            str(candidate),
            "--output-dir",
            str(out_dir),
        )
        assert good["events"] == 2
        assert good["truth_replay_scorecard_ready_events"] == 2
        assert good["scorecard_rows"] == 20
        assert good["metric_rows"] >= 6
        assert good["performance_improvement_claim_allowed_sum"] == 0
        metrics = pd.read_csv(out_dir / "mlpe_field_trial_truth_replay_scorecard_metrics_v1.csv", encoding="utf-8-sig")
        candidate_overall = metrics[(metrics["model"] == "candidate") & (metrics["metric_scope"] == "overall")].iloc[0]
        baseline_overall = metrics[(metrics["model"] == "baseline") & (metrics["metric_scope"] == "overall")].iloc[0]
        assert float(candidate_overall["precision"]) == 1.0
        assert float(candidate_overall["recall"]) == 1.0
        assert int(candidate_overall["performance_improvement_claim_allowed"]) == 0
        assert float(baseline_overall["precision"]) == 0.0

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        sidecar = root / "sidecar.csv"
        baseline = root / "baseline.csv"
        candidate = root / "candidate.csv"
        out_dir = root / "bad_out"
        write_csv(sidecar, sidecar_rows("EV_BAD", "confirmed_panel_fault", "panel_physical_fault"))
        write_csv(baseline, [replay_row("EV_BAD", 1, "bad-date", "panel_physical_fault", 0.5)])
        write_csv(candidate, [replay_row("EV_BAD", 1, "bad-date", "wrong_family", 0.5, write_flag=1)])
        bad = run_builder(
            "--sidecar-package",
            str(sidecar),
            "--baseline-replay-input",
            str(baseline),
            "--candidate-replay-input",
            str(candidate),
            "--output-dir",
            str(out_dir),
        )
        assert bad["events"] == 1
        assert bad["truth_replay_scorecard_ready_events"] == 0
        assert bad["issue_rows"] >= 3
        status_df = pd.read_csv(out_dir / "mlpe_field_trial_truth_replay_scorecard_dry_run_v1.csv", encoding="utf-8-sig")
        statuses = set(status_df["truth_replay_scorecard_status"])
        assert "blocked_candidate_result_missing" in statuses or "blocked_lead_time_axis_not_computable" in statuses
        assert "blocked_lead_time_axis_not_computable" in statuses

    print(
        json.dumps(
            {
                "smoke": "ok",
                "missing_blocked_rows": missing["scorecard_blocked_rows"],
                "good_ready_events": good["truth_replay_scorecard_ready_events"],
                "bad_ready_events": bad["truth_replay_scorecard_ready_events"],
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

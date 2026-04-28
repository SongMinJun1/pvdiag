#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_blocked_state_readiness_handoff_audit_v1.py"

EXPECTED_COMPLETE = {
    "BR-20260425-128",
    "BR-20260425-129",
    "BR-20260425-131",
    "BR-20260425-133",
    "BR-20260425-135",
    "BR-20260425-137",
    "BR-20260425-139",
    "BR-20260425-143",
}


def run_builder(repo_root: Path, queue: Path, commit_json: Path, out_dir: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "python3",
            str(BUILDER),
            "--repo-root",
            str(repo_root),
            "--queue-input",
            str(queue),
            "--commit-scope-json",
            str(commit_json),
            "--output-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def write(path: Path, text: str = "x\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def queue_rows(open_branch: str | None = None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seq in range(1, 24):
        branch = f"BR-20260425-{127 + seq:03d}"
        if branch in EXPECTED_COMPLETE:
            status = "complete_this_branch"
        else:
            status = "blocked_waiting_fixture"
        if open_branch == branch:
            status = "open_now"
        rows.append(
            {
                "branch": branch,
                "sequence_no": seq,
                "runway_stage": f"stage_{seq}",
                "status": status,
                "depends_on": "",
                "entry_gate": "",
                "planned_output": "",
                "exit_gate": "",
                "blocked_by": "fixture",
                "next_action": "fixture action",
                "operator_facing_change": "no" if branch != "BR-20260425-144" else "yes_if_authorized",
            }
        )
    return rows


def write_supporting_files(repo_root: Path) -> None:
    docs = {
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_129_REAL_CAPTURE_INTAKE_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_131_SOURCE_EVIDENCE_RESOLVER_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_133_COMMON_CAUSE_CLEARANCE_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_135_ARTIFACT_MLPE_CONTROL_CLEARANCE_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_137_SIDECAR_TRUTH_PACKAGE_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_139_TRUTH_REPLAY_SCORECARD_CONTRACT_V1.md",
        "docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_143_PANEL_ENGINE_PREPATCH_GATE_REFRESH_V1.md",
    }
    builders = {
        "build_mlpe_field_trial_real_capture_intake_contract_v1.py",
        "build_mlpe_field_trial_source_evidence_resolver_contract_v1.py",
        "build_mlpe_field_trial_common_cause_clearance_contract_v1.py",
        "build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py",
        "build_mlpe_field_trial_sidecar_truth_package_contract_v1.py",
        "build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py",
        "build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py",
    }
    smokes = {name.replace("build_", "smoke_test_") for name in builders}
    for path in docs:
        write(repo_root / path)
    for name in builders | smokes:
        write(repo_root / "research" / "prognostics" / name)


def write_commit_json(path: Path, ready: bool) -> None:
    payload = {
        "commit_scope_ready_flag": int(ready),
        "risk_files": 0 if ready else 1,
        "issue_rows": 0 if ready else 1,
        "engine_source_dirty": 0,
        "large_data_dirty": 0,
        "release_generated_dirty": 0,
        "unclassified_dirty": 0,
        "canonical_truth_write_allowed_sum": 0,
        "truth_intake_allowed_sum": 0,
        "threshold_patch_allowed_sum": 0,
        "engine_patch_allowed_sum": 0,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "good"
        root.mkdir()
        write_supporting_files(root)
        queue = root / "queue.csv"
        commit_json = root / "commit.json"
        pd.DataFrame(queue_rows()).to_csv(queue, index=False, encoding="utf-8-sig")
        write_commit_json(commit_json, ready=True)
        good = run_builder(root, queue, commit_json, root / "out")
        assert good["queue_rows"] == 23
        assert good["completed_rows"] == 8
        assert good["blocked_rows"] == 15
        assert good["open_rows"] == 0
        assert good["issue_rows"] == 0
        assert good["blocked_state_handoff_ready_flag"] == 1

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "bad"
        root.mkdir()
        write_supporting_files(root)
        queue = root / "queue.csv"
        commit_json = root / "commit.json"
        pd.DataFrame(queue_rows(open_branch="BR-20260425-144")).to_csv(queue, index=False, encoding="utf-8-sig")
        write_commit_json(commit_json, ready=False)
        bad = run_builder(root, queue, commit_json, root / "out")
        assert bad["open_rows"] == 1
        assert bad["issue_rows"] >= 2
        assert bad["blocked_state_handoff_ready_flag"] == 0

    print(json.dumps({"smoke": "ok", "good_handoff_ready": 1, "bad_handoff_ready": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

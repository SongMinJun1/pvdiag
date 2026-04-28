#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BUILDER = ROOT / "research" / "prognostics" / "build_mlpe_field_trial_prelabel_runway_checkpoint_v1.py"

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


def run_builder(queue: Path, commit_json: Path, handoff_json: Path, out_dir: Path) -> dict[str, object]:
    result = subprocess.run(
        [
            "python3",
            str(BUILDER),
            "--repo-root",
            str(ROOT),
            "--queue-input",
            str(queue),
            "--commit-scope-json",
            str(commit_json),
            "--handoff-json",
            str(handoff_json),
            "--output-dir",
            str(out_dir),
        ],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def queue_rows(bad_open: bool = False, br150_complete: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for seq in range(1, 24):
        branch = f"BR-20260425-{127 + seq:03d}"
        if branch in EXPECTED_COMPLETE:
            status = "complete_this_branch"
        else:
            status = "blocked_waiting_fixture"
        if bad_open and branch == "BR-20260425-144":
            status = "open_now"
        if br150_complete and branch == "BR-20260425-150":
            status = "complete_this_branch"
        rows.append(
            {
                "branch": branch,
                "sequence_no": seq,
                "runway_stage": f"stage_{seq}",
                "status": status,
                "blocked_by": "fixture",
                "operator_facing_change": "no" if branch != "BR-20260425-144" else "yes_if_authorized",
            }
        )
    return rows


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def good_commit() -> dict[str, object]:
    return {
        "commit_scope_ready_flag": 1,
        "risk_files": 0,
        "issue_rows": 0,
        "engine_patch_allowed_sum": 0,
        "threshold_patch_allowed_sum": 0,
        "truth_intake_allowed_sum": 0,
        "canonical_truth_write_allowed_sum": 0,
    }


def good_handoff() -> dict[str, object]:
    return {
        "blocked_state_handoff_ready_flag": 1,
        "issue_rows": 0,
        "real_data_required_to_continue_flag": 1,
        "engine_patch_allowed_sum": 0,
        "threshold_patch_allowed_sum": 0,
        "truth_intake_allowed_sum": 0,
        "canonical_truth_write_allowed_sum": 0,
    }


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        queue = root / "queue.csv"
        commit_json = root / "commit.json"
        handoff_json = root / "handoff.json"
        pd.DataFrame(queue_rows()).to_csv(queue, index=False, encoding="utf-8-sig")
        write_json(commit_json, good_commit())
        write_json(handoff_json, good_handoff())
        good = run_builder(queue, commit_json, handoff_json, root / "good_out")
        assert good["checkpoint_rows"] == 8
        assert good["checkpoint_passed_rows"] == 8
        assert good["checkpoint_blocked_rows"] == 0
        assert good["prelabel_runway_checkpoint_ready_flag"] == 1
        assert good["algorithm_complete_claim_allowed_flag"] == 0

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        queue = root / "queue.csv"
        commit_json = root / "commit.json"
        handoff_json = root / "handoff.json"
        pd.DataFrame(queue_rows(bad_open=True, br150_complete=True)).to_csv(queue, index=False, encoding="utf-8-sig")
        bad_commit = good_commit()
        bad_commit["risk_files"] = 1
        bad_commit["commit_scope_ready_flag"] = 0
        bad_handoff = good_handoff()
        bad_handoff["blocked_state_handoff_ready_flag"] = 0
        write_json(commit_json, bad_commit)
        write_json(handoff_json, bad_handoff)
        bad = run_builder(queue, commit_json, handoff_json, root / "bad_out")
        assert bad["prelabel_runway_checkpoint_ready_flag"] == 0
        assert bad["checkpoint_blocked_rows"] >= 3
        assert bad["issue_rows"] >= 3

    print(json.dumps({"smoke": "ok", "good_checkpoint_ready": 1, "bad_checkpoint_ready": 0}, ensure_ascii=False))


if __name__ == "__main__":
    main()

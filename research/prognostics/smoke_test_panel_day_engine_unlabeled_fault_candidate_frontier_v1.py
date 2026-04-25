#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


COLUMNS = [
    "site",
    "panel_id",
    "strict_trigger_date",
    "first_warning_date",
    "retrospective_onset_date",
    "days_earlier_than_trigger",
    "onset_confidence",
    "onset_method",
    "reason_summary",
    "vendor_reply_class",
    "vendor_fault_family",
    "field_confirmed_flag",
    "dispute_type",
    "vendor_note",
    "review_priority",
    "reaudited_earliest_visible_date",
    "reaudited_first_warning_date",
    "field_estimated_start_date",
    "date_judgement",
    "failure_mode_judgement",
    "candidate_validity",
    "review_confidence",
    "note",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def row(
    panel_id: str,
    strict_date: str,
    days: int,
    method: str,
    confidence: str,
    candidate_validity: str = "",
) -> dict[str, object]:
    return {
        "site": "fixture",
        "panel_id": panel_id,
        "strict_trigger_date": strict_date,
        "first_warning_date": strict_date,
        "retrospective_onset_date": strict_date,
        "days_earlier_than_trigger": days,
        "onset_confidence": confidence,
        "onset_method": method,
        "reason_summary": "fixture",
        "vendor_reply_class": "",
        "vendor_fault_family": "",
        "field_confirmed_flag": "",
        "dispute_type": "",
        "vendor_note": "",
        "review_priority": "P2" if method == "persistent_5of7" else "P3",
        "reaudited_earliest_visible_date": "",
        "reaudited_first_warning_date": "",
        "field_estimated_start_date": "",
        "date_judgement": "",
        "failure_mode_judgement": "",
        "candidate_validity": candidate_validity,
        "review_confidence": "",
        "note": "fixture",
    }


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="unlabeled_fault_candidate_frontier_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        input_dir = tmp / "input"
        output_dir = tmp / "out"
        input_dir.mkdir()
        rows = [
            row("rootA.0.0", "2025-01-01", 45, "persistent_5of7", "high"),
            row("rootB.0.0", "2025-02-01", 0, "strict_trigger_fallback", "medium"),
            row("rootB.0.1", "2025-02-01", 0, "strict_trigger_fallback", "medium"),
            row("rootC.0.0", "2025-03-01", 0, "strict_trigger_fallback", "medium", "true_positive"),
            row("rootD.0.0", "2025-04-01", 0, "strict_trigger_fallback", "medium", "false_positive"),
        ]
        pd.DataFrame(rows).reindex(columns=COLUMNS).to_csv(
            input_dir / "panel_date_reaudit_working.csv",
            index=False,
            encoding="utf-8-sig",
        )

        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py",
            "--repo-root",
            str(repo_root),
            "--input-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["source_rows"] == 5, payload)
        assert_true(payload["priority_queue_rows"] == 3, payload)
        assert_true(payload["unlabeled_rows"] == 3, payload)
        assert_true(payload["strong_unlabeled_candidate_rows"] == 1, payload)
        assert_true(payload["strong_unlabeled_30d_plus_rows"] == 1, payload)
        assert_true(payload["trigger_only_bulk_screen_rows"] == 2, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)

        frontier = pd.read_csv(output_dir / "panel_day_engine_unlabeled_fault_candidate_frontier_v1.csv")
        buckets = set(frontier["data_candidate_bucket"])
        assert_true("U1_strong_persistent_lead_review" in buckets, buckets)
        assert_true("U3_trigger_only_common_cause_screen" in buckets, buckets)
        assert_true(int(frontier["truth_intake_allowed"].sum()) == 0, frontier)
        print(json.dumps({"smoke": "ok", "source_rows": int(len(frontier))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

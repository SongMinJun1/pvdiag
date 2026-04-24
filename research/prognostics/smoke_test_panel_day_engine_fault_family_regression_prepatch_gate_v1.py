#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_fault_family_regression_prepatch_gate_v1.csv"
SUMMARY_NAME = "panel_day_engine_fault_family_regression_prepatch_gate_summary_v1.csv"


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def packet_row(case_id: str, packet_bucket: str, counterexample_bucket: str, raw_top1: str, **overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "packet_case_id": case_id,
        "site": "test",
        "panel_id": case_id.lower(),
        "packet_bucket": packet_bucket,
        "counterexample_bucket": counterexample_bucket,
        "source_closure_class": "source",
        "evidence_grade": "grade",
        "raw_top1_ko": raw_top1,
        "same_day_fault_like_row_count": 0,
        "same_day_final_fault_row_count": 1,
        "same_day_common_cause_row_count": 0,
        "target_exact_top1_flag": 0,
        "target_exact_closure_candidate_flag": 0,
        "operator_promotion_allowed_flag": 0,
        "engine_patch_candidate_flag": 0,
        "expected_reading": "read as pressure only",
        "prohibited_overgeneralization": "do not promote",
        "regression_assertion": "must remain non-promoting",
        "recommended_next_action": "keep_packet",
    }
    row.update(overrides)
    return row


def valid_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(1, 6):
        rows.append(
            packet_row(
                f"BR058-{idx:03d}",
                "non_target_hard_same_day_fault_family_seed",
                "fault_family_boundary_pressure",
                "다이오드·서브스트링형",
            )
        )
    for idx in range(6, 12):
        rows.append(
            packet_row(
                f"BR058-{idx:03d}",
                "sensor_feedback_hard_same_day_ambiguity_pressure",
                "mlpe_ambiguous",
                "센서·피드백형",
                same_day_fault_like_row_count=1 if idx in {8, 9, 10} else 0,
            )
        )
    return rows


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        valid_input = root / "valid_packet.csv"
        valid_out = root / "valid_out"
        invalid_input = root / "invalid_packet.csv"
        invalid_out = root / "invalid_out"
        rows = valid_rows()
        write_csv(valid_input, rows)
        valid = run(
            [
                sys.executable,
                str(script),
                "--packet-input",
                str(valid_input),
                "--output-dir",
                str(valid_out),
            ],
            repo_root,
        )
        assert_true(valid.returncode == 0, valid.stderr or valid.stdout)
        valid_detail = pd.read_csv(valid_out / DETAIL_NAME, encoding="utf-8-sig")
        valid_summary = pd.read_csv(valid_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(set(valid_detail["status"]) == {"pass"}, valid_detail.to_string())
        assert_true(valid_summary.iloc[0]["overall_status"] == "pass", valid_summary.to_string())
        assert_true(int(valid_summary.iloc[0]["packet_rows"]) == 11, valid_summary.to_string())

        bad_rows = rows.copy()
        bad_rows[0] = dict(bad_rows[0], target_exact_closure_candidate_flag=1)
        write_csv(invalid_input, bad_rows)
        invalid = run(
            [
                sys.executable,
                str(script),
                "--packet-input",
                str(invalid_input),
                "--output-dir",
                str(invalid_out),
            ],
            repo_root,
        )
        assert_true(invalid.returncode != 0, "invalid packet unexpectedly passed")
        invalid_summary = pd.read_csv(invalid_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(invalid_summary.iloc[0]["overall_status"] == "fail", invalid_summary.to_string())

        allow_fail_out = root / "allow_fail_out"
        allow_fail = run(
            [
                sys.executable,
                str(script),
                "--packet-input",
                str(invalid_input),
                "--output-dir",
                str(allow_fail_out),
                "--allow-fail",
            ],
            repo_root,
        )
        assert_true(allow_fail.returncode == 0, allow_fail.stderr or allow_fail.stdout)


if __name__ == "__main__":
    main()

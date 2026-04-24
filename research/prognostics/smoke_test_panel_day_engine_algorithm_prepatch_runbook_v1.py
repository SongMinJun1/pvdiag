#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
import importlib.util

import pandas as pd


DETAIL_NAME = "panel_day_engine_algorithm_prepatch_runbook_v1.csv"
SUMMARY_NAME = "panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv"


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


def valid_packet_rows() -> list[dict[str, object]]:
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
            )
        )
    return rows


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def load_common_cause_smoke_helpers(repo_root: Path):
    helper_path = (
        repo_root
        / "research"
        / "prognostics"
        / "smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py"
    )
    spec = importlib.util.spec_from_file_location("common_cause_semantic_gate_smoke", helper_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load helper smoke module: {helper_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def common_args(paths: dict[str, Path]) -> list[str]:
    return [
        "--common-cause-strong-blocker-input",
        str(paths["strong"]),
        "--common-cause-exact-search-input",
        str(paths["exact"]),
        "--common-cause-structural-input",
        str(paths["structural"]),
        "--common-cause-trace-input",
        str(paths["trace"]),
    ]


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    common_helpers = load_common_cause_smoke_helpers(repo_root)
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "check_panel_day_engine_algorithm_prepatch_runbook_v1.py"
    )
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        changed_paths = root / "empty_changed_paths.txt"
        changed_paths.write_text("", encoding="utf-8")
        packet = root / "valid_packet.csv"
        write_csv(packet, valid_packet_rows())
        common_paths = common_helpers.write_valid_inputs(root / "common_valid")
        out_root = root / "out"
        valid = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--changed-paths-file",
                str(changed_paths),
                "--packet-input",
                str(packet),
                *common_args(common_paths),
                "--output-dir",
                str(out_root),
            ],
            repo_root,
        )
        assert_true(valid.returncode == 0, valid.stderr or valid.stdout)
        detail = pd.read_csv(out_root / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(out_root / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(set(detail["overall_status"]) == {"pass"}, detail.to_string())
        assert_true(summary.iloc[0]["overall_status"] == "pass", summary.to_string())
        assert_true(int(summary.iloc[0]["gate_count"]) == 3, summary.to_string())
        assert_true(int(summary.iloc[0]["fault_family_packet_rows"]) == 11, summary.to_string())
        assert_true(summary.iloc[0]["common_cause_gate_status"] == "pass", summary.to_string())
        assert_true(int(summary.iloc[0]["common_cause_required_gate_count"]) == 12, summary.to_string())
        assert_true(int(summary.iloc[0]["common_cause_warn_gate_count"]) == 1, summary.to_string())

        bad_packet = root / "bad_packet.csv"
        bad_rows = valid_packet_rows()
        bad_rows[0] = dict(bad_rows[0], target_exact_closure_candidate_flag=1)
        write_csv(bad_packet, bad_rows)
        bad_out = root / "bad_out"
        invalid = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--changed-paths-file",
                str(changed_paths),
                "--packet-input",
                str(bad_packet),
                *common_args(common_paths),
                "--output-dir",
                str(bad_out),
            ],
            repo_root,
        )
        assert_true(invalid.returncode != 0, "invalid runbook unexpectedly passed")
        bad_summary = pd.read_csv(bad_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(bad_summary.iloc[0]["overall_status"] == "fail", bad_summary.to_string())

        allow_fail_out = root / "allow_fail_out"
        allow_fail = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--changed-paths-file",
                str(changed_paths),
                "--packet-input",
                str(bad_packet),
                *common_args(common_paths),
                "--output-dir",
                str(allow_fail_out),
                "--allow-fail",
            ],
            repo_root,
        )
        assert_true(allow_fail.returncode == 0, allow_fail.stderr or allow_fail.stdout)

        bad_common_paths = common_helpers.write_valid_inputs(root / "common_bad")
        bad_trace = pd.read_csv(bad_common_paths["trace"], encoding="utf-8-sig")
        bad_trace.loc[0, "semantic_patch_candidate_flag"] = 1
        bad_trace.to_csv(bad_common_paths["trace"], index=False, encoding="utf-8-sig")
        bad_common_out = root / "bad_common_out"
        bad_common = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(repo_root),
                "--changed-paths-file",
                str(changed_paths),
                "--packet-input",
                str(packet),
                *common_args(bad_common_paths),
                "--output-dir",
                str(bad_common_out),
            ],
            repo_root,
        )
        assert_true(bad_common.returncode != 0, "invalid common-cause drift unexpectedly passed")
        bad_common_summary = pd.read_csv(bad_common_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(bad_common_summary.iloc[0]["overall_status"] == "fail", bad_common_summary.to_string())


if __name__ == "__main__":
    main()

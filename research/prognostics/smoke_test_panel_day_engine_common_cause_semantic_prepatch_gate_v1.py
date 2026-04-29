#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_v1.csv"
SUMMARY_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_summary_v1.csv"
NOTE_NAME = "panel_day_engine_common_cause_semantic_prepatch_gate_note_v1.md"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def strong_blocker_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(1, 51):
        rows.append(
            {
                "blocker_case_id": f"BR071-{idx:03d}",
                "site": "gangui" if idx <= 20 else "ktc_ess",
                "panel_id": f"root.{idx}.1",
                "panel_root_id": f"root.{idx}",
                "common_cause_blocker_type": "group_off_synchrony_blocker" if idx <= 20 else "site_event_synchrony_blocker",
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "panel_local_promotion_blocked_flag": 1,
                "regression_seed_flag": 1,
                "review_note": "common-cause blocker regression seed only",
            }
        )
    return rows


def exact_search_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx in range(1, 177):
        is_structural = idx <= 49
        is_regression = 50 <= idx < 100
        raw_rows = 5 if idx == 49 else (2 if is_structural else 0)
        rows.append(
            {
                "search_case_id": f"BR072-{idx:03d}",
                "site": "gangui" if idx <= 90 else "ktc_ess",
                "panel_id": f"root.{idx}.1",
                "exact_family_closure_flag": 0,
                "candidate_reservoir_flag": 1 if is_structural else 0,
                "structural_blocker_flag": 1 if is_structural else 0,
                "blocker_regression_seed_flag": 1 if is_regression else 0,
                "raw_direct_common_cause_row_count": raw_rows,
                "official_current_same_day_overlap_flag": 0,
                "operator_promotion_allowed_flag": 0,
                "engine_patch_candidate_flag": 0,
                "threshold_patch_allowed_flag": 0,
                "allowed_use": "candidate reservoir or hold evidence only",
                "still_missing": "official/current same-day closure",
                "review_note": "not semantic closure",
            }
        )
    rows[0]["blocker_regression_seed_flag"] = 1
    return rows


def structural_rows() -> list[dict[str, object]]:
    subtype_counts = [
        ("no_report_lane_entry", 13),
        ("precursor_carryover_without_current_closure", 19),
        ("rawonly_date_displaced_without_current_closure", 15),
        ("rawonly_near_signal_anchor", 1),
        ("official_current_date_displaced", 1),
    ]
    rows: list[dict[str, object]] = []
    idx = 1
    for subtype, count in subtype_counts:
        for _ in range(count):
            is_manual = subtype in {"rawonly_near_signal_anchor", "official_current_date_displaced"}
            rows.append(
                {
                    "review_case_id": f"BR073-{idx:03d}",
                    "source_search_case_id": f"BR072-{idx:03d}",
                    "site": "gangui" if idx <= 25 else "ktc_ess",
                    "panel_id": f"root.{idx}.1",
                    "structural_blocker_subtype": subtype,
                    "manual_trace_review_flag": 1 if is_manual else 0,
                    "structural_patch_target_review_flag": 1 if is_manual else 0,
                    "operator_promotion_allowed_flag": 0,
                    "engine_patch_candidate_flag": 0,
                    "threshold_patch_allowed_flag": 0,
                    "official_current_same_day_overlap_flag": 0,
                    "required_next_evidence": "report-layer same-day closure",
                    "review_note": "structural blocker only",
                }
            )
            idx += 1
    return rows


def trace_rows() -> list[dict[str, object]]:
    return [
        {
            "trace_case_id": "BR074-001",
            "source_review_case_id": "BR073-048",
            "source_search_case_id": "BR072-048",
            "site": "gangui",
            "panel_id": "root.48.1",
            "trace_outcome_bucket": "rawonly_near_anchor_trace_only",
            "trace_bridge_scope": "rawonly_report_near_anchor",
            "rawonly_report_bridge_candidate_flag": 1,
            "official_current_bridge_candidate_flag": 0,
            "semantic_patch_candidate_flag": 0,
            "operator_promotion_allowed_flag": 0,
            "engine_patch_candidate_flag": 0,
            "threshold_patch_allowed_flag": 0,
            "nearest_official_current_signed_gap_days": "",
            "nearest_rawonly_signal_signed_gap_days": 2,
            "required_next_evidence": "trace raw-only report generation only",
            "review_note": "raw-only trace, not official/current closure",
        },
        {
            "trace_case_id": "BR074-002",
            "source_review_case_id": "BR073-049",
            "source_search_case_id": "BR072-049",
            "site": "ktc_ess",
            "panel_id": "root.49.1",
            "trace_outcome_bucket": "post_current_common_cause_late_event_hold",
            "trace_bridge_scope": "official_current_mismatch",
            "rawonly_report_bridge_candidate_flag": 0,
            "official_current_bridge_candidate_flag": 0,
            "semantic_patch_candidate_flag": 0,
            "operator_promotion_allowed_flag": 0,
            "engine_patch_candidate_flag": 0,
            "threshold_patch_allowed_flag": 0,
            "nearest_official_current_signed_gap_days": 71,
            "nearest_rawonly_signal_signed_gap_days": 71,
            "required_next_evidence": "independent report-date correction",
            "review_note": "post-current mismatch, not closure",
        },
    ]


def run_gate(
    repo_root: Path,
    paths: dict[str, Path],
    out_dir: Path,
    allow_fail: bool = False,
    use_manifest: bool = True,
) -> subprocess.CompletedProcess[str]:
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py"
    )
    cmd = [
        sys.executable,
        str(script),
    ]
    if use_manifest:
        manifest_path = out_dir.parent / f"{out_dir.name}_input_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "strong_blocker_input": str(paths["strong"]),
                        "exact_search_input": str(paths["exact"]),
                        "structural_input": str(paths["structural"]),
                        "trace_input": str(paths["trace"]),
                    }
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        cmd.extend(["--input-manifest", str(manifest_path)])
    else:
        cmd.extend(
            [
                "--strong-blocker-input",
                str(paths["strong"]),
                "--exact-search-input",
                str(paths["exact"]),
                "--structural-input",
                str(paths["structural"]),
                "--trace-input",
                str(paths["trace"]),
            ]
        )
    cmd.extend(["--output-dir", str(out_dir)])
    if allow_fail:
        cmd.append("--allow-fail")
    return subprocess.run(cmd, cwd=repo_root, text=True, capture_output=True)


def write_valid_inputs(root: Path) -> dict[str, Path]:
    paths = {
        "strong": root / "strong.csv",
        "exact": root / "exact.csv",
        "structural": root / "structural.csv",
        "trace": root / "trace.csv",
    }
    write_csv(paths["strong"], strong_blocker_rows())
    write_csv(paths["exact"], exact_search_rows())
    write_csv(paths["structural"], structural_rows())
    write_csv(paths["trace"], trace_rows())
    return paths


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="common_cause_semantic_gate_") as tmp_dir:
        root = Path(tmp_dir)
        valid_paths = write_valid_inputs(root / "valid")
        valid_out = root / "valid_out"
        valid = run_gate(repo_root, valid_paths, valid_out)
        assert_true(valid.returncode == 0, valid.stderr or valid.stdout)
        valid_detail = pd.read_csv(valid_out / DETAIL_NAME, encoding="utf-8-sig")
        valid_summary = pd.read_csv(valid_out / SUMMARY_NAME, encoding="utf-8-sig")
        note = (valid_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(valid_summary.iloc[0]["overall_status"] == "pass", valid_summary.to_string())
        assert_true(int(valid_summary.iloc[0]["failed_required_gate_count"]) == 0, valid_detail.to_string())
        assert_true(int(valid_summary.iloc[0]["trace_rows"]) == 2, valid_summary.to_string())
        assert_true("Passing this gate does not approve" in note, "note missing approval boundary")
        assert_true("`strong_blocker_input`: `input_manifest`" in note, "note missing manifest source")
        assert_true("`trace_input`: `input_manifest`" in note, "note missing trace manifest source")

        invalid_root = root / "invalid"
        invalid_paths = write_valid_inputs(invalid_root)
        invalid_trace = pd.read_csv(invalid_paths["trace"], encoding="utf-8-sig")
        invalid_trace.loc[0, "semantic_patch_candidate_flag"] = 1
        invalid_trace.to_csv(invalid_paths["trace"], index=False, encoding="utf-8-sig")
        invalid_out = root / "invalid_out"
        invalid = run_gate(repo_root, invalid_paths, invalid_out)
        assert_true(invalid.returncode != 0, "invalid semantic drift unexpectedly passed")
        invalid_summary = pd.read_csv(invalid_out / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(invalid_summary.iloc[0]["overall_status"] == "fail", invalid_summary.to_string())

        allow_fail = run_gate(repo_root, invalid_paths, root / "allow_fail_out", allow_fail=True)
        assert_true(allow_fail.returncode == 0, allow_fail.stderr or allow_fail.stdout)

    print("smoke ok: panel_day_engine_common_cause_semantic_prepatch_gate_v1")


if __name__ == "__main__":
    main()

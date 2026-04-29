#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_common_cause_structural_blocker_review_v1.csv"
SUMMARY_NAME = "panel_day_engine_common_cause_structural_blocker_review_summary_v1.csv"
SITE_SUMMARY_NAME = "panel_day_engine_common_cause_structural_blocker_site_summary_v1.csv"
NOTE_NAME = "panel_day_engine_common_cause_structural_blocker_review_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def detail_row(
    search_case_id: str,
    panel_id: str,
    lane: str,
    best_lane: str,
    blocker: str,
    current_flag: int,
    current_dates: str,
    gap: str,
) -> str:
    values = [
        search_case_id,
        f"BR064-{search_case_id[-3:]}",
        "site_a",
        panel_id,
        ".".join(panel_id.split(".")[:-1]),
        "structural_blocker",
        "block_panel_local_promotion_regression_seed",
        "raw_direct_row_but_report_layer_misaligned",
        0,
        1,
        1,
        0,
        1,
        1,
        "2026-01-10",
        "site_event_soft",
        current_flag,
        current_dates,
        0,
        gap,
        int(lane != "none"),
        lane,
        best_lane,
        "site_event_synchrony",
        "site_event_synchrony__" + best_lane,
        1,
        1,
        0,
        0,
        0.25,
        blocker,
        1,
        0,
        1,
        0,
        0,
        0,
        "patch-target selection and blocker split only",
        "report-layer same-day closure or explicit lane/date-alignment resolution",
        "test row",
    ]
    return ",".join(str(value) for value in values)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_common_cause_structural_blocker_review_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="common_cause_structural_blocker_") as tmp_dir:
        root = Path(tmp_dir)
        input_csv = root / "exact_seed.csv"
        input_manifest = root / "input_manifest.json"
        out_dir = root / "out"
        header = [
            "search_case_id",
            "source_candidate_case_id",
            "site",
            "panel_id",
            "panel_root_id",
            "primary_judgment_role",
            "usage_tag",
            "common_cause_search_bucket",
            "exact_family_closure_flag",
            "candidate_reservoir_flag",
            "structural_blocker_flag",
            "supportive_hint_flag",
            "blocker_regression_seed_flag",
            "raw_direct_common_cause_row_count",
            "raw_direct_common_cause_dates",
            "raw_direct_common_cause_family",
            "official_current_entry_flag",
            "official_current_dates",
            "official_current_same_day_overlap_flag",
            "nearest_official_current_gap_days",
            "any_report_lane_entry_flag",
            "report_lane_presence",
            "best_report_lane",
            "synchrony_bucket",
            "synchrony_lane_bucket",
            "common_cause_row_count",
            "site_event_row_count",
            "group_off_row_count",
            "subgroup_common_cause_row_count",
            "max_co_drop_frac",
            "friction_blocker_types",
            "friction_direct_row_count",
            "friction_group_off_row_count",
            "friction_site_event_row_count",
            "operator_promotion_allowed_flag",
            "engine_patch_candidate_flag",
            "threshold_patch_allowed_flag",
            "allowed_use",
            "still_missing",
            "review_note",
        ]
        lines = [
            ",".join(header),
            detail_row("BR072-001", "root.0.1", "official_current|rawonly_signal", "official_current", "current_date_displaced", 1, "2026-02-01", "22"),
            detail_row("BR072-002", "root.0.2", "rawonly_signal", "rawonly_current", "rawonly_near_signal_anchor", 0, "", ""),
            detail_row("BR072-003", "root.0.3", "none", "none", "no_report_lane_entry", 0, "", ""),
            detail_row("BR072-004", "root.0.4", "precursor", "precursor", "precursor_carryover_without_exact_overlap", 0, "", ""),
            detail_row("BR072-005", "root.0.5", "rawonly_signal", "rawonly_current", "rawonly_date_displaced", 0, "", ""),
            detail_row("BR072-006", "root.0.6", "none", "none", "no_report_lane_entry", 0, "", "").replace(
                "structural_blocker", "supportive_hint", 1
            ),
        ]
        write_text(input_csv, "\n".join(lines) + "\n")
        write_text(
            input_manifest,
            json.dumps({"inputs": {"exact_seed_input": str(input_csv)}}, indent=2) + "\n",
        )
        result = subprocess.run(
            [
                "python3",
                str(script),
                "--input-manifest",
                str(input_manifest),
                "--output-dir",
                str(out_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(result.returncode == 0, f"builder failed:\nSTDOUT={result.stdout}\nSTDERR={result.stderr}")
        detail = pd.read_csv(out_dir / DETAIL_NAME, low_memory=False)
        summary = pd.read_csv(out_dir / SUMMARY_NAME, low_memory=False)
        site_summary = pd.read_csv(out_dir / SITE_SUMMARY_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        by_panel = detail.set_index("panel_id")
        assert_true(len(detail) == 5, f"unexpected rows: {len(detail)}")
        assert_true(by_panel.loc["root.0.1", "structural_blocker_subtype"] == "official_current_date_displaced", detail.to_string())
        assert_true(by_panel.loc["root.0.2", "structural_blocker_subtype"] == "rawonly_near_signal_anchor", detail.to_string())
        assert_true(by_panel.loc["root.0.3", "structural_blocker_subtype"] == "no_report_lane_entry", detail.to_string())
        assert_true(
            by_panel.loc["root.0.4", "structural_blocker_subtype"] == "precursor_carryover_without_current_closure",
            detail.to_string(),
        )
        assert_true(
            by_panel.loc["root.0.5", "structural_blocker_subtype"] == "rawonly_date_displaced_without_current_closure",
            detail.to_string(),
        )
        assert_true(int(detail["manual_trace_review_flag"].sum()) == 2, detail.to_string())
        assert_true(int(detail["structural_patch_target_review_flag"].sum()) == 2, detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")
        assert_true(len(summary) == 5, summary.to_string())
        assert_true(int(site_summary["raw_direct_common_cause_rows"].sum()) == 5, site_summary.to_string())
        assert_true("manual trace review targets: `2`" in note, "note missing manual trace count")
        assert_true("`exact_seed_input`: `input_manifest`" in note, "note missing manifest source")
    print("smoke ok: panel_day_engine_common_cause_structural_blocker_review_v1")


if __name__ == "__main__":
    main()

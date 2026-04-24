#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


SHAPE_COLUMNS = [
    "shape_review_row_id",
    "shape_review_decision",
    "shape_confidence",
    "reviewer_truth_label",
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_track",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "window_day_rows",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "threshold_replay_input_allowed_candidate",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

TRUTH_COLUMNS = [
    "reviewed_truth_row_id",
    "review_packet_id",
    "review_status",
    "truth_role",
    "threshold_replay_input_allowed",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def shape_row(
    row_id: str,
    decision: str,
    label: str,
    positive: int,
    negative: int,
    gap_days: int,
    window_signal_days: int,
    event_a_days: int,
    low_mid_days: int,
    vlow_iok_days: int,
    hard_anchor_days: int,
) -> dict[str, object]:
    idx = row_id.rsplit("-", 1)[-1]
    return {
        "shape_review_row_id": row_id,
        "shape_review_decision": decision,
        "shape_confidence": "fixture",
        "reviewer_truth_label": label,
        "reviewed_truth_row_id": f"BR084-RTR-{idx}",
        "review_packet_id": f"BR082-EPR-{idx}",
        "review_track": "fixture_track",
        "site": "conalog",
        "panel_id": f"panel.{idx}",
        "episode_anchor_date": "2025-01-01",
        "strict_trigger_date": "2025-01-21",
        "gap_days": gap_days,
        "window_day_rows": max(gap_days + 1, 21),
        "window_signal_days": window_signal_days,
        "event_A_days": event_a_days,
        "low_mid_days": low_mid_days,
        "voltage_low_current_ok_days": vlow_iok_days,
        "hard_anchor_days": hard_anchor_days,
        "common_cause_days": 0,
        "data_bad_days": 0,
        "median_signal_mid_v_ratio": 0.65 if positive else 0.95,
        "median_signal_mid_i_ratio": 0.97,
        "positive_replay_candidate": positive,
        "negative_replay_candidate": negative,
        "threshold_replay_input_allowed_candidate": 1 if positive or negative else 0,
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": 0,
        "threshold_patch_allowed": 0,
    }


def truth_row(row: dict[str, object], unsafe_engine_patch: int = 0) -> dict[str, object]:
    positive = int(row["positive_replay_candidate"])
    negative = int(row["negative_replay_candidate"])
    return {
        "reviewed_truth_row_id": row["reviewed_truth_row_id"],
        "review_packet_id": row["review_packet_id"],
        "review_status": "reviewed_positive" if positive else ("reviewed_negative" if negative else "needs_evidence"),
        "truth_role": "positive_precursor_truth"
        if positive
        else ("negative_counterexample" if negative else "unassigned"),
        "threshold_replay_input_allowed": int(row["threshold_replay_input_allowed_candidate"]),
        "operator_facing_change_allowed": 0,
        "engine_patch_allowed": unsafe_engine_patch,
        "threshold_patch_allowed": 0,
    }


def build_fixture(tmp_root: Path) -> tuple[Path, Path, Path]:
    shape_rows = [
        shape_row(
            "BR090-FIX-001",
            "fill_positive_durable_voltage_precursor",
            "real_precursor",
            positive=1,
            negative=0,
            gap_days=20,
            window_signal_days=21,
            event_a_days=21,
            low_mid_days=21,
            vlow_iok_days=20,
            hard_anchor_days=1,
        ),
        shape_row(
            "BR090-FIX-002",
            "carry_forward_negative_counterexample",
            "episode_only_or_backdating",
            positive=0,
            negative=1,
            gap_days=270,
            window_signal_days=3,
            event_a_days=2,
            low_mid_days=2,
            vlow_iok_days=1,
            hard_anchor_days=1,
        ),
        shape_row(
            "BR090-FIX-003",
            "defer_durable_shape_hold",
            "",
            positive=0,
            negative=0,
            gap_days=49,
            window_signal_days=5,
            event_a_days=4,
            low_mid_days=2,
            vlow_iok_days=0,
            hard_anchor_days=1,
        ),
    ]
    shape_path = tmp_root / "shape.csv"
    truth_path = tmp_root / "truth.csv"
    threshold_path = tmp_root / "threshold.csv"
    write_csv(shape_path, shape_rows, SHAPE_COLUMNS)
    write_csv(truth_path, [truth_row(row) for row in shape_rows], TRUTH_COLUMNS)
    write_csv(
        threshold_path,
        [
            {
                "axis": "duration",
                "feature": "fixture",
                "promote_candidate": 1,
                "hold_or_block": "fixture",
            }
        ],
        ["axis", "feature", "promote_candidate", "hold_or_block"],
    )
    return shape_path, truth_path, threshold_path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_subtype_threshold_replay_pilot_v1.py"
    with tempfile.TemporaryDirectory(prefix="br090_threshold_replay_smoke_") as tmp:
        tmp_root = Path(tmp)
        shape_path, truth_path, threshold_path = build_fixture(tmp_root)
        output_dir = tmp_root / "out"
        result = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--shape-input",
                str(shape_path),
                "--reviewed-truth-input",
                str(truth_path),
                "--threshold-candidate-input",
                str(threshold_path),
                "--output-dir",
                str(output_dir),
            ],
            cwd=repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        summary = pd.read_csv(
            output_dir / "panel_day_engine_subtype_threshold_replay_pilot_summary_v1.csv",
            encoding="utf-8-sig",
        )
        cases = pd.read_csv(
            output_dir / "panel_day_engine_subtype_threshold_replay_pilot_cases_v1.csv",
            encoding="utf-8-sig",
        )
        payload = json.loads(
            (output_dir / "panel_day_engine_subtype_threshold_replay_pilot_v1.json").read_text(encoding="utf-8")
        )

        assert_true(len(summary) == 7, summary.to_string())
        assert_true(len(cases) == 21, cases.to_string())
        assert_true(int(summary["threshold_tuning_approved"].sum()) == 0, summary.to_string())
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        by_rule = summary.set_index("rule_id")
        assert_true(
            by_rule.loc["duration_gap_eventA_2d", "pilot_decision"]
            == "blocked_hold_pressure_and_insufficient_support",
            by_rule.loc["duration_gap_eventA_2d"].to_dict(),
        )
        assert_true(
            int(by_rule.loc["duration_gap_eventA_2d", "deferred_hold_hits"]) == 1,
            by_rule.loc["duration_gap_eventA_2d"].to_dict(),
        )
        assert_true(
            by_rule.loc["voltage_preserved_gap_vlow_iok_2d", "pilot_decision"]
            == "pilot_candidate_collect_more_positive_truth",
            by_rule.loc["voltage_preserved_gap_vlow_iok_2d"].to_dict(),
        )
        assert_true(
            int(by_rule.loc["voltage_preserved_gap_vlow_iok_2d", "false_positive_hits"]) == 0,
            by_rule.loc["voltage_preserved_gap_vlow_iok_2d"].to_dict(),
        )

        unsafe_truth = tmp_root / "truth_unsafe.csv"
        base_truth = [truth_row(row) for row in pd.read_csv(shape_path, encoding="utf-8-sig").to_dict(orient="records")]
        base_truth[0]["engine_patch_allowed"] = 1
        write_csv(unsafe_truth, base_truth, TRUTH_COLUMNS)
        unsafe = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--shape-input",
                str(shape_path),
                "--reviewed-truth-input",
                str(unsafe_truth),
                "--threshold-candidate-input",
                str(threshold_path),
                "--output-dir",
                str(tmp_root / "unsafe_out"),
            ],
            cwd=repo_root,
        )
        assert_true(unsafe.returncode != 0, "unsafe input should fail")
        assert_true("engine_patch_allowed sum is 1" in (unsafe.stderr + unsafe.stdout), unsafe.stderr + unsafe.stdout)

    print("smoke ok: panel_day_engine_subtype_threshold_replay_pilot_v1")


if __name__ == "__main__":
    main()

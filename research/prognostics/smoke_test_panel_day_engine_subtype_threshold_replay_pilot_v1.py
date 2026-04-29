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
        note = (output_dir / "panel_day_engine_subtype_threshold_replay_pilot_note_v1.md").read_text(encoding="utf-8")

        assert_true(len(summary) == 7, summary.to_string())
        assert_true(len(cases) == 21, cases.to_string())
        assert_true(int(summary["threshold_tuning_approved"].sum()) == 0, summary.to_string())
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)
        assert_true(payload["input_manifest"] == "not provided", payload)
        assert_true(payload["input_resolution_sources"]["shape_input"] == "explicit_cli", payload)
        assert_true(payload["input_resolution_sources"]["reviewed_truth_input"] == "explicit_cli", payload)
        assert_true("evidence input manifest: `not provided`" in note, "note missing no-manifest marker")
        assert_true("`shape_input`: `explicit_cli`" in note, "note missing explicit shape source")
        assert_true("`reviewed_truth_input`: `explicit_cli`" in note, "note missing explicit truth source")

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

        manifest = tmp_root / "threshold_replay_inputs.json"
        manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "shape_input": str(shape_path),
                        "reviewed_truth_input": str(truth_path),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = tmp_root / "manifest_out"
        manifest_result = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest),
                "--threshold-candidate-input",
                str(threshold_path),
                "--output-dir",
                str(manifest_out),
            ],
            cwd=repo_root,
        )
        assert_true(manifest_result.returncode == 0, manifest_result.stderr or manifest_result.stdout)
        manifest_summary = pd.read_csv(
            manifest_out / "panel_day_engine_subtype_threshold_replay_pilot_summary_v1.csv",
            encoding="utf-8-sig",
        )
        manifest_payload = json.loads(
            (manifest_out / "panel_day_engine_subtype_threshold_replay_pilot_v1.json").read_text(encoding="utf-8")
        )
        manifest_note = (manifest_out / "panel_day_engine_subtype_threshold_replay_pilot_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(
            manifest_summary["pilot_decision"].tolist() == summary["pilot_decision"].tolist(),
            "manifest pilot decisions drifted",
        )
        assert_true(manifest_payload["input_manifest"] == str(manifest), manifest_payload)
        assert_true(manifest_payload["input_resolution_sources"]["shape_input"] == "input_manifest", manifest_payload)
        assert_true(
            manifest_payload["input_resolution_sources"]["reviewed_truth_input"] == "input_manifest",
            manifest_payload,
        )
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, "note missing manifest path")
        assert_true("`shape_input`: `input_manifest`" in manifest_note, "note missing manifest shape source")
        assert_true("`reviewed_truth_input`: `input_manifest`" in manifest_note, "note missing manifest truth source")

        bad_manifest = tmp_root / "bad_threshold_replay_inputs.json"
        bad_manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "shape_input": str(tmp_root / "missing_shape.csv"),
                        "reviewed_truth_input": str(tmp_root / "missing_truth.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = tmp_root / "override_out"
        override_result = run(
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
                "--input-manifest",
                str(bad_manifest),
                "--output-dir",
                str(override_out),
            ],
            cwd=repo_root,
        )
        assert_true(override_result.returncode == 0, override_result.stderr or override_result.stdout)
        override_payload = json.loads(
            (override_out / "panel_day_engine_subtype_threshold_replay_pilot_v1.json").read_text(encoding="utf-8")
        )
        assert_true(override_payload["input_resolution_sources"]["shape_input"] == "explicit_cli", override_payload)
        assert_true(
            override_payload["input_resolution_sources"]["reviewed_truth_input"] == "explicit_cli",
            override_payload,
        )

        missing_key_manifest = tmp_root / "missing_key_threshold_replay_inputs.json"
        missing_key_manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "shape_input": str(shape_path),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        missing_key_result = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest),
                "--threshold-candidate-input",
                str(threshold_path),
                "--output-dir",
                str(tmp_root / "missing_key_out"),
            ],
            cwd=repo_root,
        )
        assert_true(missing_key_result.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `reviewed_truth_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr + missing_key_result.stdout,
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

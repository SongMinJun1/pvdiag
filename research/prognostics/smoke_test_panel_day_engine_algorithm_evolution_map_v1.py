#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


LAYER_NAME = "panel_day_engine_algorithm_evolution_layer_map_v1.csv"
GAP_NAME = "panel_day_engine_algorithm_evolution_gap_audit_v1.csv"
ACTION_NAME = "panel_day_engine_algorithm_evolution_action_queue_v1.csv"
SUMMARY_NAME = "panel_day_engine_algorithm_evolution_summary_v1.csv"
NOTE_NAME = "panel_day_engine_algorithm_evolution_note_v1.md"
JSON_NAME = "panel_day_engine_algorithm_evolution_map_v1.json"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research/prognostics/build_panel_day_engine_algorithm_evolution_map_v1.py"

    with tempfile.TemporaryDirectory(prefix="algorithm_evolution_map_smoke_") as tmpdir:
        output_dir = Path(tmpdir) / "out"
        cmd = [
            sys.executable,
            str(script),
            "--repo-root",
            str(repo_root),
            "--output-dir",
            str(output_dir),
            "--owner-branch",
            "BR-TEST-079",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        layer_df = pd.read_csv(output_dir / LAYER_NAME, encoding="utf-8-sig")
        gap_df = pd.read_csv(output_dir / GAP_NAME, encoding="utf-8-sig")
        action_df = pd.read_csv(output_dir / ACTION_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        note_text = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        required_layers = {
            "train_only_vbin_reference",
            "ae_reconstruction_anomaly",
            "group_off_common_cause_gate",
            "vdrop_critical_like_ssot",
            "final_fault_confirmation",
            "ews_local_precursor",
            "site_event_context",
            "prefault_b_template",
        }
        actual_layers = set(layer_df["layer_id"].astype(str))
        assert_true(required_layers.issubset(actual_layers), f"missing layers: {required_layers - actual_layers}")
        assert_true((layer_df["owner_branch"] == "BR-TEST-079").all(), layer_df.to_string())
        assert_true(layer_df["engine_location_hint"].astype(str).str.contains("pv_ae/panel_day_engine.py:").all(), layer_df.to_string())
        assert_true(not layer_df["engine_location_hint"].astype(str).str.contains("MISSING_PATTERN").any(), layer_df.to_string())

        for frame_name, frame in {
            "layer": layer_df,
            "gap": gap_df,
            "action": action_df,
        }.items():
            assert_true(int(frame["operator_facing_change_allowed"].sum()) == 0, f"{frame_name} operator change allowed")
            assert_true(int(frame["engine_patch_allowed"].sum()) == 0, f"{frame_name} engine patch allowed")
            assert_true(int(frame["threshold_patch_allowed"].sum()) == 0, f"{frame_name} threshold patch allowed")

        p0_gaps = set(gap_df.loc[gap_df["priority"].eq("P0"), "gap_id"].astype(str))
        assert_true({"GAP-001", "GAP-002", "GAP-003", "GAP-004"}.issubset(p0_gaps), gap_df.to_string())
        assert_true(action_df["sequence"].tolist() == sorted(action_df["sequence"].tolist()), action_df.to_string())
        assert_true(action_df.iloc[0]["action_id"] == "ACT-001", action_df.to_string())
        assert_true("subtype_truth_expansion" in str(action_df.iloc[1]["entrypoint_or_artifact"]), action_df.to_string())

        summary = dict(zip(summary_df["metric"], summary_df["value"], strict=False))
        assert_true(int(summary["mapped_layer_count"]) == len(layer_df), summary_df.to_string())
        assert_true(int(summary["engine_patch_allowed_sum"]) == 0, summary_df.to_string())
        assert_true(int(summary["threshold_patch_allowed_sum"]) == 0, summary_df.to_string())

        assert_true(payload["layer_count"] == len(layer_df), payload)
        assert_true(payload["gap_count"] == len(gap_df), payload)
        assert_true(payload["engine_patch_allowed_sum"] == 0, payload)
        assert_true(payload["recommended_next_branch"] == "panel_day_engine_subtype_truth_expansion_backlog_v1", payload)
        assert_true("BR-076 3-gate prepatch runbook" in note_text, note_text)

    print("smoke_test_panel_day_engine_algorithm_evolution_map_v1.py: PASS")


if __name__ == "__main__":
    main()

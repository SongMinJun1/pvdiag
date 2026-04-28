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
    "reviewed_truth_row_id",
    "review_packet_id",
    "site",
    "panel_id",
    "episode_anchor_date",
    "strict_trigger_date",
    "gap_days",
    "window_signal_days",
    "event_A_days",
    "low_mid_days",
    "voltage_low_current_ok_days",
    "current_low_voltage_ok_days",
    "both_low_vi_days",
    "hard_anchor_days",
    "common_cause_days",
    "data_bad_days",
    "median_signal_mid_v_ratio",
    "median_signal_mid_i_ratio",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

CORE_COLUMNS = [
    "date",
    "panel_id",
    "source_csv",
    "event_A",
    "is_ae_abn",
    "is_ae_strong",
    "re_drop",
    "fault_like_day",
    "critical_fault",
    "final_fault",
    "degraded_candidate",
    "data_bad",
    "mid_ratio",
    "mid_v_ratio",
    "mid_i_ratio",
    "dtw_dist",
    "co_drop_frac",
]


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    if columns is not None:
        df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def raw_rows(date: str, target: str, peer: str, shape: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for hour in [11, 12, 13, 14]:
        peer_v = 10.0
        peer_i = 10.0
        if shape == "current_limited":
            target_v = 10.0
            target_i = 5.0
        elif shape == "voltage_preserved":
            target_v = 5.0
            target_i = 10.0
        else:
            target_v = 9.5
            target_i = 9.5
        for pid, v, i in [(target, target_v, target_i), (peer, peer_v, peer_i)]:
            rows.append(
                {
                    "date_time": f"{date} {hour:02d}:00",
                    "map_type": "panel",
                    "map_id": pid,
                    "i_out (A)": i,
                    "v_in (V)": v,
                    "v_out (V)": v,
                    "p (W)": v * i,
                    "energy (Wh)": v * i / 12,
                    "cumulative_energy (Wh)": 0,
                    "die_temp (°C)": 25,
                }
            )
    return rows


def build_fixture(tmp_root: Path) -> tuple[Path, Path]:
    data_root = tmp_root / "data"
    site = "fixture"
    target_current = "root.1.0"
    target_flat = "root.2.0"
    peer_current = "root.1.1"
    peer_flat = "root.2.1"
    shape_rows = [
        {
            "shape_review_row_id": "BR089-DSR-001",
            "shape_review_decision": "defer_durable_shape_hold",
            "reviewed_truth_row_id": "BR084-RTR-001",
            "review_packet_id": "BR082-EPR-001",
            "site": site,
            "panel_id": target_current,
            "episode_anchor_date": "2025-01-01",
            "strict_trigger_date": "2025-01-02",
            "gap_days": 1,
            "window_signal_days": 2,
            "event_A_days": 2,
            "low_mid_days": 2,
            "voltage_low_current_ok_days": 0,
            "current_low_voltage_ok_days": 2,
            "both_low_vi_days": 0,
            "hard_anchor_days": 1,
            "common_cause_days": 0,
            "data_bad_days": 0,
            "median_signal_mid_v_ratio": 1.0,
            "median_signal_mid_i_ratio": 0.5,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        },
        {
            "shape_review_row_id": "BR089-DSR-002",
            "shape_review_decision": "defer_durable_shape_hold",
            "reviewed_truth_row_id": "BR084-RTR-002",
            "review_packet_id": "BR082-EPR-002",
            "site": site,
            "panel_id": target_flat,
            "episode_anchor_date": "2025-01-01",
            "strict_trigger_date": "2025-01-02",
            "gap_days": 1,
            "window_signal_days": 2,
            "event_A_days": 2,
            "low_mid_days": 0,
            "voltage_low_current_ok_days": 0,
            "current_low_voltage_ok_days": 0,
            "both_low_vi_days": 0,
            "hard_anchor_days": 1,
            "common_cause_days": 0,
            "data_bad_days": 0,
            "median_signal_mid_v_ratio": 0.95,
            "median_signal_mid_i_ratio": 0.95,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        },
    ]
    core_rows = []
    for date in ["2025-01-01", "2025-01-02"]:
        for panel, source, mid, mv, mi in [
            (target_current, f"{date}-fixture.csv", 0.5, 1.0, 0.5),
            (target_flat, f"{date}-fixture.csv", 0.9, 0.95, 0.95),
        ]:
            core_rows.append(
                {
                    "date": date,
                    "panel_id": panel,
                    "source_csv": source,
                    "event_A": 1,
                    "is_ae_abn": 1,
                    "is_ae_strong": 1,
                    "re_drop": 0,
                    "fault_like_day": 1 if date == "2025-01-02" else 0,
                    "critical_fault": 0,
                    "final_fault": 0,
                    "degraded_candidate": 1,
                    "data_bad": 0,
                    "mid_ratio": mid,
                    "mid_v_ratio": mv,
                    "mid_i_ratio": mi,
                    "dtw_dist": 10,
                    "co_drop_frac": 0,
                }
            )
    write_csv(tmp_root / "shape.csv", shape_rows, SHAPE_COLUMNS)
    write_csv(data_root / site / "out" / "panel_day_core.csv", core_rows, CORE_COLUMNS)
    for date in ["2025-01-01", "2025-01-02"]:
        rows = []
        rows.extend(raw_rows(date, target_current, peer_current, "current_limited"))
        rows.extend(raw_rows(date, target_flat, peer_flat, "flat"))
        write_csv(data_root / site / "raw" / f"{date}-fixture.csv", rows)
    return tmp_root / "shape.csv", data_root


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_durable_hold_raw_shape_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="br091_raw_hold_smoke_") as tmp:
        tmp_root = Path(tmp)
        shape_path, data_root = build_fixture(tmp_root)
        output_dir = tmp_root / "out"
        result = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--shape-input",
                str(shape_path),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(output_dir),
                "--max-days-per-hold",
                "2",
            ],
            cwd=repo_root,
        )
        assert_true(result.returncode == 0, result.stderr or result.stdout)
        summary = pd.read_csv(output_dir / "panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv", encoding="utf-8-sig")
        days = pd.read_csv(output_dir / "panel_day_engine_durable_hold_raw_shape_review_days_v1.csv", encoding="utf-8-sig")
        payload = json.loads(
            (output_dir / "panel_day_engine_durable_hold_raw_shape_review_v1.json").read_text(encoding="utf-8")
        )
        assert_true(len(summary) == 2, summary.to_string())
        assert_true(len(days) == 4, days.to_string())
        decisions = set(summary["raw_shape_decision"])
        assert_true("stay_hold_current_limited_shape" in decisions, decisions)
        assert_true("stay_hold_no_low_shape_on_selected_raw_days" in decisions, decisions)
        assert_true(int(summary["positive_truth_candidate"].sum()) == 0, summary.to_string())
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        unsafe_shape = tmp_root / "unsafe_shape.csv"
        unsafe_df = pd.read_csv(shape_path, encoding="utf-8-sig")
        unsafe_df.loc[0, "engine_patch_allowed"] = 1
        unsafe_df.to_csv(unsafe_shape, index=False, encoding="utf-8-sig")
        unsafe = run(
            [
                sys.executable,
                str(build_script),
                "--repo-root",
                str(repo_root),
                "--shape-input",
                str(unsafe_shape),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(tmp_root / "unsafe_out"),
            ],
            cwd=repo_root,
        )
        assert_true(unsafe.returncode != 0, "unsafe input should fail")
        assert_true("engine_patch_allowed sum is 1" in (unsafe.stderr + unsafe.stdout), unsafe.stderr + unsafe.stdout)

    print("smoke ok: panel_day_engine_durable_hold_raw_shape_review_v1")


if __name__ == "__main__":
    main()

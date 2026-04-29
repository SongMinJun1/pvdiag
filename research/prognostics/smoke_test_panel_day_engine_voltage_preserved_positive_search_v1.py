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
    "strict_trigger_date",
    "positive_replay_candidate",
    "negative_replay_candidate",
    "operator_facing_change_allowed",
    "engine_patch_allowed",
    "threshold_patch_allowed",
]

HOLD_COLUMNS = [
    "raw_hold_review_id",
    "shape_review_row_id",
    "site",
    "panel_id",
    "strict_trigger_date",
    "raw_shape_decision",
    "positive_truth_candidate",
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
    "confirmed_fault",
    "final_fault",
    "degraded_candidate",
    "data_bad",
    "subgroup_common_cause_candidate",
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


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def daily_rows(
    panel_id: str,
    start: str,
    end: str,
    onset: str | None,
    anchor: str,
    shape: str,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    dates = pd.date_range(start, end, freq="D")
    onset_dt = pd.Timestamp(onset) if onset else None
    anchor_dt = pd.Timestamp(anchor)
    for dt in dates:
        date = dt.strftime("%Y-%m-%d")
        signal = int(onset_dt is not None and onset_dt <= dt <= anchor_dt)
        hard = int(dt == anchor_dt)
        mid_ratio = 0.98
        mid_v_ratio = 0.98
        mid_i_ratio = 0.98
        if signal and dt < anchor_dt and shape == "voltage_preserved":
            mid_ratio = 0.68
            mid_v_ratio = 0.66
            mid_i_ratio = 0.98
        elif signal and dt < anchor_dt and shape == "normal_signal":
            mid_ratio = 0.95
            mid_v_ratio = 0.95
            mid_i_ratio = 0.95
        rows.append(
            {
                "date": date,
                "panel_id": panel_id,
                "source_csv": f"{date}-fixture.csv",
                "event_A": signal,
                "is_ae_abn": signal,
                "is_ae_strong": signal,
                "re_drop": signal,
                "fault_like_day": hard,
                "critical_fault": 0,
                "confirmed_fault": 0,
                "final_fault": 0,
                "degraded_candidate": signal,
                "data_bad": 0,
                "subgroup_common_cause_candidate": 0,
                "mid_ratio": mid_ratio,
                "mid_v_ratio": mid_v_ratio,
                "mid_i_ratio": mid_i_ratio,
                "dtw_dist": 1.0 + signal,
                "co_drop_frac": 0.0,
            }
        )
    return rows


def build_fixture(tmp_root: Path) -> tuple[Path, Path, Path]:
    site = "fixture"
    data_root = tmp_root / "data"
    shape_input = tmp_root / "shape.csv"
    hold_input = tmp_root / "hold.csv"

    pos_panel = "pos.1.0"
    neg_panel = "neg.1.0"
    hold_panel = "hold.1.0"
    new_panel = "new.1.0"
    shape_rows = [
        {
            "shape_review_row_id": "BR089-DSR-POS",
            "shape_review_decision": "fill_positive_durable_voltage_preserved_shape",
            "reviewed_truth_row_id": "BR084-RTR-POS",
            "review_packet_id": "BR082-EPR-POS",
            "site": site,
            "panel_id": pos_panel,
            "strict_trigger_date": "2025-02-01",
            "positive_replay_candidate": 1,
            "negative_replay_candidate": 0,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        },
        {
            "shape_review_row_id": "BR089-DSR-NEG",
            "shape_review_decision": "carry_forward_negative_counterexample",
            "reviewed_truth_row_id": "BR084-RTR-NEG",
            "review_packet_id": "BR082-EPR-NEG",
            "site": site,
            "panel_id": neg_panel,
            "strict_trigger_date": "2025-04-01",
            "positive_replay_candidate": 0,
            "negative_replay_candidate": 1,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        },
        {
            "shape_review_row_id": "BR089-DSR-HOLD",
            "shape_review_decision": "defer_durable_shape_hold",
            "reviewed_truth_row_id": "BR084-RTR-HOLD",
            "review_packet_id": "BR082-EPR-HOLD",
            "site": site,
            "panel_id": hold_panel,
            "strict_trigger_date": "2025-05-01",
            "positive_replay_candidate": 0,
            "negative_replay_candidate": 0,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        },
    ]
    hold_rows = [
        {
            "raw_hold_review_id": "BR091-DHR-HOLD",
            "shape_review_row_id": "BR089-DSR-HOLD",
            "site": site,
            "panel_id": hold_panel,
            "strict_trigger_date": "2025-05-01",
            "raw_shape_decision": "stay_hold_no_low_shape_on_selected_raw_days",
            "positive_truth_candidate": 0,
            "operator_facing_change_allowed": 0,
            "engine_patch_allowed": 0,
            "threshold_patch_allowed": 0,
        }
    ]
    core_rows = []
    core_rows.extend(daily_rows(pos_panel, "2025-01-01", "2025-02-01", "2025-01-10", "2025-02-01", "voltage_preserved"))
    core_rows.extend(daily_rows(neg_panel, "2025-03-10", "2025-04-01", "2025-03-20", "2025-04-01", "voltage_preserved"))
    core_rows.extend(daily_rows(hold_panel, "2025-04-01", "2025-05-01", "2025-04-10", "2025-05-01", "normal_signal"))
    core_rows.extend(daily_rows(new_panel, "2025-05-01", "2025-06-01", "2025-05-10", "2025-06-01", "voltage_preserved"))

    write_csv(shape_input, shape_rows, SHAPE_COLUMNS)
    write_csv(hold_input, hold_rows, HOLD_COLUMNS)
    write_csv(data_root / site / "out" / "panel_day_core.csv", core_rows, CORE_COLUMNS)
    return data_root, shape_input, hold_input


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        data_root, shape_input, hold_input = build_fixture(tmp_root)
        out_dir = tmp_root / "out"
        cmd = [
            sys.executable,
            "research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py",
            "--repo-root",
            str(repo_root),
            "--shape-input",
            str(shape_input),
            "--hold-input",
            str(hold_input),
            "--data-root",
            str(data_root),
            "--sites",
            "fixture",
            "--output-dir",
            str(out_dir),
        ]
        proc = run(cmd, repo_root)
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["candidate_rows"] == 3, payload)
        assert_true(payload["new_search_candidate_rows"] == 1, payload)
        assert_true(payload["known_positive_seed_rows"] == 1, payload)
        assert_true(payload["known_negative_overlap_rows"] == 1, payload)
        assert_true(payload["known_hold_overlap_rows"] == 0, payload)
        assert_true(payload["positive_truth_candidate_approved_sum"] == 0, payload)
        assert_true(payload["threshold_tuning_approved_sum"] == 0, payload)

        artifact_payload = json.loads(
            (out_dir / "panel_day_engine_voltage_preserved_positive_search_v1.json").read_text(encoding="utf-8")
        )
        note = (out_dir / "panel_day_engine_voltage_preserved_positive_search_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(artifact_payload["input_resolution_sources"]["shape_input"] == "explicit_cli", artifact_payload)
        assert_true(artifact_payload["input_resolution_sources"]["hold_input"] == "explicit_cli", artifact_payload)
        assert_true("evidence input manifest: `not provided`" in note, note)
        assert_true("`shape_input`: `explicit_cli`" in note, note)
        assert_true("`hold_input`: `explicit_cli`" in note, note)

        candidates = pd.read_csv(out_dir / "panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv")
        summary = pd.read_csv(out_dir / "panel_day_engine_voltage_preserved_positive_search_summary_v1.csv")
        assert_true(set(candidates["known_review_role"]) == {
            "known_positive_seed",
            "known_negative_counterexample",
            "new_search_candidate",
        }, candidates)
        assert_true(int(candidates["engine_patch_allowed"].sum()) == 0, candidates)
        assert_true(int(candidates["manual_review_ready"].sum()) == 1, candidates)
        assert_true("block_known_negative_counterexample_overlap" in set(candidates["truth_search_action"]), candidates)
        assert_true(len(summary) == 3, summary)

        manifest_path = tmp_root / "voltage_preserved_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"shape_input": str(shape_input), "hold_input": str(hold_input)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = tmp_root / "manifest_out"
        manifest = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(manifest_path),
                "--data-root",
                str(data_root),
                "--sites",
                "fixture",
                "--output-dir",
                str(manifest_out),
            ],
            repo_root,
        )
        assert_true(manifest.returncode == 0, manifest.stderr or manifest.stdout)
        manifest_candidates = pd.read_csv(
            manifest_out / "panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv",
            encoding="utf-8-sig",
        )
        manifest_payload = json.loads(
            (manifest_out / "panel_day_engine_voltage_preserved_positive_search_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (
            manifest_out / "panel_day_engine_voltage_preserved_positive_search_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(manifest_payload["candidate_rows"] == payload["candidate_rows"], manifest_payload)
        assert_true(
            manifest_candidates["known_review_role"].tolist() == candidates["known_review_role"].tolist(),
            manifest_candidates.to_string(),
        )
        assert_true(
            manifest_candidates["truth_search_action"].tolist() == candidates["truth_search_action"].tolist(),
            manifest_candidates.to_string(),
        )
        assert_true(manifest_payload["input_resolution_sources"]["shape_input"] == "input_manifest", manifest_payload)
        assert_true(manifest_payload["input_resolution_sources"]["hold_input"] == "input_manifest", manifest_payload)
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`shape_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`hold_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp_root / "bad_voltage_preserved_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {
                    "inputs": {
                        "shape_input": str(tmp_root / "missing_shape.csv"),
                        "hold_input": str(tmp_root / "missing_hold.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = tmp_root / "override_out"
        override = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py",
                "--repo-root",
                str(repo_root),
                "--shape-input",
                str(shape_input),
                "--hold-input",
                str(hold_input),
                "--input-manifest",
                str(bad_manifest_path),
                "--data-root",
                str(data_root),
                "--sites",
                "fixture",
                "--output-dir",
                str(override_out),
            ],
            repo_root,
        )
        assert_true(override.returncode == 0, override.stderr or override.stdout)
        override_payload = json.loads(
            (override_out / "panel_day_engine_voltage_preserved_positive_search_v1.json").read_text(
                encoding="utf-8"
            )
        )
        assert_true(override_payload["input_resolution_sources"]["shape_input"] == "explicit_cli", override_payload)
        assert_true(override_payload["input_resolution_sources"]["hold_input"] == "explicit_cli", override_payload)

        missing_key_manifest_path = tmp_root / "missing_key_voltage_preserved_inputs.json"
        missing_key_manifest_path.write_text(
            json.dumps({"inputs": {"shape_input": str(shape_input)}}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        missing_key = run(
            [
                sys.executable,
                "research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py",
                "--repo-root",
                str(repo_root),
                "--input-manifest",
                str(missing_key_manifest_path),
                "--data-root",
                str(data_root),
                "--sites",
                "fixture",
                "--output-dir",
                str(tmp_root / "missing_key_out"),
            ],
            repo_root,
        )
        assert_true(missing_key.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true("missing `hold_input`" in (missing_key.stderr + missing_key.stdout), missing_key.stderr)
        print(json.dumps({"smoke": "ok", "candidate_rows": int(len(candidates))}, ensure_ascii=False))


if __name__ == "__main__":
    main()

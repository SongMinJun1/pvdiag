#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_common_cause_exact_seed_search_v1.csv"
SUMMARY_NAME = "panel_day_engine_common_cause_exact_seed_search_summary_v1.csv"
SITE_STATUS_NAME = "panel_day_engine_common_cause_exact_seed_site_status_summary_v1.csv"
NOTE_NAME = "panel_day_engine_common_cause_exact_seed_search_note_v1.md"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def judgment_row(case_id: str, panel_id: str, focus: str, blocker: str = "") -> str:
    values = [
        case_id,
        "site_a",
        panel_id,
        "block_individual_precursor_common_cause" if focus == "strong_common_cause_hold_review" else "hold_subgroup_or_breadth_context",
        "외부계통·공통원인 계열",
        "external_common_cause",
        focus,
        blocker,
        1 if blocker else 0,
        1 if "group" in blocker else 0,
        1 if "site" in blocker else 0,
        "site_event_synchrony" if focus == "strong_common_cause_hold_review" else "subgroup_synchrony_candidate",
        1,
        1 if focus == "strong_common_cause_hold_review" else 0,
        0,
        1 if focus != "strong_common_cause_hold_review" else 0,
        0.25,
        0,
        0,
        "spatiality_blocks_panel_local_promotion",
    ]
    return ",".join(str(value) for value in values)


def raw_row(date: str, panel_id: str, group_off: str, site_soft: int, site_hard: int, final_fault: str = "False") -> str:
    values = [
        date,
        panel_id,
        group_off,
        site_soft,
        site_hard,
        "True",
        "False",
        "False",
        final_fault,
        "False",
    ]
    return ",".join(str(value) for value in values)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = (
        repo_root
        / "research"
        / "prognostics"
        / "build_panel_day_engine_common_cause_exact_seed_search_v1.py"
    )
    with tempfile.TemporaryDirectory(prefix="common_cause_exact_seed_") as tmp_dir:
        root = Path(tmp_dir)
        data_root = root / "data"
        input_dir = root / "input"
        out_dir = root / "out"
        judgment_csv = input_dir / "judgment.csv"
        synchrony_csv = input_dir / "synchrony.csv"
        current_csv = input_dir / "current.csv"
        precursor_csv = input_dir / "precursor.csv"
        rawonly_csv = input_dir / "rawonly.csv"
        raw_csv = data_root / "site_a" / "out" / "ae_simple_fault_candidates.csv"
        judgment_header = [
            "candidate_case_id",
            "site",
            "panel_id",
            "judgment_bucket",
            "candidate_family_label_ko",
            "candidate_family_track",
            "review_focus_bucket",
            "friction_blocker_types",
            "friction_direct_row_count",
            "friction_group_off_row_count",
            "friction_site_event_row_count",
            "synchrony_bucket",
            "common_cause_row_count",
            "site_event_row_count",
            "group_off_row_count",
            "subgroup_common_cause_row_count",
            "max_co_drop_frac",
            "operator_promotion_allowed_flag",
            "engine_patch_candidate_flag",
            "threshold_candidate_role",
        ]
        write_text(
            judgment_csv,
            "\n".join(
                [
                    ",".join(judgment_header),
                    judgment_row("BR064-001", "root.0.1", "strong_common_cause_hold_review", "current_date_displaced"),
                    judgment_row("BR064-002", "root.0.2", "strong_common_cause_hold_review"),
                    judgment_row("BR064-003", "root.0.3", "strong_common_cause_hold_review", "rawonly_date_displaced"),
                    judgment_row("BR064-004", "root.0.4", "subgroup_or_breadth_context_review"),
                ]
            )
            + "\n",
        )
        write_text(
            synchrony_csv,
            "\n".join(
                [
                    ",".join(
                        [
                            "site",
                            "panel_id",
                            "best_report_lane",
                            "synchrony_lane_bucket",
                            "first_common_cause_date",
                            "last_common_cause_date",
                            "any_pre_ews",
                            "any_prefault_B",
                            "any_fault_like_day",
                            "any_final_fault",
                            "any_critical_fault",
                        ]
                    ),
                    "site_a,root.0.1,official_current,site_event_synchrony__official_current,2026-01-10,2026-01-10,1,0,1,1,0",
                    "site_a,root.0.2,official_current,site_event_synchrony__official_current,2026-01-10,2026-01-10,1,0,1,1,0",
                    "site_a,root.0.3,rawonly_current,site_event_synchrony__rawonly_current,2026-01-10,2026-01-10,1,0,1,1,0",
                    "site_a,root.0.4,rawonly_current,subgroup_synchrony_candidate__rawonly_current,2026-01-11,2026-01-11,1,0,1,1,0",
                ]
            )
            + "\n",
        )
        write_text(
            current_csv,
            "\n".join(
                [
                    "site,panel_id,고장날짜,전조날짜",
                    "site_a,root.0.1,2026-01-10,2026-01-01",
                    "site_a,root.0.2,2026-02-01,2026-01-01",
                ]
            )
            + "\n",
        )
        write_text(precursor_csv, "site,panel_id,전조날짜\nsite_a,root.0.3,2026-01-11\n")
        write_text(rawonly_csv, "site,panel_id,신호 기준일,전조 시작일\nsite_a,root.0.3,2026-01-12,2026-01-01\n")
        write_text(
            raw_csv,
            "\n".join(
                [
                    ",".join(
                        [
                            "date",
                            "panel_id",
                            "group_off_date",
                            "site_event_soft",
                            "site_event_hard",
                            "pre_ews",
                            "prefault_B",
                            "fault_like_day",
                            "final_fault",
                            "critical_fault",
                        ]
                    ),
                    raw_row("2026-01-10", "root.0.1", "False", 1, 0, "True"),
                    raw_row("2026-01-10", "root.0.2", "False", 1, 0, "True"),
                    raw_row("2026-01-10", "root.0.3", "False", 1, 0, "True"),
                ]
            )
            + "\n",
        )
        result = subprocess.run(
            [
                "python3",
                str(script),
                "--judgment-input",
                str(judgment_csv),
                "--synchrony-input",
                str(synchrony_csv),
                "--current-input",
                str(current_csv),
                "--precursor-input",
                str(precursor_csv),
                "--rawonly-signal-input",
                str(rawonly_csv),
                "--data-root",
                str(data_root),
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
        site_status = pd.read_csv(out_dir / SITE_STATUS_NAME, low_memory=False)
        note = (out_dir / NOTE_NAME).read_text(encoding="utf-8")
        by_panel = detail.set_index("panel_id")
        assert_true(by_panel.loc["root.0.1", "primary_judgment_role"] == "exact_family_closure", detail.to_string())
        assert_true(by_panel.loc["root.0.1", "exact_family_closure_flag"] == 1, detail.to_string())
        assert_true(by_panel.loc["root.0.2", "primary_judgment_role"] == "structural_blocker", detail.to_string())
        assert_true(by_panel.loc["root.0.2", "nearest_official_current_gap_days"] == 22, detail.to_string())
        assert_true(by_panel.loc["root.0.3", "primary_judgment_role"] == "structural_blocker", detail.to_string())
        assert_true(by_panel.loc["root.0.4", "primary_judgment_role"] == "supportive_hint", detail.to_string())
        assert_true(int(detail["operator_promotion_allowed_flag"].sum()) == 0, "promotion must stay zero")
        assert_true(int(detail["engine_patch_candidate_flag"].sum()) == 0, "engine patch must stay zero")
        assert_true(int(detail["threshold_patch_allowed_flag"].sum()) == 0, "threshold patch must stay zero")
        assert_true(int(summary["exact_family_closure_sum"].sum()) == 1, summary.to_string())
        assert_true(int(site_status["raw_direct_common_cause_rows"].sum()) == 3, site_status.to_string())
        assert_true("exact family closure candidates: `1`" in note, "note missing closure count")
        assert_true("evidence input manifest: `not provided`" in note, note)
        assert_true("`judgment_input`: `explicit_cli`" in note, note)
        assert_true("`synchrony_input`: `explicit_cli`" in note, note)
        assert_true("`current_input`: `explicit_cli`" in note, note)
        assert_true("`precursor_input`: `explicit_cli`" in note, note)
        assert_true("`rawonly_signal_input`: `explicit_cli`" in note, note)

        manifest = root / "common_cause_exact_seed_inputs.json"
        manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "judgment_input": str(judgment_csv),
                        "synchrony_input": str(synchrony_csv),
                        "current_input": str(current_csv),
                        "precursor_input": str(precursor_csv),
                        "rawonly_signal_input": str(rawonly_csv),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_out = root / "manifest_out"
        manifest_result = subprocess.run(
            [
                "python3",
                str(script),
                "--input-manifest",
                str(manifest),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(manifest_out),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(
            manifest_result.returncode == 0,
            f"manifest builder failed:\nSTDOUT={manifest_result.stdout}\nSTDERR={manifest_result.stderr}",
        )
        manifest_detail = pd.read_csv(manifest_out / DETAIL_NAME, low_memory=False)
        manifest_summary = pd.read_csv(manifest_out / SUMMARY_NAME, low_memory=False)
        manifest_note = (manifest_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true(
            manifest_detail["primary_judgment_role"].tolist() == detail["primary_judgment_role"].tolist(),
            manifest_detail.to_string(),
        )
        assert_true(int(manifest_summary["exact_family_closure_sum"].sum()) == 1, manifest_summary.to_string())
        assert_true(f"evidence input manifest: `{manifest}`" in manifest_note, manifest_note)
        assert_true("`judgment_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`synchrony_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`current_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`precursor_input`: `input_manifest`" in manifest_note, manifest_note)
        assert_true("`rawonly_signal_input`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest = root / "bad_common_cause_exact_seed_inputs.json"
        bad_manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "judgment_input": str(root / "missing_judgment.csv"),
                        "synchrony_input": str(root / "missing_synchrony.csv"),
                        "current_input": str(root / "missing_current.csv"),
                        "precursor_input": str(root / "missing_precursor.csv"),
                        "rawonly_signal_input": str(root / "missing_rawonly.csv"),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_out = root / "override_out"
        override_result = subprocess.run(
            [
                "python3",
                str(script),
                "--input-manifest",
                str(bad_manifest),
                "--judgment-input",
                str(judgment_csv),
                "--synchrony-input",
                str(synchrony_csv),
                "--current-input",
                str(current_csv),
                "--precursor-input",
                str(precursor_csv),
                "--rawonly-signal-input",
                str(rawonly_csv),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(override_out),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(
            override_result.returncode == 0,
            f"override builder failed:\nSTDOUT={override_result.stdout}\nSTDERR={override_result.stderr}",
        )
        override_note = (override_out / NOTE_NAME).read_text(encoding="utf-8")
        assert_true("`judgment_input`: `explicit_cli`" in override_note, override_note)
        assert_true("`rawonly_signal_input`: `explicit_cli`" in override_note, override_note)

        missing_key_manifest = root / "missing_key_common_cause_exact_seed_inputs.json"
        missing_key_manifest.write_text(
            json.dumps(
                {
                    "inputs": {
                        "judgment_input": str(judgment_csv),
                        "synchrony_input": str(synchrony_csv),
                        "current_input": str(current_csv),
                        "precursor_input": str(precursor_csv),
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        missing_key_result = subprocess.run(
            [
                "python3",
                str(script),
                "--input-manifest",
                str(missing_key_manifest),
                "--data-root",
                str(data_root),
                "--output-dir",
                str(root / "missing_key_out"),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
        )
        assert_true(missing_key_result.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `rawonly_signal_input`" in (missing_key_result.stderr + missing_key_result.stdout),
            missing_key_result.stderr,
        )
    print("smoke ok: panel_day_engine_common_cause_exact_seed_search_v1")


if __name__ == "__main__":
    main()

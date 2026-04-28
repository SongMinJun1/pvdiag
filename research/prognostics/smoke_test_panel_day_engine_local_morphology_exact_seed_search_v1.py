#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_local_morphology_exact_seed_search_v1.csv"
SUMMARY_NAME = "panel_day_engine_local_morphology_exact_seed_search_summary_v1.csv"


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    cross_root = root / "cross"
    data_root = root / "data" / "conalog" / "out"
    result_root = root / "result"
    raw_share = root / "raw_share"
    live_share = root / "live_share"

    cross_rows = [
        {
            "site": "conalog",
            "panel_id": "panel.exact",
            "review_focus_bucket": "local_signal_morphology_review",
            "recovery_bucket": "re_drop_cycle",
            "recovery_best_report_lane": "rawonly_current",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "synchrony_best_report_lane": "rawonly_current",
        },
        {
            "site": "conalog",
            "panel_id": "panel.supportive",
            "review_focus_bucket": "local_signal_morphology_review",
            "recovery_bucket": "re_drop_cycle",
            "recovery_best_report_lane": "official_current",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "synchrony_best_report_lane": "official_current",
        },
        {
            "site": "conalog",
            "panel_id": "panel.sensor",
            "review_focus_bucket": "local_signal_morphology_review",
            "recovery_bucket": "persistent_non_recovery",
            "recovery_best_report_lane": "rawonly_current",
            "synchrony_bucket": "panel_local_or_weak_synchrony",
            "synchrony_best_report_lane": "rawonly_current",
        },
        {
            "site": "conalog",
            "panel_id": "panel.ignore",
            "review_focus_bucket": "strong_common_cause_hold_review",
            "recovery_bucket": "re_drop_cycle",
            "recovery_best_report_lane": "rawonly_current",
            "synchrony_bucket": "group_off_synchrony",
            "synchrony_best_report_lane": "rawonly_current",
        },
    ]
    write_csv(
        cross_root / "panel_day_engine_cross_axis_manifest_sync_review_v1.csv",
        cross_rows,
        columns=list(cross_rows[0].keys()),
    )

    raw_rows = [
        {
            "date": "2025-01-10",
            "panel_id": "panel.exact",
            "pre_ews": 1,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 1,
            "critical_fault": 0,
            "recovered_any": 1,
            "recovered_sustained": 1,
            "re_drop": 1,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "group_off_date": 0,
            "group_off_like": 0,
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
        },
        {
            "date": "2025-01-11",
            "panel_id": "panel.supportive",
            "pre_ews": 1,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 0,
            "critical_fault": 0,
            "recovered_any": 1,
            "recovered_sustained": 1,
            "re_drop": 1,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "group_off_date": 0,
            "group_off_like": 0,
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
        },
        {
            "date": "2025-01-12",
            "panel_id": "panel.sensor",
            "pre_ews": 1,
            "prefault_B": 0,
            "prefault_B_effective": 0,
            "fault_like_day": 1,
            "final_fault": 0,
            "critical_fault": 0,
            "recovered_any": 0,
            "recovered_sustained": 0,
            "re_drop": 0,
            "site_event_soft": 0,
            "site_event_hard": 0,
            "group_off_date": 0,
            "group_off_like": 0,
            "subgroup_common_cause_candidate": 0,
            "prefault_B_common_cause_overlap": 0,
        },
    ]
    write_csv(data_root / "ae_simple_fault_candidates.csv", raw_rows, columns=list(raw_rows[0].keys()))

    write_csv(
        result_root / "fault_panel_result_raw_only_current_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.exact", "고장 기준일": "2025-01-10"},
            {"site": "conalog", "panel_id": "panel.supportive", "고장 기준일": "2025-01-11"},
            {"site": "conalog", "panel_id": "panel.sensor", "고장 기준일": "2025-01-12"},
        ],
        columns=["site", "panel_id", "고장 기준일"],
    )

    write_csv(
        raw_share / "panel_day_engine_runtime_fault_event_audit_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.exact", "strict_trigger_date": "2025-01-10", "first_final_fault_date": "2025-01-10"},
            {"site": "conalog", "panel_id": "panel.supportive", "strict_trigger_date": "2025-01-11", "first_final_fault_date": "2025-01-11"},
            {"site": "conalog", "panel_id": "panel.sensor", "strict_trigger_date": "2025-01-12", "first_final_fault_date": "2025-01-12"},
        ],
        columns=["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
    )
    write_csv(
        raw_share / "panel_day_engine_runtime_cause_candidate_heuristics_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.exact", "원인후보_top1_ko": "제어응답형", "원인후보_top1_score": 8, "원인후보_top2_ko": "센서·피드백형", "원인후보_top3_ko": "접속·부분개방형"},
            {"site": "conalog", "panel_id": "panel.supportive", "원인후보_top1_ko": "다이오드·서브스트링형", "원인후보_top1_score": 5, "원인후보_top2_ko": "센서·피드백형", "원인후보_top3_ko": "접속·부분개방형"},
            {"site": "conalog", "panel_id": "panel.sensor", "원인후보_top1_ko": "센서·피드백형", "원인후보_top1_score": 6, "원인후보_top2_ko": "접속·부분개방형", "원인후보_top3_ko": "다이오드·서브스트링형"},
        ],
        columns=["site", "panel_id", "원인후보_top1_ko", "원인후보_top1_score", "원인후보_top2_ko", "원인후보_top3_ko"],
    )
    write_csv(
        raw_share / "panel_day_engine_runtime_final_verdict_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.exact", "세부fault_기준일": "2025-01-10", "GPVS_외부참조패턴_ko": ""},
            {"site": "conalog", "panel_id": "panel.supportive", "세부fault_기준일": "2025-01-11", "GPVS_외부참조패턴_ko": ""},
            {"site": "conalog", "panel_id": "panel.sensor", "세부fault_기준일": "2025-01-12", "GPVS_외부참조패턴_ko": ""},
        ],
        columns=["site", "panel_id", "세부fault_기준일", "GPVS_외부참조패턴_ko"],
    )
    write_csv(
        live_share / "panel_day_engine_cause_candidate_heuristics_v1.csv",
        [
            {"site": "conalog", "panel_id": "panel.supportive", "원인후보_top1_ko": "다이오드·서브스트링형", "원인후보_top1_score": 4, "원인후보_top2_ko": "센서·피드백형", "원인후보_top3_ko": "접속·부분개방형", "GPVS_외부참조패턴_ko": "장치 응답 이상형"},
        ],
        columns=["site", "panel_id", "원인후보_top1_ko", "원인후보_top1_score", "원인후보_top2_ko", "원인후보_top3_ko", "GPVS_외부참조패턴_ko"],
    )
    write_csv(
        live_share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [{"site": "conalog", "panel_id": "panel.supportive", "GPVS_외부참조패턴_ko": "장치 응답 이상형"}],
        columns=["site", "panel_id", "GPVS_외부참조패턴_ko"],
    )
    write_csv(
        live_share / "panel_day_engine_gpvs_evidence_pack_v1.csv",
        [{"site": "conalog", "panel_id": "panel.supportive", "GPVS_외부참조패턴_ko": "장치 응답 이상형"}],
        columns=["site", "panel_id", "GPVS_외부참조패턴_ko"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_panel_day_engine_local_morphology_exact_seed_search_v1.py"
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture(tmp_root)
        out_dir = tmp_root / "out"
        cmd = [
            sys.executable,
            str(script),
            "--cross-axis-root",
            str(tmp_root / "cross"),
            "--data-root",
            str(tmp_root / "data"),
            "--result-root",
            str(tmp_root / "result"),
            "--raw-only-share-root",
            str(tmp_root / "raw_share"),
            "--live-share-root",
            str(tmp_root / "live_share"),
            "--output-dir",
            str(out_dir),
            "--sites",
            "conalog",
        ]
        completed = run(cmd, repo_root)
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail_df = pd.read_csv(out_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary_df = pd.read_csv(out_dir / SUMMARY_NAME, encoding="utf-8-sig")
        assert_true(len(detail_df) == 3, detail_df.to_string())
        status_map = {row["panel_id"]: row["search_status"] for row in detail_df.to_dict(orient="records")}
        assert_true(status_map["panel.exact"] == "exact_family_candidate", str(status_map))
        assert_true(
            status_map["panel.supportive"] == "supportive_device_response_recovery_seed",
            str(status_map),
        )
        assert_true(
            status_map["panel.sensor"] == "sensor_feedback_local_morphology_candidate",
            str(status_map),
        )
        assert_true(int(summary_df["exact_family_candidates"].sum()) == 1, summary_df.to_string())
        assert_true(int(summary_df["supportive_seed_candidates"].sum()) == 1, summary_df.to_string())


if __name__ == "__main__":
    main()

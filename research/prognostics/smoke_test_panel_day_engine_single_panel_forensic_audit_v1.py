from __future__ import annotations

import importlib.util
import py_compile
import sys
import tempfile
from pathlib import Path

import pandas as pd


TARGET_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"


def load_builder_module():
    builder_path = Path(__file__).with_name("build_panel_day_engine_single_panel_forensic_audit_v1.py")
    spec = importlib.util.spec_from_file_location("single_panel_forensic_builder", builder_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def write_empty_csv(path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture(root: Path) -> None:
    write_csv(
        root / "_share/panel_date_reaudit_working.csv",
        [
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "strict_trigger_date": "2025-03-21",
                "first_warning_date": "2025-01-20",
                "retrospective_onset_date": "2025-01-20",
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "open_or_device_issue_like",
                "vendor_note": "전압 0, 패널이나 장비 문제로 볼 수 있는 상태, 현장확인 안됨",
                "reason_summary": "fixture",
            }
        ],
    )
    write_csv(
        root / "_share/panel_day_engine_non_precursor_performance_cases_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "anchor_date": "2025-03-21",
                "candidate_validity": "needs_more_info",
                "vendor_reply_class": "vendor_likely_positive",
                "vendor_fault_family": "open_or_device_issue_like",
                "final_fault_hit_by_anchor_flag": 1,
                "critical_fault_hit_by_anchor_flag": 0,
            }
        ],
    )
    write_empty_csv(
        root / "_share/panel_day_engine_precursor_onset_truth_v1.csv",
        ["site", "panel_id", "preferred_precursor_onset_date"],
    )
    write_csv(
        root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "사건유형_ko": "전조형 고장",
                "최종고장양상_ko": "급격 종료",
                "커널로그_증상명_ko": "전압 변화형",
                "커널로그_원인군_ko": "개방/장치이상형",
                "GPVS_참고유형_ko": "개방/장치이상 계열",
            }
        ],
    )
    write_csv(
        root / "_share/panel_day_engine_fault_panel_event_audit_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "사건유형_재판정_ko": "전조형 고장",
                "최종고장양상_재판정_ko": "급격 종료",
            }
        ],
    )
    write_csv(
        root / "data/conalog/out/panel_day_core.csv",
        [
            {
                "date": current.strftime("%Y-%m-%d"),
                "panel_id": TARGET_PANEL_ID,
                "mid_ratio": 0.91 if current < pd.Timestamp("2025-03-21") else 0.0,
                "mid_v_ratio": 0.84 if current < pd.Timestamp("2025-03-21") else 0.0,
                "v_drop": 0.17 if current < pd.Timestamp("2025-03-21") else 1.0,
                "recon_error": 0.03 if current < pd.Timestamp("2025-03-21") else 0.08,
                "confirmed_fault": bool(current >= pd.Timestamp("2025-03-21")),
                "critical_fault": False,
                "final_fault": bool(current == pd.Timestamp("2025-03-21")),
                "fault_like_day": bool(current >= pd.Timestamp("2025-03-21")),
                "degraded_candidate": bool(current >= pd.Timestamp("2025-03-21")),
                "dead_diag_date": "2025-03-22",
                "diagnosis_date_online": "2025-03-22",
            }
            for current in pd.date_range("2025-01-20", "2025-03-21", freq="D")
        ],
    )
    gate_rows: list[dict[str, object]] = []
    for current in pd.date_range("2025-01-16", "2025-03-21", freq="D"):
        current_ts = pd.Timestamp(current)
        gate_rows.append(
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "date": current_ts.strftime("%Y-%m-%d"),
                "cond_evt": bool(pd.Timestamp("2025-02-01") <= current_ts <= pd.Timestamp("2025-02-27") or current_ts == pd.Timestamp("2025-03-20")),
                "cond_hs": bool(pd.Timestamp("2025-02-01") <= current_ts <= pd.Timestamp("2025-02-09")),
                "signal_count": 2 if current_ts >= pd.Timestamp("2025-02-01") else 1,
                "ews_warning": bool(current_ts == pd.Timestamp("2025-01-16")),
                "site_event_soft": False,
                "site_event_hard": False,
                "prefault_B": bool(current_ts >= pd.Timestamp("2025-02-01")),
                "pre_alarm": bool(current_ts in {pd.Timestamp("2025-02-01"), pd.Timestamp("2025-03-20")}),
                "prefault_cond_mid": bool(current_ts >= pd.Timestamp("2025-02-01")),
                "prefault_cond_ae": bool(current_ts <= pd.Timestamp("2025-03-20")),
                "prefault_cond_dtw": bool(current_ts >= pd.Timestamp("2025-01-27")),
            }
        )
    write_csv(
        root / "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
        gate_rows,
    )


def main() -> None:
    builder_module = load_builder_module()
    py_compile.compile(str(Path(__file__).with_name("build_panel_day_engine_single_panel_forensic_audit_v1.py")), doraise=True)
    py_compile.compile(str(Path(__file__)), doraise=True)

    precursor_decision = builder_module.determine_rule_based_event_decision(
        pd.Series(
            {
                "retrospective_onset_date": "2025-01-20",
                "strict_trigger_date": "2025-03-21",
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
            }
        ),
        pd.Series({"anchor_date": "2025-03-21"}),
        pd.DataFrame(
            [
                {"date": "2025-03-21", "final_fault": True, "critical_fault": False, "dead_diag_date": "2025-03-22"},
            ]
        ),
    )
    assert precursor_decision.event_type_ko == "전조형 고장"
    assert precursor_decision.terminal_pattern_ko == "급격 종료"

    abrupt_decision = builder_module.determine_rule_based_event_decision(
        pd.Series(
            {
                "retrospective_onset_date": "",
                "strict_trigger_date": "2025-03-21",
                "onset_confidence": "",
                "onset_method": "",
            }
        ),
        pd.Series({"anchor_date": "2025-03-21"}),
        pd.DataFrame([{"date": "2025-03-21", "final_fault": False, "critical_fault": False, "dead_diag_date": ""}]),
    )
    assert abrupt_decision.event_type_ko == "급작 고장"

    holdout_decision = builder_module.determine_rule_based_event_decision(
        pd.Series(
            {
                "retrospective_onset_date": "2025-03-21",
                "strict_trigger_date": "2025-03-21",
                "onset_confidence": "medium",
                "onset_method": "strict_trigger_fallback",
            }
        ),
        pd.Series({"anchor_date": "2025-03-21"}),
        pd.DataFrame([{"date": "2025-03-21", "final_fault": False, "critical_fault": False, "dead_diag_date": ""}]),
    )
    assert holdout_decision.event_type_ko == "고장유형 보류"

    assert builder_module.continuity_recommendation_for("동일사건_연속가능성_높음") == "전조형고장으로상향"
    assert builder_module.continuity_recommendation_for("전조흔적은있지만_연속성불충분") == "고장유형보류유지"
    assert builder_module.continuity_recommendation_for("초기경고와_후기트리거_별개가능성") == "순수급작으로복귀"
    assert builder_module.continuity_recommendation_for("불충분") == "추가수동검토필요"
    assert builder_module.judge_continuity(
        explicit_precursor_eval_flag=False,
        effective_lead_days=30,
        ae_active_days_pretrigger=25,
        dtw_active_days_pretrigger=20,
        hs_active_days_pretrigger=5,
        cond_evt_days_pretrigger=10,
        pre_alarm_days_pretrigger=2,
        longest_consecutive_active_run_days=20,
        longest_consecutive_cond_evt_run_days=7,
        last_gap_before_trigger_days=1,
    ) == "동일사건_연속가능성_높음"
    assert builder_module.judge_continuity(
        explicit_precursor_eval_flag=False,
        effective_lead_days=20,
        ae_active_days_pretrigger=4,
        dtw_active_days_pretrigger=1,
        hs_active_days_pretrigger=0,
        cond_evt_days_pretrigger=2,
        pre_alarm_days_pretrigger=0,
        longest_consecutive_active_run_days=4,
        longest_consecutive_cond_evt_run_days=1,
        last_gap_before_trigger_days=5,
    ) == "전조흔적은있지만_연속성불충분"
    assert builder_module.judge_continuity(
        explicit_precursor_eval_flag=False,
        effective_lead_days=18,
        ae_active_days_pretrigger=1,
        dtw_active_days_pretrigger=0,
        hs_active_days_pretrigger=0,
        cond_evt_days_pretrigger=0,
        pre_alarm_days_pretrigger=0,
        longest_consecutive_active_run_days=1,
        longest_consecutive_cond_evt_run_days=0,
        last_gap_before_trigger_days=16,
    ) == "초기경고와_후기트리거_별개가능성"
    assert builder_module.judge_continuity(
        explicit_precursor_eval_flag=False,
        effective_lead_days=None,
        ae_active_days_pretrigger=0,
        dtw_active_days_pretrigger=0,
        hs_active_days_pretrigger=0,
        cond_evt_days_pretrigger=0,
        pre_alarm_days_pretrigger=0,
        longest_consecutive_active_run_days=0,
        longest_consecutive_cond_evt_run_days=0,
        last_gap_before_trigger_days=None,
    ) == "불충분"

    with tempfile.TemporaryDirectory(prefix="single_panel_forensic_") as tmpdir:
        root = Path(tmpdir)
        build_fixture(root)
        summary_df, timeline_df, note_text = builder_module.build_forensic_pack(root)
        builder_module.write_csv(summary_df, root / builder_module.SUMMARY_OUTPUT)
        builder_module.write_csv(timeline_df, root / builder_module.TIMELINE_OUTPUT)
        builder_module.write_text(note_text, root / builder_module.NOTE_OUTPUT)

        assert len(summary_df) == 1, "summary must emit exactly one row"
        assert not timeline_df.empty, "timeline rows must be emitted"
        assert summary_df.iloc[0]["원래_커널로그라벨_ko"] == "미확인", "missing original-label path must resolve to 미확인"
        assert summary_df.iloc[0]["사건유형_결정_ko"] == "전조형 고장"
        assert summary_df.iloc[0]["최종고장양상_결정_ko"] == "급격 종료"
        assert "persistent_5of7" in summary_df.iloc[0]["사건유형_결정규칙_ko"]
        assert "first_final_fault_date == strict_trigger_date" in summary_df.iloc[0]["최종고장양상_결정규칙_ko"]
        assert summary_df.iloc[0]["사건시간양상_판정_ko"] == "전조흔적있음_순수급작보류"
        assert summary_df.iloc[0]["continuity_judgment_ko"] == "동일사건_연속가능성_높음"
        assert summary_df.iloc[0]["event_recommendation_ko"] == "전조형고장으로상향"
        assert summary_df.iloc[0]["확정도_판정_ko"] == "보류"
        assert int(summary_df.iloc[0]["현재표_보정필요여부_flag"]) == 0
        assert summary_df.iloc[0]["earliest_warning_date"] == "2025-01-16"
        assert summary_df.iloc[0]["earliest_onset_date"] == "2025-01-20"
        assert int(summary_df.iloc[0]["pretrigger_window_day_count"]) > 0
        assert int(summary_df.iloc[0]["ae_active_days_pretrigger"]) >= 60
        assert int(summary_df.iloc[0]["longest_consecutive_active_run_days"]) >= 60
        assert (root / builder_module.SUMMARY_OUTPUT).exists(), "summary output file must be written"
        assert (root / builder_module.TIMELINE_OUTPUT).exists(), "timeline output file must be written"
        assert (root / builder_module.NOTE_OUTPUT).exists(), "note output file must be written"
        assert not (root / "_share/panel_day_engine_project_eval_matrix_v1.csv").exists(), "downstream official outputs must not be created"

        required_sections = [
            "## 1. 현재 파일에서 확인된 사실",
            "## 2. 서로 충돌하는 지점",
            "## 3. 지금 가장 안전한 판정",
            "## 4. 왜 보정이 필요한지",
        ]
        for section in required_sections:
            assert section in note_text, f"missing note section: {section}"
        assert "전조흔적은 실제로 있었다" in note_text
        assert "stored-field rule 기준으로 `전조형 고장`" in note_text
        assert "heuristic continuity wording 이 아니라" in note_text
        assert "forensic/explanatory note" in note_text

        timeline_stages = set(timeline_df["단계"].tolist())
        assert "first_warning_date" in timeline_stages
        assert "strict_trigger_date" in timeline_stages
        assert "earliest_warning_date" in timeline_stages
        assert "ae_active_days_pretrigger" in timeline_stages
        assert "longest_consecutive_active_run_days" in timeline_stages
        assert "last_gap_before_trigger_days" in timeline_stages
        assert "event_recommendation_ko" in timeline_stages
        assert "사건유형_결정_ko" in timeline_stages
        assert "최종고장양상_결정_ko" in timeline_stages

    print("smoke_test_panel_day_engine_single_panel_forensic_audit_v1: PASS")


if __name__ == "__main__":
    main()

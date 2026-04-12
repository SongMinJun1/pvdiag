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
                "사건유형_ko": "급작 고장",
                "커널로그_증상명_ko": "전압 변화형",
                "커널로그_원인군_ko": "개방/장치이상형",
                "GPVS_참고유형_ko": "개방/장치이상 계열",
            }
        ],
    )
    write_csv(
        root / "data/conalog/out/panel_day_core.csv",
        [
            {
                "date": "2025-01-20",
                "panel_id": TARGET_PANEL_ID,
                "mid_ratio": 0.91,
                "mid_v_ratio": 0.84,
                "v_drop": 0.17,
                "recon_error": 0.03,
                "confirmed_fault": False,
                "critical_fault": False,
                "final_fault": False,
                "fault_like_day": False,
                "degraded_candidate": False,
                "dead_diag_date": "2025-03-22",
                "diagnosis_date_online": "2025-03-22",
            },
            {
                "date": "2025-03-21",
                "panel_id": TARGET_PANEL_ID,
                "mid_ratio": 0.0,
                "mid_v_ratio": 0.0,
                "v_drop": 1.0,
                "recon_error": 0.08,
                "confirmed_fault": True,
                "critical_fault": False,
                "final_fault": True,
                "fault_like_day": True,
                "degraded_candidate": True,
                "dead_diag_date": "2025-03-22",
                "diagnosis_date_online": "2025-03-22",
            },
        ],
    )
    write_csv(
        root / "data/conalog/out/ae_simple_local_precursor_gate_daily.csv",
        [
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "date": "2025-01-16",
                "cond_evt": False,
                "cond_hs": False,
                "signal_count": 1,
                "ews_warning": True,
                "site_event_soft": False,
                "site_event_hard": False,
                "prefault_B": False,
                "pre_alarm": False,
                "prefault_cond_mid": False,
                "prefault_cond_ae": True,
                "prefault_cond_dtw": False,
            },
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "date": "2025-02-01",
                "cond_evt": True,
                "cond_hs": True,
                "signal_count": 2,
                "ews_warning": False,
                "site_event_soft": False,
                "site_event_hard": False,
                "prefault_B": True,
                "pre_alarm": True,
                "prefault_cond_mid": True,
                "prefault_cond_ae": True,
                "prefault_cond_dtw": True,
            },
            {
                "site": "conalog",
                "panel_id": TARGET_PANEL_ID,
                "date": "2025-03-21",
                "cond_evt": True,
                "cond_hs": False,
                "signal_count": 2,
                "ews_warning": False,
                "site_event_soft": False,
                "site_event_hard": False,
                "prefault_B": True,
                "pre_alarm": True,
                "prefault_cond_mid": True,
                "prefault_cond_ae": True,
                "prefault_cond_dtw": True,
            },
        ],
    )


def main() -> None:
    builder_module = load_builder_module()
    py_compile.compile(str(Path(__file__).with_name("build_panel_day_engine_single_panel_forensic_audit_v1.py")), doraise=True)
    py_compile.compile(str(Path(__file__)), doraise=True)

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
        assert summary_df.iloc[0]["사건시간양상_판정_ko"] == "전조흔적있음_순수급작보류"
        assert summary_df.iloc[0]["확정도_판정_ko"] == "보류"
        assert (root / builder_module.SUMMARY_OUTPUT).exists(), "summary output file must be written"
        assert (root / builder_module.TIMELINE_OUTPUT).exists(), "timeline output file must be written"
        assert (root / builder_module.NOTE_OUTPUT).exists(), "note output file must be written"

        required_sections = [
            "## 1. 현재 파일에서 확인된 사실",
            "## 2. 서로 충돌하는 지점",
            "## 3. 지금 가장 안전한 판정",
            "## 4. 왜 보정이 필요한지",
        ]
        for section in required_sections:
            assert section in note_text, f"missing note section: {section}"

        timeline_stages = set(timeline_df["단계"].tolist())
        assert "first_warning_date" in timeline_stages
        assert "strict_trigger_date" in timeline_stages
        assert "window_ae_active_days" in timeline_stages
        assert "window_min_mid_ratio" in timeline_stages

    print("smoke_test_panel_day_engine_single_panel_forensic_audit_v1: PASS")


if __name__ == "__main__":
    main()

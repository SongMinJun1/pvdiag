from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


TARGET_SITE = "conalog"
TARGET_PANEL_ID = "c42997a6-5881-47e7-9035-7de8a2673b54.1.1"


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def build_fixture(root: Path) -> None:
    share = root / "_share"

    verdict_rows = [
        {
            "site": "conalog",
            "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
            "패널고장여부_ko": "고장",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
        },
        {
            "site": TARGET_SITE,
            "panel_id": TARGET_PANEL_ID,
            "패널고장여부_ko": "고장",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "급격 종료",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 0,
        },
        {
            "site": "gangui",
            "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7",
            "패널고장여부_ko": "고장",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "전조흔적_flag": 0,
            "순수급작_flag": 1,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 1,
        },
        {
            "site": "gangui",
            "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16",
            "패널고장여부_ko": "고장",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "전조흔적_flag": 0,
            "순수급작_flag": 1,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 1,
        },
        {
            "site": "ktc_ess",
            "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12",
            "패널고장여부_ko": "고장",
            "사건유형_ko": "급작 고장",
            "최종고장양상_ko": "급작 발생",
            "전조흔적_flag": 0,
            "순수급작_flag": 1,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 1,
        },
        {
            "site": "ktc_ess",
            "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
            "패널고장여부_ko": "고장",
            "사건유형_ko": "전조형 고장",
            "최종고장양상_ko": "진행성 악화",
            "전조흔적_flag": 1,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 1,
            "급작평가셋편입_flag": 0,
        },
        {
            "site": "conalog",
            "panel_id": "nonfault.1",
            "패널고장여부_ko": "비고장",
            "사건유형_ko": "공통원인 이벤트",
            "최종고장양상_ko": "해당없음",
            "전조흔적_flag": 0,
            "순수급작_flag": 0,
            "전조평가셋편입_flag": 0,
            "급작평가셋편입_flag": 0,
        },
    ]
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        [
            "site",
            "panel_id",
            "패널고장여부_ko",
            "사건유형_ko",
            "최종고장양상_ko",
            "전조흔적_flag",
            "순수급작_flag",
            "전조평가셋편입_flag",
            "급작평가셋편입_flag",
        ],
    )

    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        [
            {"site": "conalog", "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0"},
            {"site": TARGET_SITE, "panel_id": TARGET_PANEL_ID},
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7"},
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16"},
            {"site": "ktc_ess", "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12"},
            {"site": "ktc_ess", "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4"},
        ],
        ["site", "panel_id"],
    )

    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {
                "site": "conalog",
                "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
                "preferred_precursor_onset_date": "2024-11-08",
            },
            {
                "site": "ktc_ess",
                "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
                "preferred_precursor_onset_date": "2025-01-27",
            },
        ],
        ["site", "panel_id", "preferred_precursor_onset_date"],
    )

    write_csv(
        share / "panel_date_reaudit_working.csv",
        [
            {
                "site": "conalog",
                "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
                "first_warning_date": "2024-11-06",
                "retrospective_onset_date": "2024-11-06",
                "strict_trigger_date": "2024-11-26",
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
            },
            {
                "site": TARGET_SITE,
                "panel_id": TARGET_PANEL_ID,
                "first_warning_date": "2025-01-20",
                "retrospective_onset_date": "2025-01-20",
                "strict_trigger_date": "2025-03-21",
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
            },
            {
                "site": "gangui",
                "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "strict_trigger_date": "2025-06-08",
                "onset_confidence": "",
                "onset_method": "",
            },
            {
                "site": "gangui",
                "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16",
                "first_warning_date": "",
                "retrospective_onset_date": "",
                "strict_trigger_date": "2025-06-08",
                "onset_confidence": "",
                "onset_method": "",
            },
            {
                "site": "ktc_ess",
                "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12",
                "first_warning_date": "",
                "retrospective_onset_date": "2025-08-16",
                "strict_trigger_date": "2025-08-16",
                "onset_confidence": "medium",
                "onset_method": "strict_trigger_fallback",
            },
            {
                "site": "ktc_ess",
                "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
                "first_warning_date": "2025-01-25",
                "retrospective_onset_date": "2025-01-25",
                "strict_trigger_date": "2025-02-02",
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
            },
        ],
        [
            "site",
            "panel_id",
            "first_warning_date",
            "retrospective_onset_date",
            "strict_trigger_date",
            "onset_confidence",
            "onset_method",
        ],
    )

    write_csv(
        share / "vendor_reply_adjudication_latest.csv",
        [
            {"site": TARGET_SITE, "panel_id": TARGET_PANEL_ID, "vendor_fault_family": "open_or_device_issue_like", "vendor_reply_class": "likely_positive"}
        ],
        ["site", "panel_id", "vendor_fault_family", "vendor_reply_class"],
    )

    def write_site_core(site: str, rows: list[dict[str, object]]) -> None:
        write_csv(
            root / "data" / site / "out" / "panel_day_core.csv",
            rows,
            ["site", "panel_id", "date", "final_fault", "critical_fault", "dead_diag_date"],
        )

    def write_site_gate(site: str, rows: list[dict[str, object]]) -> None:
        write_csv(
            root / "data" / site / "out" / "ae_simple_local_precursor_gate_daily.csv",
            rows,
            ["site", "panel_id", "date", "ews_warning"],
        )

    write_site_core(
        "conalog",
        [
            {"site": "conalog", "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0", "date": "2024-11-25", "final_fault": 0, "critical_fault": 0, "dead_diag_date": "2025-12-19"},
            {"site": "conalog", "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0", "date": "2024-11-26", "final_fault": 1, "critical_fault": 0, "dead_diag_date": "2025-12-19"},
            {"site": TARGET_SITE, "panel_id": TARGET_PANEL_ID, "date": "2025-03-20", "final_fault": 0, "critical_fault": 0, "dead_diag_date": "2025-03-22"},
            {"site": TARGET_SITE, "panel_id": TARGET_PANEL_ID, "date": "2025-03-21", "final_fault": 1, "critical_fault": 0, "dead_diag_date": "2025-03-22"},
        ],
    )
    write_site_gate(
        "conalog",
        [
            {"site": "conalog", "panel_id": "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0", "date": "2024-11-06", "ews_warning": 1},
            {"site": TARGET_SITE, "panel_id": TARGET_PANEL_ID, "date": "2025-01-16", "ews_warning": 1},
        ],
    )

    write_site_core(
        "gangui",
        [
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7", "date": "2025-06-08", "final_fault": 0, "critical_fault": 0, "dead_diag_date": ""},
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16", "date": "2025-06-08", "final_fault": 1, "critical_fault": 0, "dead_diag_date": ""},
        ],
    )
    write_site_gate(
        "gangui",
        [
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7", "date": "2025-06-08", "ews_warning": 0},
            {"site": "gangui", "panel_id": "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16", "date": "2025-06-08", "ews_warning": 0},
        ],
    )

    write_site_core(
        "ktc_ess",
        [
            {"site": "ktc_ess", "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12", "date": "2025-08-16", "final_fault": 1, "critical_fault": 0, "dead_diag_date": ""},
            {"site": "ktc_ess", "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4", "date": "2025-02-02", "final_fault": 0, "critical_fault": 0, "dead_diag_date": ""},
        ],
    )
    write_site_gate(
        "ktc_ess",
        [
            {"site": "ktc_ess", "panel_id": "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12", "date": "2025-08-16", "ews_warning": 0},
            {"site": "ktc_ess", "panel_id": "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4", "date": "2025-01-25", "ews_warning": 1},
        ],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_fault_panel_event_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_fault_panel_event_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_fault_panel_event_audit_v1.csv",
        repo_root / "_share/panel_day_engine_fault_panel_event_audit_summary_v1.csv",
        repo_root / "_share/panel_day_engine_fault_panel_event_audit_note_v1.md",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_fault_panel_event_audit_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        audit_df = pd.read_csv(root / "_share" / "panel_day_engine_fault_panel_event_audit_v1.csv")
        summary_df = pd.read_csv(root / "_share" / "panel_day_engine_fault_panel_event_audit_summary_v1.csv")
        note_text = (root / "_share" / "panel_day_engine_fault_panel_event_audit_note_v1.md").read_text(encoding="utf-8-sig")

        assert_true(len(audit_df) == 6, f"expected 6 fault panels, found {len(audit_df)}")
        assert_true(len(summary_df) == 1, "summary must contain exactly one row")
        assert_true(audit_df[["site", "panel_id"]].duplicated().sum() == 0, "audit rows must be unique by (site, panel_id)")
        assert_true(audit_df["site"].eq("conalog").any(), "fixture should contain conalog rows")
        assert_true(~audit_df["panel_id"].eq("nonfault.1").any(), "non-fault panel must not be included")

        c429_row = audit_df.loc[(audit_df["site"].eq(TARGET_SITE)) & (audit_df["panel_id"].eq(TARGET_PANEL_ID))]
        assert_true(len(c429_row) == 1, "c42997 target row must appear exactly once")
        c429_row = c429_row.iloc[0]
        assert_true(c429_row["사건유형_재판정_ko"] == "전조형 고장", "c42997 must re-evaluate to precursor")
        assert_true(c429_row["최종고장양상_재판정_ko"] == "급격 종료", "c42997 terminal pattern should be abrupt ending")

        precursor_rows = audit_df.loc[audit_df["사건유형_재판정_ko"].eq("전조형 고장")]
        assert_true(len(precursor_rows) == 3, "fixture precursor re-evaluation count should be 3")
        assert_true(
            precursor_rows["panel_id"].isin(
                [
                    "7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0",
                    TARGET_PANEL_ID,
                    "70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4",
                ]
            ).all(),
            "all explicit precursor-rule hits must re-evaluate to precursor",
        )

        abrupt_rows = audit_df.loc[audit_df["사건유형_재판정_ko"].eq("급작 고장")]
        assert_true(len(abrupt_rows) == 3, "fixture abrupt path should produce 3 rows")
        assert_true(
            set(abrupt_rows["panel_id"])
            == {
                "bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7",
                "bf1a912f-6cf0-4f12-8e97-9d9d86576511.2.16",
                "10305b40-b67e-40d1-9cd1-271b6642a3d9.2.12",
            },
            "abrupt rows mismatch",
        )
        assert_true(abrupt_rows["최종고장양상_재판정_ko"].eq("급작 발생").all(), "abrupt rows should keep abrupt terminal pattern")

        holdout_rows = audit_df.loc[audit_df["사건유형_재판정_ko"].eq("고장유형 보류")]
        assert_true(len(holdout_rows) == 0, "fixture holdout path should produce 0 rows")

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["고유_고장패널수"]) == 6, "summary fault-panel count mismatch")
        assert_true(int(summary_row["사건유형_재판정_전조형수"]) == 3, "summary precursor count mismatch")
        assert_true(int(summary_row["사건유형_재판정_급작수"]) == 3, "summary abrupt count mismatch")
        assert_true(int(summary_row["사건유형_재판정_보류수"]) == 0, "summary holdout count mismatch")
        assert_true(int(summary_row["최종고장양상_급격종료수"]) == 1, "summary abrupt-ending count mismatch")
        assert_true(int(summary_row["전조흔적_패널수"]) == 3, "summary precursor-trace count mismatch")
        assert_true(int(summary_row["순수급작_패널수"]) == 3, "summary current pure-abrupt flag count mismatch")
        assert_true(int(summary_row["전조평가셋편입_패널수"]) == 2, "summary precursor-eval inclusion mismatch")
        assert_true(int(summary_row["급작평가셋편입_패널수"]) == 3, "summary abrupt-eval inclusion mismatch")
        assert_true(int(summary_row["해석과평가셋불일치_패널수"]) == 1, "summary mismatch count mismatch")
        assert_true(int(summary_row["현재표_보정필요_패널수"]) == 0, "summary correction-needed count mismatch")

        for section in [
            "## 1. 전체 고장 패널 전수 결과",
            "## 2. 순수 급작 패널 수",
            "## 3. 전조흔적은 있지만 평가셋에 안 들어간 패널",
            "## 4. 지금 바로 고쳐야 하는 패널",
        ]:
            assert_true(section in note_text, f"missing note section: {section}")
        assert_true(TARGET_PANEL_ID in note_text, "note should mention c42997 target")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")
    print("smoke_test_panel_day_engine_fault_panel_event_audit_v1: PASS")


if __name__ == "__main__":
    main()

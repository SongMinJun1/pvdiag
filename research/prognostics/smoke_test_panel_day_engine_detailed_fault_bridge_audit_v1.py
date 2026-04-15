#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {"site": "siteA", "panel_id": "fault_attach_1", "패널고장여부_ko": "고장"},
            {"site": "siteA", "panel_id": "fault_attach_2", "패널고장여부_ko": "고장"},
            {"site": "siteA", "panel_id": "fault_conflict", "패널고장여부_ko": "고장"},
            {"site": "siteA", "panel_id": "fault_miss_1", "패널고장여부_ko": "고장"},
            {"site": "siteB", "panel_id": "fault_miss_2", "패널고장여부_ko": "고장"},
            {"site": "siteC", "panel_id": "fault_attach_3", "패널고장여부_ko": "고장"},
            {"site": "siteZ", "panel_id": "not_fault", "패널고장여부_ko": "미확정"},
        ],
        ["site", "panel_id", "패널고장여부_ko"],
    )

    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        [
            {"site": "siteA", "panel_id": "fault_attach_1", "strict_trigger_date": "2025-01-01", "first_final_fault_date": ""},
            {"site": "siteA", "panel_id": "fault_attach_2", "strict_trigger_date": "", "first_final_fault_date": "2025-01-02"},
            {"site": "siteA", "panel_id": "fault_conflict", "strict_trigger_date": "2025-01-03", "first_final_fault_date": ""},
            {"site": "siteA", "panel_id": "fault_miss_1", "strict_trigger_date": "2025-01-04", "first_final_fault_date": ""},
            {"site": "siteB", "panel_id": "fault_miss_2", "strict_trigger_date": "2025-01-05", "first_final_fault_date": ""},
            {"site": "siteC", "panel_id": "fault_attach_3", "strict_trigger_date": "2025-01-06", "first_final_fault_date": ""},
        ],
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
    )

    candidate_rows_main = [
        {"date": "2025-01-01", "panel_id": "fault_attach_1", "fault_type_max": "F101"},
        {"date": "2025-01-02", "panel_id": "fault_attach_2", "fault_type_max": "F202"},
        {"date": "2025-01-03", "panel_id": "fault_conflict", "fault_type_max": "F301"},
        {"date": "2025-01-06", "panel_id": "fault_attach_3", "fault_type_max": "F7ZZ"},
    ]
    candidate_rows_agree = [
        {"date": "2025-01-01", "panel_id": "fault_attach_1", "fault_type_max": "F101"},
        {"date": "2025-01-02", "panel_id": "fault_attach_2", "fault_type_max": "F202"},
        {"date": "2025-01-03", "panel_id": "fault_conflict", "fault_type_max": "F302"},
        {"date": "2025-01-06", "panel_id": "fault_attach_3", "fault_type_max": "F7ZZ"},
    ]
    candidate_rows_sparse = [
        {"date": "2025-01-01", "panel_id": "fault_attach_1", "fault_type_max": "F101"},
        {"date": "2025-01-06", "panel_id": "fault_attach_3", "fault_type_max": "F7ZZ"},
    ]

    write_csv(
        root / "data/pvfault/out/PVFAULT_labels_day.csv",
        candidate_rows_main,
        ["date", "panel_id", "fault_type_max"],
    )
    write_csv(
        share / "external_pvfault_20260304/PVFAULT_labels_day.csv",
        candidate_rows_agree,
        ["date", "panel_id", "fault_type_max"],
    )
    write_csv(
        share / "external_pvfault_20260304_215400/PVFAULT_labels_day.csv",
        candidate_rows_sparse,
        ["date", "panel_id", "fault_type_max"],
    )
    write_csv(
        share / "external_pvfault_fixlabel_20260304_174840/PVFAULT_labels_day.csv",
        candidate_rows_agree,
        ["date", "panel_id", "fault_type_max"],
    )
    write_csv(
        share / "final_validation_20260304_172755/pvfault/PVFAULT_labels_day.csv",
        candidate_rows_sparse,
        ["date", "panel_id", "fault_type_max"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_detailed_fault_bridge_audit_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_detailed_fault_bridge_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv",
        repo_root / "_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="detailed_fault_bridge_audit_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        audit_df = pd.read_csv(
            root / "_share/panel_day_engine_detailed_fault_bridge_audit_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )
        summary_df = pd.read_csv(
            root / "_share/panel_day_engine_detailed_fault_bridge_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )

        assert_true(len(audit_df) == 6, f"fault-panel audit row count must be 6, found {len(audit_df)}")
        attach_1 = audit_df.loc[audit_df["panel_id"].eq("fault_attach_1")].iloc[0]
        attach_2 = audit_df.loc[audit_df["panel_id"].eq("fault_attach_2")].iloc[0]
        attach_3 = audit_df.loc[audit_df["panel_id"].eq("fault_attach_3")].iloc[0]
        conflict = audit_df.loc[audit_df["panel_id"].eq("fault_conflict")].iloc[0]
        miss_1 = audit_df.loc[audit_df["panel_id"].eq("fault_miss_1")].iloc[0]
        miss_2 = audit_df.loc[audit_df["panel_id"].eq("fault_miss_2")].iloc[0]

        assert_true(int(attach_1["attachable_flag"]) == 1, "consensus path should attach fault_attach_1")
        assert_true(str(attach_1["consensus_fault_type_code"]) == "F101", "fault_attach_1 consensus code mismatch")
        assert_true(str(attach_2["reference_date"]) == "2025-01-02", "fallback reference-date path failed")
        assert_true(int(attach_2["attachable_flag"]) == 1, "fallback first_final_fault_date path should attach fault_attach_2")
        assert_true(int(attach_3["attachable_flag"]) == 1, "consensus path should attach fault_attach_3")

        assert_true(int(conflict["exact_match_file_count"]) > 0, "conflict row should still have exact-date matches")
        assert_true(int(conflict["attachable_flag"]) == 0, "conflict row must not attach")
        assert_true(str(conflict["attach_reason_ko"]) == "exact_date_conflict", "conflict reason mismatch")

        assert_true(int(miss_1["exact_match_file_count"]) == 0, "miss row should have zero exact-date matches")
        assert_true(int(miss_1["attachable_flag"]) == 0, "miss row must not attach")
        assert_true(str(miss_1["attach_reason_ko"]) == "no_exact_date_match", "miss reason mismatch")
        assert_true(str(miss_2["attach_reason_ko"]) == "no_exact_date_match", "second miss reason mismatch")

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["고장패널수"]) == 6, "summary fault-panel count mismatch")
        assert_true(int(summary_row["세부fault_부착수"]) == 3, "summary attached count mismatch")
        assert_true(int(summary_row["세부fault_보류수"]) == 3, "summary hold count mismatch")
        assert_true(int(summary_row["exact_date_match_패널수"]) == 4, "summary exact-date-match count mismatch")
        assert_true(int(summary_row["exact_date_conflict_패널수"]) == 1, "summary conflict count mismatch")
        assert_true(int(summary_row["exact_date_miss_패널수"]) == 2, "summary miss count mismatch")
        assert_true("exact-date consensus" in str(summary_row["note_ko"]), "summary note should mention exact-date rule")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")

    print("smoke_test_panel_day_engine_detailed_fault_bridge_audit_v1.py: PASS")


if __name__ == "__main__":
    main()

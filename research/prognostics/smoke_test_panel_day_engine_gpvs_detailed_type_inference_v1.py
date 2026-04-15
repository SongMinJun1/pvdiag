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


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def add_panel_history(
    rows: list[dict[str, object]],
    panel_id: str,
    reference_date: str,
    *,
    mode: str,
) -> None:
    ref_ts = pd.Timestamp(reference_date)
    baseline = [
        ("2025-01-05", 0.95, 0.05, 1.0, 0.10, 0.010),
        ("2025-01-06", 0.96, 0.06, 1.1, 0.12, 0.011),
        ("2025-01-07", 0.94, 0.04, 0.9, 0.11, 0.009),
        ("2025-01-08", 0.97, 0.07, 1.2, 0.13, 0.012),
        ("2025-01-09", 0.93, 0.03, 0.8, 0.09, 0.008),
    ]
    for date_str, mid_ratio, v_drop, dtw_dist, hs_score, recon_error in baseline:
        rows.append(
            {
                "date": date_str,
                "panel_id": panel_id,
                "mid_ratio": mid_ratio,
                "v_drop": v_drop,
                "dtw_dist": dtw_dist,
                "hs_score": hs_score,
                "recon_error": recon_error,
            }
        )

    if mode == "attach":
        rows.append(
            {
                "date": ref_ts.strftime("%Y-%m-%d"),
                "panel_id": panel_id,
                "mid_ratio": 0.50,
                "v_drop": 0.60,
                "dtw_dist": 8.0,
                "hs_score": 0.80,
                "recon_error": 0.080,
            }
        )
    elif mode == "defer":
        rows.append(
            {
                "date": ref_ts.strftime("%Y-%m-%d"),
                "panel_id": panel_id,
                "mid_ratio": 0.91,
                "v_drop": 0.09,
                "dtw_dist": 1.4,
                "hs_score": 0.14,
                "recon_error": 0.014,
            }
        )
    elif mode == "impossible_no_baseline":
        rows[:] = [row for row in rows if row["panel_id"] != panel_id]
        rows.append(
            {
                "date": ref_ts.strftime("%Y-%m-%d"),
                "panel_id": panel_id,
                "mid_ratio": 0.55,
                "v_drop": 0.55,
                "dtw_dist": 6.0,
                "hs_score": 0.75,
                "recon_error": 0.070,
            }
        )
    elif mode == "impossible_no_event":
        pass
    else:
        raise ValueError(f"unexpected mode: {mode}")


def build_fixture(root: Path) -> None:
    share = root / "_share"
    gpvs_out = root / "data" / "gpvs" / "out"
    panel_core_dir = root / "data" / "siteA" / "out"
    share.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)
    panel_core_dir.mkdir(parents=True, exist_ok=True)

    fault_rows = [
        {"site": "siteA", "panel_id": "fault_attach_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "fault_attach_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "fault_defer_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "fault_defer_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "fault_impossible_1", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
        {"site": "siteA", "panel_id": "fault_impossible_2", "strict_trigger_date": "2025-01-10", "first_final_fault_date": ""},
    ]
    write_csv(
        share / "panel_day_engine_fault_panel_event_audit_v1.csv",
        fault_rows,
        ["site", "panel_id", "strict_trigger_date", "first_final_fault_date"],
    )

    verdict_rows = [
        {"site": "siteA", "panel_id": "fault_attach_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "fault_attach_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전기적 고장 계열"},
        {"site": "siteA", "panel_id": "fault_defer_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "모듈 손상 계열"},
        {"site": "siteA", "panel_id": "fault_defer_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "모듈 손상 계열"},
        {"site": "siteA", "panel_id": "fault_impossible_1", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
        {"site": "siteA", "panel_id": "fault_impossible_2", "패널고장여부_ko": "고장", "GPVS_참고유형_ko": "전압 변화 계열"},
    ]
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        verdict_rows,
        ["site", "panel_id", "패널고장여부_ko", "GPVS_참고유형_ko"],
    )

    bytype_rows = []
    thresholds = {"F1": 3.0, "F2": 4.0, "F3": 5.0, "F4": 6.0, "F5": 7.0, "F6": 8.0, "F7": 9.0}
    for fault_code, threshold in thresholds.items():
        bytype_rows.append(
            {
                "fault_type": f"{fault_code}_fixture",
                "sid": 1,
                "score": "ensemble_top2_raw",
                "threshold_fpr1": threshold,
                "ap": 0.90,
                "roc_auc": 0.90,
            }
        )
    write_csv(
        gpvs_out / "EXTERNAL_GPVS_ENSEMBLE2_BYTYPE_METRICS.csv",
        bytype_rows,
        ["fault_type", "sid", "score", "threshold_fpr1", "ap", "roc_auc"],
    )

    write_csv(
        gpvs_out / "EXTERNAL_GPVS_METRICS.csv",
        [
            {"score": "level_drop_like", "roc_auc": 0.70},
            {"score": "v_drop_like", "roc_auc": 0.75},
            {"score": "dtw_like", "roc_auc": 0.80},
            {"score": "hs_like", "roc_auc": 0.65},
        ],
        ["score", "roc_auc"],
    )

    panel_core_rows: list[dict[str, object]] = []
    add_panel_history(panel_core_rows, "fault_attach_1", "2025-01-10", mode="attach")
    add_panel_history(panel_core_rows, "fault_attach_2", "2025-01-10", mode="attach")
    add_panel_history(panel_core_rows, "fault_defer_1", "2025-01-10", mode="defer")
    add_panel_history(panel_core_rows, "fault_defer_2", "2025-01-10", mode="defer")
    add_panel_history(panel_core_rows, "fault_impossible_1", "2025-01-10", mode="impossible_no_baseline")
    add_panel_history(panel_core_rows, "fault_impossible_2", "2025-01-10", mode="impossible_no_event")
    write_csv(
        panel_core_dir / "panel_day_core.csv",
        panel_core_rows,
        ["date", "panel_id", "mid_ratio", "v_drop", "dtw_dist", "hs_score", "recon_error"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_detailed_type_inference_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_gpvs_detailed_type_inference_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_inference_v1.csv",
        repo_root / "_share/panel_day_engine_gpvs_detailed_type_summary_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="gpvs_detailed_type_inference_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        assert_true(not any(root.rglob("PVFAULT_labels_day.csv")), "fixture must not rely on synthetic PVFAULT label files")

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        audit_path = root / "_share/panel_day_engine_gpvs_detailed_type_inference_v1.csv"
        summary_path = root / "_share/panel_day_engine_gpvs_detailed_type_summary_v1.csv"
        assert_true(audit_path.exists(), "missing detailed-type audit csv")
        assert_true(summary_path.exists(), "missing detailed-type summary csv")

        audit_df = pd.read_csv(audit_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")

        assert_true(len(audit_df) == 6, f"fault panel count must be 6, found {len(audit_df)}")
        assert_true(not audit_df.duplicated(subset=["site", "panel_id"]).any(), "audit csv must be unique by fault panel")
        assert_true(set(audit_df["gpvs_detailed_fault_status_ko"]) == {"부착", "판정유보", "추론불가"}, "all three status paths should appear")

        attached_count = int(audit_df["gpvs_detailed_fault_status_ko"].eq("부착").sum())
        deferred_count = int(audit_df["gpvs_detailed_fault_status_ko"].eq("판정유보").sum())
        impossible_count = int(audit_df["gpvs_detailed_fault_status_ko"].eq("추론불가").sum())
        assert_true(attached_count == 2, f"expected 2 attached rows, found {attached_count}")
        assert_true(deferred_count == 2, f"expected 2 deferred rows, found {deferred_count}")
        assert_true(impossible_count == 2, f"expected 2 impossible rows, found {impossible_count}")

        attach_row = audit_df.loc[audit_df["panel_id"].eq("fault_attach_1")].iloc[0]
        defer_row = audit_df.loc[audit_df["panel_id"].eq("fault_defer_1")].iloc[0]
        impossible_row = audit_df.loc[audit_df["panel_id"].eq("fault_impossible_1")].iloc[0]

        assert_true(attach_row["gpvs_family_label"] == "전기적 고장 계열", "family label should pass through unchanged")
        assert_true(normalize_text(attach_row["gpvs_detailed_fault_code"]) == "F1", "attached top code mismatch")
        assert_true(normalize_text(attach_row["gpvs_detailed_fault_rank2_code"]) == "F2", "attached rank2 code mismatch")
        assert_true(float(attach_row["gpvs_detailed_fault_score"]) > 0, "attached score should be positive")
        assert_true(defer_row["gpvs_detailed_fault_status_ko"] == "판정유보", "deferred path mismatch")
        assert_true(normalize_text(defer_row["gpvs_detailed_fault_code"]) == "F1", "deferred row should still keep top code")
        assert_true("threshold" in str(defer_row["gpvs_detailed_fault_reason_ko"]), "deferred reason should mention threshold")
        assert_true(impossible_row["gpvs_detailed_fault_status_ko"] == "추론불가", "impossible path mismatch")
        assert_true(normalize_text(impossible_row["gpvs_detailed_fault_code"]) == "", "impossible row should keep blank top code")
        assert_true(
            "baseline" in str(impossible_row["gpvs_detailed_fault_reason_ko"])
            or "row 없음" in str(impossible_row["gpvs_detailed_fault_reason_ko"])
            or "usable" in str(impossible_row["gpvs_detailed_fault_reason_ko"]),
            "impossible reason should mention missing baseline/event row",
        )

        summary_row = summary_df.iloc[0]
        assert_true(int(summary_row["고장패널수"]) == 6, "summary fault-panel count mismatch")
        assert_true(int(summary_row["세부fault_부착수"]) == attached_count, "summary attached count mismatch")
        assert_true(int(summary_row["세부fault_판정유보수"]) == deferred_count, "summary deferred count mismatch")
        assert_true(int(summary_row["세부fault_추론불가수"]) == impossible_count, "summary impossible count mismatch")
        assert_true("synthetic PVFAULT_labels_day panel_id direct bridge" in str(summary_row["note_ko"]), "summary note should explicitly exclude synthetic PVFAULT bridge")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()

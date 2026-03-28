#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_common_inputs(share_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    canonical_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "vendor_same_label_case",
                "strict_trigger_date": "2025-05-01",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=critical_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P1",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
            {
                "site": "demo",
                "panel_id": "excluded_to_manual_case",
                "strict_trigger_date": "2025-05-02",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=critical_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P1",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
            {
                "site": "demo",
                "panel_id": "vendor_negative_case",
                "strict_trigger_date": "2025-05-03",
                "candidate_validity": "",
                "onset_confidence": "medium",
                "reason_summary": "strict_method=critical_fault_flag|shadow_frac=0.0|group_off_frac=0.0|recovery_reset=no",
                "review_priority": "P2",
                "vendor_reply_class": "",
                "vendor_fault_family": "",
                "note": "",
            },
        ]
    )
    canonical_df.to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

    vendor_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "vendor_same_label_case",
                "strict_trigger_date": "2025-05-01",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "diode_like",
                "vendor_note": "positive vendor support",
            },
            {
                "site": "demo",
                "panel_id": "vendor_negative_case",
                "strict_trigger_date": "2025-05-03",
                "vendor_reply_class": "vendor_rejected",
                "vendor_fault_family": "none_visible",
                "vendor_note": "negative vendor support",
            },
        ]
    )
    vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

    actionability_df = pd.DataFrame(
        [
            {
                "site": "demo",
                "panel_id": "vendor_same_label_case",
                "strict_trigger_date": "2025-05-01",
                "actionability_v3": "maintenance_candidate",
            },
            {
                "site": "demo",
                "panel_id": "excluded_to_manual_case",
                "strict_trigger_date": "2025-05-02",
                "actionability_v3": "monitor_only",
            },
            {
                "site": "demo",
                "panel_id": "vendor_negative_case",
                "strict_trigger_date": "2025-05-03",
                "actionability_v3": "monitor_only",
            },
        ]
    )
    actionability_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")
    return canonical_df, vendor_df


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "evaluate_truth_seed_impact_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_truth_review_copyback_apply_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        share_dir.mkdir(parents=True, exist_ok=True)

        canonical_df, _vendor_df = write_common_inputs(share_dir)
        original_canonical_csv = canonical_df.to_csv(index=False)

        shutil.copyfile(
            share_dir / "panel_date_reaudit_working.csv",
            share_dir / "panel_date_reaudit_working_proposed_v1.csv",
        )

        identical_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(identical_res.returncode == 0, f"identical run failed:\n{identical_res.stdout}\n{identical_res.stderr}")

        identical_summary_df = pd.read_csv(share_dir / "truth_seed_impact_summary_v1.csv", encoding="utf-8-sig")
        identical_metric_df = pd.read_csv(share_dir / "truth_seed_impact_metric_delta_v1.csv", encoding="utf-8-sig")
        identical_changed_df = pd.read_csv(share_dir / "truth_seed_impact_changed_cases_v1.csv", encoding="utf-8-sig")

        identical_summary_row = identical_summary_df.loc[identical_summary_df["record_type"].eq("summary")].iloc[0]
        assert_true(int(identical_summary_row["changed_case_count"]) == 0, "identical inputs should produce zero changed cases")
        assert_true(
            float(identical_metric_df["delta_f1"].abs().sum()) == 0.0,
            "identical current/proposed inputs should produce zero F1 deltas",
        )
        assert_true(identical_changed_df.empty, "identical current/proposed inputs should not emit changed cases")

        proposed_df = canonical_df.copy()
        proposed_df.loc[proposed_df["panel_id"].eq("vendor_same_label_case"), "candidate_validity"] = "true_positive"
        proposed_df.loc[proposed_df["panel_id"].eq("excluded_to_manual_case"), "candidate_validity"] = "false_positive"
        proposed_df.to_csv(share_dir / "panel_date_reaudit_working_proposed_v1.csv", index=False, encoding="utf-8-sig")

        changed_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(changed_res.returncode == 0, f"changed run failed:\n{changed_res.stdout}\n{changed_res.stderr}")

        summary_df = pd.read_csv(share_dir / "truth_seed_impact_summary_v1.csv", encoding="utf-8-sig")
        metric_df = pd.read_csv(share_dir / "truth_seed_impact_metric_delta_v1.csv", encoding="utf-8-sig")
        changed_df = pd.read_csv(share_dir / "truth_seed_impact_changed_cases_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output should not be empty")
        assert_true(not metric_df.empty, "metric delta output should not be empty")
        assert_true(not changed_df.empty, "changed cases output should not be empty")

        summary_row = summary_df.loc[summary_df["record_type"].eq("summary")].iloc[0]
        assert_true(
            int(summary_row["delta_manual_truth_present_count_total"]) == 2,
            "manual truth present count delta should reflect the two proposed seeds",
        )
        assert_true(
            int(summary_row["changed_case_count_vendor_to_manual_same_label"]) == 2,
            "vendor->manual same-label changes should appear once per truth_mode",
        )
        assert_true(
            int(summary_row["changed_case_count_excluded_to_manual_scored"]) == 2,
            "excluded->manual scored changes should appear once per truth_mode",
        )

        same_label_rows = changed_df.loc[changed_df["panel_id"].eq("vendor_same_label_case")]
        assert_true(
            same_label_rows["change_type"].eq("vendor_to_manual_same_label").all(),
            "synthetic proposed manual truth should shift vendor_truth to manual_truth without changing polarity",
        )

        overall_strict_maintenance = metric_df.loc[
            metric_df["truth_mode"].eq("strict")
            & metric_df["prediction_mode"].eq("maintenance")
            & metric_df["source_split"].eq("overall")
        ].iloc[0]
        assert_true(
            int(overall_strict_maintenance["delta_manual_truth_present_count"]) == 2,
            "metric delta manual truth count should align with proposed seeds",
        )
        assert_true(
            int(overall_strict_maintenance["delta_vendor_truth_used_count"]) == -1,
            "vendor truth use should decrease when a vendor-backed row becomes manual truth",
        )

        current_canonical_csv = pd.read_csv(
            share_dir / "panel_date_reaudit_working.csv",
            encoding="utf-8-sig",
        ).to_csv(index=False)
        assert_true(current_canonical_csv == original_canonical_csv, "canonical source file should remain unchanged")

        print("[OK] outputs generate")
        print("[OK] identical current/proposed inputs produce zero deltas")
        print("[OK] synthetic proposed manual truth shifts vendor_truth to manual_truth without changing polarity")
        print("[OK] changed_case_count and manual_truth_present_count deltas are consistent")
        print("[OK] no canonical source file is modified")

    safe_smoke_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

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


def make_core_rows(anchor_date: str, panels: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": anchor_date,
                "panel_id": panel_id,
                "group_key_base": group_key_base,
            }
            for panel_id, group_key_base in panels
        ]
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_critical_actionability_shadow_v3.py"
    smoke_v2 = root / "research" / "prognostics" / "smoke_test_critical_phenotype_shadow_v2.py"
    smoke_onset = root / "research" / "prognostics" / "smoke_test_panel_onset_shadow.py"
    smoke_vendor = root / "research" / "prognostics" / "smoke_test_vendor_reply_adjudication.py"
    smoke_field = root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        out_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        out_dir.mkdir(parents=True, exist_ok=True)

        v2_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_cluster_a",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 1,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_cluster_b",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 1,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_cluster_c",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 1,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "anchor_date": "2025-03-11",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 1,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_long_hold",
                    "strict_trigger_date": "2025-03-12",
                    "anchor_date": "2025-03-12",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 0,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_missing_onset",
                    "strict_trigger_date": "2025-03-13",
                    "anchor_date": "2025-03-13",
                    "critical_phenotype_v2": "borderline_electrical_review",
                    "cluster_guard_flag": 0,
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_electrical",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v2": "electrical_fault_like",
                    "cluster_guard_flag": 0,
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical",
                },
            ]
        )
        v2_df.to_csv(share_dir / "critical_phenotype_shadow_v2_latest.csv", index=False, encoding="utf-8-sig")

        onset_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "days_earlier_than_trigger": 0,
                    "onset_confidence": "medium",
                    "onset_method": "strict_trigger_fallback",
                    "reason_summary": "strict_method=critical_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
                {
                    "site": "demo",
                    "panel_id": "p_long_hold",
                    "strict_trigger_date": "2025-03-12",
                    "days_earlier_than_trigger": 60,
                    "onset_confidence": "high",
                    "onset_method": "persistent_5of7",
                    "reason_summary": "strict_method=critical_fault_flag|recovery_reset=no|shadow_frac=0.0|group_off_frac=0.0",
                },
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_cluster_a", "vendor_reply_class": "vendor_no_info", "vendor_fault_family": "unknown"},
                {"site": "demo", "panel_id": "p_electrical", "vendor_reply_class": "field_confirmed_positive", "vendor_fault_family": "electrical"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_core_rows(
                    "2025-03-10",
                    [
                        ("p_cluster_a", "g1"),
                        ("p_cluster_b", "g1"),
                        ("p_cluster_c", "g2"),
                        ("p_electrical", "g3"),
                        ("p_normal", "g1"),
                    ],
                ),
                make_core_rows(
                    "2025-03-11",
                    [
                        ("p_singleton", "g9"),
                        ("p_other", "g8"),
                    ],
                ),
                make_core_rows(
                    "2025-03-12",
                    [
                        ("p_long_hold", "g10"),
                        ("p_long_other", "g11"),
                    ],
                ),
                make_core_rows(
                    "2025-03-13",
                    [
                        ("p_missing_onset", "g12"),
                        ("p_missing_other", "g13"),
                    ],
                ),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"critical actionability v3 build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest = pd.read_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "critical_actionability_shadow_v3_summary.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(latest) == len(v2_df), "no new candidates should be created")
        by_panel = latest.set_index("panel_id")

        assert_true(by_panel.loc["p_cluster_a", "critical_phenotype_v3"] == "common_cause_borderline", "borderline cluster should be classified as common_cause_borderline")
        assert_true(by_panel.loc["p_cluster_b", "critical_phenotype_v3"] == "common_cause_borderline", "borderline cluster member should stay common-cause")
        assert_true(by_panel.loc["p_cluster_a", "actionability_v3"] == "common_cause_review", "common-cause borderline should remain common_cause_review")
        assert_true(by_panel.loc["p_singleton", "critical_phenotype_v3"] == "singleton_borderline_review", "singleton borderline should remain singleton review")
        assert_true(by_panel.loc["p_singleton", "actionability_v3"] == "singleton_review", "short-horizon singleton should remain singleton review")
        assert_true(by_panel.loc["p_long_hold", "critical_phenotype_v3"] == "singleton_monitor_hold", "long-horizon isolated singleton should become singleton_monitor_hold")
        assert_true(by_panel.loc["p_long_hold", "actionability_v3"] == "monitor_only", "long-horizon isolated singleton should demote to monitor_only")
        assert_true(int(by_panel.loc["p_long_hold", "singleton_hold_flag"]) == 1, "long-horizon hold flag mismatch")
        assert_true(by_panel.loc["p_missing_onset", "critical_phenotype_v3"] == "singleton_borderline_review", "missing onset context should preserve singleton review")
        assert_true(by_panel.loc["p_missing_onset", "actionability_v3"] == "singleton_review", "missing onset context should keep singleton_review")
        assert_true(int(by_panel.loc["p_missing_onset", "singleton_hold_flag"]) == 0, "missing onset context should not activate hold")
        assert_true(by_panel.loc["p_electrical", "critical_phenotype_v3"] == "electrical_fault_like", "maintenance phenotype should stay unchanged")
        assert_true(by_panel.loc["p_electrical", "actionability_v3"] == "maintenance_candidate", "maintenance phenotype should map to maintenance_candidate")
        assert_true(int(by_panel.loc["p_cluster_a", "same_site_borderline_count_anchor_date"]) == 3, "same-site borderline count mismatch")
        assert_true(int(by_panel.loc["p_cluster_a", "same_group_borderline_count_anchor_date"]) == 2, "same-group borderline count mismatch")
        assert_true(int(summary.iloc[0]["count_common_cause_borderline"]) == 3, "summary common-cause borderline count mismatch")
        assert_true(int(summary.iloc[0]["count_singleton_borderline_review"]) == 2, "summary singleton borderline count mismatch")
        assert_true(int(summary.iloc[0]["count_singleton_monitor_hold"]) == 1, "summary singleton monitor hold count mismatch")
        assert_true(int(summary.iloc[0]["count_singleton_review"]) == 2, "summary singleton review count mismatch")

    smoke_v2_res = run([sys.executable, str(smoke_v2)], root)
    assert_true(smoke_v2_res.returncode == 0, f"critical phenotype v2 smoke failed:\n{smoke_v2_res.stdout}\n{smoke_v2_res.stderr}")
    smoke_onset_res = run([sys.executable, str(smoke_onset)], root)
    assert_true(smoke_onset_res.returncode == 0, f"panel onset shadow smoke failed:\n{smoke_onset_res.stdout}\n{smoke_onset_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] no new candidates are created")
    print("[OK] a synthetic isolated long-horizon singleton borderline becomes singleton_monitor_hold / monitor_only")
    print("[OK] a synthetic borderline cluster is classified as common_cause_borderline")
    print("[OK] a synthetic singleton borderline remains singleton_borderline_review")
    print("[OK] synthetic singleton with missing onset context preserves existing behavior")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

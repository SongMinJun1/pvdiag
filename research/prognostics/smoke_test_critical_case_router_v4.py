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
    build_script = root / "research" / "prognostics" / "build_critical_case_router_v4.py"
    smoke_v3 = root / "research" / "prognostics" / "smoke_test_critical_actionability_shadow_v3.py"
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

        v3_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_outbound",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                    "vendor_reply_class": "field_confirmed_positive",
                    "vendor_fault_family": "electrical",
                },
                {
                    "site": "demo",
                    "panel_id": "p_cluster_a",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                    "vendor_reply_class": "vendor_no_info",
                    "vendor_fault_family": "unknown",
                },
                {
                    "site": "demo",
                    "panel_id": "p_cluster_b",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "actionability_v3": "common_cause_review",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
                {
                    "site": "demo",
                    "panel_id": "p_singleton",
                    "strict_trigger_date": "2025-03-11",
                    "anchor_date": "2025-03-11",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                    "vendor_reply_class": "vendor_rejected",
                    "vendor_fault_family": "none_visible",
                },
                {
                    "site": "demo",
                    "panel_id": "p_monitor",
                    "strict_trigger_date": "2025-03-12",
                    "anchor_date": "2025-03-12",
                    "critical_phenotype_v3": "shape_only_monitor",
                    "actionability_v3": "monitor_only",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                },
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_outbound", "vendor_reply_class": "field_confirmed_positive", "vendor_fault_family": "electrical"},
                {"site": "demo", "panel_id": "p_singleton", "vendor_reply_class": "vendor_rejected", "vendor_fault_family": "none_visible"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_core_rows(
                    "2025-03-10",
                    [
                        ("p_outbound", "g9"),
                        ("p_cluster_a", "g1"),
                        ("p_cluster_b", "g1"),
                    ],
                ),
                make_core_rows(
                    "2025-03-11",
                    [
                        ("p_singleton", "g2"),
                        ("p_other", "g3"),
                    ],
                ),
                make_core_rows(
                    "2025-03-12",
                    [
                        ("p_monitor", "g4"),
                    ],
                ),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"critical router v4 build failed:\n{build_res.stdout}\n{build_res.stderr}")

        outbound = pd.read_csv(share_dir / "critical_outbound_candidates_v4.csv", low_memory=False, encoding="utf-8-sig")
        cluster_df = pd.read_csv(share_dir / "critical_cluster_review_v4.csv", low_memory=False, encoding="utf-8-sig")
        internal = pd.read_csv(share_dir / "critical_internal_review_v4.csv", low_memory=False, encoding="utf-8-sig")
        monitor = pd.read_csv(share_dir / "critical_monitor_archive_v4.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "critical_case_routing_summary_v4.csv", low_memory=False, encoding="utf-8-sig")

        routed_total = len(outbound) + int(cluster_df["member_panel_count"].sum()) + len(internal) + len(monitor)
        assert_true(routed_total == len(v3_df), "no new candidates should be created and all v3 rows should be routed exactly once")
        assert_true(len(cluster_df) < len(v3_df.loc[v3_df["actionability_v3"].eq("common_cause_review")]), "common-cause rows should aggregate into fewer cluster rows than panel rows")
        assert_true(len(internal) == int(v3_df["actionability_v3"].eq("singleton_review").sum()), "singleton_review rows should remain one-per-panel")
        assert_true("p_monitor" not in set(outbound["panel_id"].astype(str)), "monitor_only rows must not appear in outbound candidates")
        assert_true(set(outbound["actionability_v3"].astype(str)) == {"maintenance_candidate"}, "outbound routing should contain maintenance candidates only")
        assert_true(internal.set_index("panel_id").loc["p_singleton", "internal_review_priority"] == "high", "vendor_rejected singleton should be high internal priority")
        assert_true(int(summary.iloc[0]["common_cause_cluster_count"]) == len(cluster_df), "summary cluster count mismatch")

    smoke_v3_res = run([sys.executable, str(smoke_v3)], root)
    assert_true(smoke_v3_res.returncode == 0, f"critical actionability v3 smoke failed:\n{smoke_v3_res.stdout}\n{smoke_v3_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] no new candidates are created")
    print("[OK] common-cause rows are aggregated into fewer cluster rows than panel rows when synthetic duplicates exist")
    print("[OK] singleton_review rows remain one-per-panel")
    print("[OK] monitor_only rows are excluded from outbound")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

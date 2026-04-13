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
    build_script = root / "research" / "prognostics" / "build_critical_case_packets_v5.py"
    smoke_v4 = root / "research" / "prognostics" / "smoke_test_critical_case_router_v4.py"
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
                {"site": "demo", "panel_id": "p_outbound_leak", "anchor_date": "2025-03-10", "actionability_v3": "maintenance_candidate"},
                {"site": "demo", "panel_id": "p_cluster_a", "anchor_date": "2025-03-10", "actionability_v3": "common_cause_review"},
                {"site": "demo", "panel_id": "p_cluster_b", "anchor_date": "2025-03-10", "actionability_v3": "common_cause_review"},
                {"site": "demo", "panel_id": "p_internal_hold", "anchor_date": "2025-03-11", "actionability_v3": "singleton_review"},
                {"site": "demo", "panel_id": "p_monitor", "anchor_date": "2025-03-12", "actionability_v3": "monitor_only"},
            ]
        )
        v3_df.to_csv(share_dir / "critical_actionability_shadow_v3_latest.csv", index=False, encoding="utf-8-sig")

        outbound_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_outbound_leak",
                    "strict_trigger_date": "2025-03-10",
                    "anchor_date": "2025-03-10",
                    "critical_phenotype_v3": "electrical_fault_like",
                    "actionability_v3": "maintenance_candidate",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                }
            ]
        )
        outbound_df.to_csv(share_dir / "critical_outbound_candidates_v4.csv", index=False, encoding="utf-8-sig")

        cluster_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "cluster_id": "demo:2025-03-10:g1",
                    "anchor_date": "2025-03-10",
                    "group_proxy": "g1",
                    "member_panel_count": 2,
                    "member_panels": "p_cluster_a|p_cluster_b",
                    "representative_panel_id": "p_cluster_a",
                    "critical_phenotype_v3": "common_cause_borderline",
                    "vendor_reply_class": "",
                    "vendor_fault_family": "",
                    "recommended_action": "review_as_common_cause_cluster",
                }
            ]
        )
        cluster_df.to_csv(share_dir / "critical_cluster_review_v4.csv", index=False, encoding="utf-8-sig")

        internal_df = pd.DataFrame(
            [
                {
                    "site": "demo",
                    "panel_id": "p_internal_hold",
                    "strict_trigger_date": "2025-03-11",
                    "anchor_date": "2025-03-11",
                    "critical_phenotype_v3": "singleton_borderline_review",
                    "actionability_v3": "singleton_review",
                    "internal_review_priority": "medium",
                    "vendor_reply_class": "vendor_pattern_positive",
                    "vendor_fault_family": "diode_like",
                }
            ]
        )
        internal_df.to_csv(share_dir / "critical_internal_review_v4.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_internal_hold", "vendor_reply_class": "vendor_pattern_positive", "vendor_fault_family": "diode_like"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_core_rows(
                    "2025-03-10",
                    [
                        ("p_outbound_leak", "g1"),
                        ("p_cluster_a", "g1"),
                        ("p_cluster_b", "g1"),
                    ],
                ),
                make_core_rows(
                    "2025-03-11",
                    [
                        ("p_internal_hold", "g2"),
                    ],
                ),
                make_core_rows(
                    "2025-03-12",
                    [
                        ("p_monitor", "g3"),
                    ],
                ),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"critical case packets v5 build failed:\n{build_res.stdout}\n{build_res.stderr}")

        outbound_pack = pd.read_csv(share_dir / "critical_outbound_pack_v5.csv", low_memory=False, encoding="utf-8-sig")
        cluster_pack = pd.read_csv(share_dir / "critical_cluster_pack_v5.csv", low_memory=False, encoding="utf-8-sig")
        internal_pack = pd.read_csv(share_dir / "critical_internal_review_pack_v5.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "critical_case_packets_summary_v5.csv", low_memory=False, encoding="utf-8-sig")

        routed_total = len(outbound_pack) + int(cluster_df["member_panel_count"].sum()) + len(internal_pack) + int(summary.iloc[0]["monitor_count"])
        assert_true(routed_total == len(v3_df), "no new candidates should be created and all v3 rows should remain accounted for")
        assert_true(int(outbound_pack.set_index("panel_id").loc["p_outbound_leak", "cluster_leakage_flag"]) == 1, "cluster_leakage_flag should trigger on synthetic overlap case")
        assert_true(int(internal_pack.set_index("panel_id").loc["p_internal_hold", "vendor_positive_hold_flag"]) == 1, "vendor_positive_hold_flag should trigger on synthetic internal-review case")
        assert_true(len(cluster_pack) == 1, "synthetic cluster pack should keep one row per cluster")

    smoke_v4_res = run([sys.executable, str(smoke_v4)], root)
    assert_true(smoke_v4_res.returncode == 0, f"critical case router v4 smoke failed:\n{smoke_v4_res.stdout}\n{smoke_v4_res.stderr}")
    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] no new candidates are created")
    print("[OK] cluster_leakage_flag can be triggered on a synthetic overlap case")
    print("[OK] vendor_positive_hold_flag can be triggered on a synthetic internal-review case")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

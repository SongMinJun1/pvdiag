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


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_maintenance_proxy_cluster_audit_v1.py"
    existing_safe_smoke = root / "research" / "prognostics" / "smoke_test_evaluate_maintenance_proxy_shadow_f1_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        share_dir = tmp_root / "_share"
        data_dir = tmp_root / "data" / "demo" / "out"
        share_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)

        selected_rows = []
        broad_specs = [
            ("broadA.0", 4),
            ("broadB.0", 3),
            ("broadC.0", 3),
        ]
        for prefix, count in broad_specs:
            for idx in range(count):
                selected_rows.append(
                    {
                        "site": "demo",
                        "panel_id": f"{prefix}.{idx}",
                        "strict_trigger_date": "2025-03-10",
                        "current_actionability_v3": "",
                        "shadow_actionability_v3": "maintenance_candidate_shadow",
                        "strict_method": "confirmed_fault_flag",
                        "shadow_frac": 0.0,
                        "group_off_frac": 0.0,
                        "recovery_reset": "no",
                        "days_earlier_than_trigger": 0,
                        "onset_confidence": "medium",
                        "onset_method": "strict_trigger_fallback",
                        "mid_ratio": 0.0,
                        "mid_v_ratio": 1.1,
                        "mid_i_ratio": 0.0,
                        "v_drop": -0.1,
                        "coverage_mid": 1.0,
                        "strict_day_group_like_flag": True,
                        "same_group_zero_like_count": count,
                        "same_site_zero_like_count": 10,
                        "vendor_reply_class": "",
                        "vendor_fault_family": "",
                        "note": "broad site event",
                    }
                )
        for idx in range(4):
            selected_rows.append(
                {
                    "site": "demo",
                    "panel_id": f"concentrated.1.{idx}",
                    "strict_trigger_date": "2025-03-11",
                    "current_actionability_v3": "",
                    "shadow_actionability_v3": "maintenance_candidate_shadow",
                    "strict_method": "confirmed_fault_flag",
                    "shadow_frac": 0.0,
                    "group_off_frac": 0.0,
                    "recovery_reset": "no",
                    "days_earlier_than_trigger": 2,
                    "onset_confidence": "high",
                    "onset_method": "strict_trigger_fallback",
                    "mid_ratio": 0.0,
                    "mid_v_ratio": 1.12,
                    "mid_i_ratio": 0.0,
                    "v_drop": -0.12,
                    "coverage_mid": 1.0,
                    "strict_day_group_like_flag": True,
                    "same_group_zero_like_count": 4,
                    "same_site_zero_like_count": 5,
                    "vendor_reply_class": "field_confirmed_positive" if idx == 0 else "",
                    "vendor_fault_family": "group_or_inverter_side_like" if idx == 0 else "",
                    "note": "concentrated group event",
                }
            )
        selected_rows.append(
            {
                "site": "demo",
                "panel_id": "singleton.2.0",
                "strict_trigger_date": "2025-03-12",
                "current_actionability_v3": "",
                "shadow_actionability_v3": "maintenance_candidate_shadow",
                "strict_method": "confirmed_fault_flag",
                "shadow_frac": 0.0,
                "group_off_frac": 0.0,
                "recovery_reset": "no",
                "days_earlier_than_trigger": 40,
                "onset_confidence": "high",
                "onset_method": "persistent_5of7",
                "mid_ratio": 0.0,
                "mid_v_ratio": 1.09,
                "mid_i_ratio": 0.0,
                "v_drop": -0.09,
                "coverage_mid": 1.0,
                "strict_day_group_like_flag": True,
                "same_group_zero_like_count": 1,
                "same_site_zero_like_count": 1,
                "vendor_reply_class": "vendor_rejected",
                "vendor_fault_family": "none_visible",
                "note": "singleton event",
            }
        )
        selected_df = pd.DataFrame(selected_rows)
        selected_csv_before = selected_df.to_csv(index=False)
        selected_df.to_csv(share_dir / "maintenance_proxy_shadow_selected_cases_v1.csv", index=False, encoding="utf-8-sig")

        reaudit_rows = []
        for row in selected_rows:
            reaudit_rows.append(
                {
                    "site": row["site"],
                    "panel_id": row["panel_id"],
                    "strict_trigger_date": row["strict_trigger_date"],
                    "candidate_validity": "",
                    "review_priority": "P1" if "concentrated" in row["panel_id"] else "P3",
                }
            )
        reaudit_rows[0]["candidate_validity"] = "group_side"
        reaudit_rows[-1]["candidate_validity"] = "false_positive"
        pd.DataFrame(reaudit_rows).to_csv(share_dir / "panel_date_reaudit_working.csv", index=False, encoding="utf-8-sig")

        vendor_rows = [
            {
                "site": "demo",
                "panel_id": "broadA.0.0",
                "strict_trigger_date": "2025-03-10",
                "vendor_reply_class": "vendor_pattern_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_note": "broad vendor context",
            },
            {
                "site": "demo",
                "panel_id": "concentrated.1.0",
                "strict_trigger_date": "2025-03-11",
                "vendor_reply_class": "field_confirmed_positive",
                "vendor_fault_family": "group_or_inverter_side_like",
                "vendor_note": "concentrated vendor context",
            },
            {
                "site": "demo",
                "panel_id": "singleton.2.0",
                "strict_trigger_date": "2025-03-12",
                "vendor_reply_class": "vendor_rejected",
                "vendor_fault_family": "none_visible",
                "vendor_note": "singleton vendor context",
            },
        ]
        vendor_df = pd.DataFrame(vendor_rows)
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        onset_rows = []
        for row in selected_rows:
            onset_rows.append(
                {
                    "site": row["site"],
                    "panel_id": row["panel_id"],
                    "strict_trigger_date": row["strict_trigger_date"],
                    "days_earlier_than_trigger": row["days_earlier_than_trigger"],
                    "onset_confidence": row["onset_confidence"],
                    "onset_method": row["onset_method"],
                }
            )
        pd.DataFrame(onset_rows).to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        core_rows = []
        for row in selected_rows:
            panel_id = row["panel_id"]
            parts = panel_id.split(".")
            group_key = ".".join(parts[:2])
            core_rows.append(
                {
                    "panel_id": panel_id,
                    "date": row["strict_trigger_date"],
                    "group_key_base": group_key,
                }
            )
        pd.DataFrame(core_rows).to_csv(data_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        run_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(run_res.returncode == 0, f"script failed:\n{run_res.stdout}\n{run_res.stderr}")

        summary_df = pd.read_csv(share_dir / "maintenance_proxy_cluster_audit_summary_v1.csv", encoding="utf-8-sig")
        clusters_df = pd.read_csv(share_dir / "maintenance_proxy_cluster_audit_clusters_v1.csv", encoding="utf-8-sig")
        cases_df = pd.read_csv(share_dir / "maintenance_proxy_cluster_audit_cases_v1.csv", encoding="utf-8-sig")

        assert_true(not summary_df.empty, "summary output is empty")
        assert_true(not clusters_df.empty, "clusters output is empty")
        assert_true(not cases_df.empty, "cases output is empty")
        assert_true(len(cases_df) == len(selected_df), "selected-case universe must be preserved exactly")

        selected_keys = set(selected_df[["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        case_keys = set(cases_df[["site", "panel_id", "strict_trigger_date"]].itertuples(index=False, name=None))
        assert_true(selected_keys == case_keys, "case output keys must match selected-case universe exactly")
        assert_true(len(clusters_df) == 5, f"expected 5 group clusters, got {len(clusters_df)}")

        broad_clusters = clusters_df.loc[clusters_df["strict_trigger_date"].eq("2025-03-10")]
        assert_true((broad_clusters["cluster_interpretation"] == "broad_site_day_cluster").all(), "broad site-day event should classify as broad_site_day_cluster")
        concentrated_cluster = clusters_df.loc[clusters_df["strict_trigger_date"].eq("2025-03-11")].iloc[0]
        assert_true(concentrated_cluster["cluster_interpretation"] == "concentrated_group_cluster", "concentrated cluster should classify as concentrated_group_cluster")
        singleton_cluster = clusters_df.loc[clusters_df["strict_trigger_date"].eq("2025-03-12")].iloc[0]
        assert_true(singleton_cluster["cluster_interpretation"] == "singleton_cluster", "singleton case should classify as singleton_cluster")

        case_group_counts = cases_df.groupby("group_cluster_id").size().to_dict()
        assert_true(max(case_group_counts.values()) == 4, "multiple rows from same site/date/group should collapse into one group cluster row")

        selected_csv_after = (share_dir / "maintenance_proxy_shadow_selected_cases_v1.csv").read_text(encoding="utf-8-sig")
        assert_true(selected_csv_after == selected_csv_before, "official selected-case input must not be modified")

        print("[OK] outputs generate")
        print("[OK] selected-case universe is preserved exactly")
        print("[OK] multiple rows from the same site/date/group collapse into one group cluster row")
        print("[OK] synthetic broad site-day event is classified as broad_site_day_cluster")
        print("[OK] synthetic concentrated group cluster is classified as concentrated_group_cluster")
        print("[OK] synthetic singleton case is classified as singleton_cluster")
        print("[OK] no official prediction outputs are modified")

    safe_res = run([sys.executable, str(existing_safe_smoke)], root)
    assert_true(safe_res.returncode == 0, f"existing safe smoke failed:\n{safe_res.stdout}\n{safe_res.stderr}")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

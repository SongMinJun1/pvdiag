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


def make_window(panel_id: str, strict_date: str, case_kind: str) -> pd.DataFrame:
    strict_dt = pd.Timestamp(strict_date)
    dates = pd.date_range(strict_dt - pd.Timedelta(days=7), strict_dt + pd.Timedelta(days=7), freq="D")
    rows: list[dict[str, object]] = []
    for date_dt in dates:
        base = {
            "date": date_dt.date().isoformat(),
            "panel_id": panel_id,
            "mid_ratio": 0.95,
            "last_ratio": 0.95,
            "mid_v_ratio": 0.95,
            "mid_i_ratio": 0.95,
            "v_drop": 0.10,
            "v_ref_ok": True,
            "coverage_mid": 0.95,
            "shadow_like": False,
            "group_off_like": False,
            "recon_error": 0.01,
            "dtw_dist": 0.10,
        }
        if case_kind == "consensus_electrical":
            if strict_dt - pd.Timedelta(days=7) <= date_dt <= strict_dt + pd.Timedelta(days=2):
                base.update({"mid_ratio": 0.70, "mid_v_ratio": 0.68, "mid_i_ratio": 0.94, "v_drop": 0.36})
            if date_dt == strict_dt:
                base.update({"mid_ratio": 0.60, "mid_v_ratio": 0.78, "mid_i_ratio": 0.82, "v_drop": 0.50})
        elif case_kind == "shape_only":
            base.update({"mid_ratio": 0.92, "mid_v_ratio": 0.90, "mid_i_ratio": 0.93, "v_drop": 0.12})
            if strict_dt - pd.Timedelta(days=4) <= date_dt <= strict_dt:
                base.update({"recon_error": 0.90, "dtw_dist": 0.90})
        elif case_kind == "background":
            base.update({"recon_error": 0.02, "dtw_dist": 0.02})
        else:
            raise ValueError(case_kind)
        rows.append(base)
    return pd.DataFrame(rows)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_critical_phenotype_shadow_v2.py"
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

        onset_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_consensus", "strict_trigger_date": "2025-03-10", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_shape", "strict_trigger_date": "2025-03-10", "reason_summary": "strict_method=critical_fault_flag|demo"},
                {"site": "demo", "panel_id": "p_noncritical", "strict_trigger_date": "2025-03-10", "reason_summary": "strict_method=confirmed_fault_flag|demo"},
            ]
        )
        onset_df.to_csv(share_dir / "panel_onset_shadow_latest.csv", index=False, encoding="utf-8-sig")

        vendor_df = pd.DataFrame(
            [
                {"site": "demo", "panel_id": "p_consensus", "vendor_reply_class": "field_confirmed_positive", "vendor_fault_family": "electrical"},
                {"site": "demo", "panel_id": "p_shape", "vendor_reply_class": "vendor_no_info", "vendor_fault_family": "unknown"},
            ]
        )
        vendor_df.to_csv(share_dir / "vendor_reply_adjudication_latest.csv", index=False, encoding="utf-8-sig")

        core_df = pd.concat(
            [
                make_window("p_consensus", "2025-03-10", "consensus_electrical"),
                make_window("p_shape", "2025-03-10", "shape_only"),
                make_window("p_background_a", "2025-03-10", "background"),
                make_window("p_background_b", "2025-03-10", "background"),
                make_window("p_noncritical", "2025-03-10", "background"),
            ],
            ignore_index=True,
        )
        core_df.to_csv(out_dir / "panel_day_core.csv", index=False, encoding="utf-8-sig")

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root), "--sites", "demo"], root)
        assert_true(build_res.returncode == 0, f"critical phenotype v2 build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest = pd.read_csv(share_dir / "critical_phenotype_shadow_v2_latest.csv", low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(share_dir / "critical_phenotype_shadow_v2_summary.csv", low_memory=False, encoding="utf-8-sig")

        assert_true(len(latest) == 2, "no new candidates should be created and noncritical rows should be excluded")
        by_panel = latest.set_index("panel_id")

        assert_true(by_panel.loc["p_consensus", "critical_phenotype_v2"] == "electrical_fault_like", "window consensus should classify strong electrical case")
        assert_true(by_panel.loc["p_shape", "critical_phenotype_v2"] == "shape_only_monitor", "shape-only case should be monitor, not maintenance phenotype")
        assert_true(int(by_panel.loc["p_shape", "shape_support_flag"]) == 1, "shape-only case should have shape support flag")
        assert_true(int(by_panel.loc["p_consensus", "cluster_guard_flag"]) in {0, 1}, "cluster guard flag must be emitted")
        assert_true(int(by_panel.loc["p_consensus", "evidence_days"]) >= 4, "consensus electrical case should have evidence days")
        assert_true(int(summary.iloc[0]["count_electrical_fault_like"]) == 1, "summary electrical count mismatch")
        assert_true(int(summary.iloc[0]["count_shape_only_monitor"]) == 1, "summary shape-only count mismatch")

    smoke_vendor_res = run([sys.executable, str(smoke_vendor)], root)
    assert_true(smoke_vendor_res.returncode == 0, f"vendor smoke failed:\n{smoke_vendor_res.stdout}\n{smoke_vendor_res.stderr}")
    smoke_field_res = run([sys.executable, str(smoke_field)], root)
    assert_true(smoke_field_res.returncode == 0, f"field truth smoke failed:\n{smoke_field_res.stdout}\n{smoke_field_res.stderr}")

    print("[OK] scripts compile")
    print("[OK] no new candidates are created")
    print("[OK] a synthetic anchor-miss case is corrected by window consensus")
    print("[OK] synthetic shape-only case is classified as shape_only_monitor")
    print("[OK] synthetic strong electrical case is classified as electrical_fault_like")
    print("[OK] existing smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

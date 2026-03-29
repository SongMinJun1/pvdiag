#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "common_cause_incident_gate_audit_summary_v1.csv",
    "common_cause_incident_gate_days_v1.csv",
    "common_cause_incident_gate_comparison_v1.csv",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def make_matrix_row(
    site: str,
    panel_id: str,
    date: str,
    group_proxy_value: str,
    coverage_ok_flag: int = 1,
    mid_ratio: float = 0.05,
    mid_v_ratio: float = 1.10,
    mid_i_ratio: float = 0.05,
) -> dict[str, object]:
    return {
        "site": site,
        "panel_id": panel_id,
        "date": date,
        "coverage_mid": 1.0,
        "coverage_ok_flag": coverage_ok_flag,
        "mid_ratio": mid_ratio,
        "last_ratio": mid_ratio,
        "mid_v_ratio": mid_v_ratio,
        "mid_i_ratio": mid_i_ratio,
        "v_drop": 0.0,
        "shadow_like_flag": 0,
        "group_off_like_flag": 0,
        "shape_flag": "",
        "shape_score": "",
        "instability_flag": "",
        "instability_score": "",
        "electrical_like_flag": 0,
        "open_device_like_flag": 0,
        "local_signal_signature": "",
        "evidence_reason_code": "",
        "group_proxy_value": group_proxy_value,
        "group_proxy_source": "group_key_base",
        "topology_confidence": "high",
    }


def build_fixture_root(tmp_root: Path) -> None:
    rows: list[dict[str, object]] = []

    # schema_default fails on group share, while relaxed/precursor tiers pass.
    for group_proxy in ["cg1", "cg2", "cg3"]:
        rows.append(make_matrix_row("conalog", f"{group_proxy}.a", "2025-01-01", group_proxy))
        rows.append(make_matrix_row("conalog", f"{group_proxy}.b", "2025-01-01", group_proxy))
        for suffix in ["c", "d", "e", "f"]:
            rows.append(
                make_matrix_row(
                    "conalog",
                    f"{group_proxy}.{suffix}",
                    "2025-01-01",
                    group_proxy,
                    mid_ratio=0.80,
                    mid_v_ratio=0.80,
                    mid_i_ratio=0.80,
                )
            )

    # explicit no-signal day
    rows.append(make_matrix_row("gangui", "g1", "2025-02-01", "gg1", mid_ratio=0.80, mid_v_ratio=0.80, mid_i_ratio=0.80))
    rows.append(make_matrix_row("ktc_ess", "k1", "2025-03-01", "kg1", mid_ratio=0.80, mid_v_ratio=0.80, mid_i_ratio=0.80))
    rows.append(make_matrix_row("sinhyo", "s1", "2025-04-01", "sg1", mid_ratio=0.80, mid_v_ratio=0.80, mid_i_ratio=0.80))

    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(share_dir / "panel_day_evidence_matrix_v1.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(
        [
            {"tier_id": "broad_3g_10p", "site": "conalog", "date": "2025-01-01"},
            {"tier_id": "medium_2g_5p", "site": "conalog", "date": "2025-01-01"},
        ]
    ).to_csv(share_dir / "common_cause_precursor_candidate_days_v1.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_common_cause_incident_gate_audit_v1.py"
    safe_smoke = root / "research" / "prognostics" / "smoke_test_common_cause_incident_registry_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        for output_name in OUTPUT_NAMES:
            assert_true(output_name in produced_output_names, f"{output_name} should be generated")

        summary_df = pd.read_csv(share_dir / "common_cause_incident_gate_audit_summary_v1.csv", encoding="utf-8-sig")
        days_df = pd.read_csv(share_dir / "common_cause_incident_gate_days_v1.csv", encoding="utf-8-sig")
        comparison_df = pd.read_csv(share_dir / "common_cause_incident_gate_comparison_v1.csv", encoding="utf-8-sig")

        schema_row = comparison_df.loc[
            comparison_df["tier_id"].astype(str).eq("schema_default")
            & comparison_df["site"].astype(str).eq("conalog")
            & comparison_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        assert_true(int(schema_row["pass_flag"]) == 0, "schema_default should fail on the synthetic strict-share case")
        assert_true(
            schema_row["fail_reason_code"] == "insufficient_group_share",
            "fail_reason_code should report insufficient_group_share for the strict-share failure",
        )

        relaxed_row = comparison_df.loc[
            comparison_df["tier_id"].astype(str).eq("relaxed_group_share")
            & comparison_df["site"].astype(str).eq("conalog")
            & comparison_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        medium_row = comparison_df.loc[
            comparison_df["tier_id"].astype(str).eq("precursor_like_medium")
            & comparison_df["site"].astype(str).eq("conalog")
            & comparison_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        broad_row = comparison_df.loc[
            comparison_df["tier_id"].astype(str).eq("precursor_like_broad")
            & comparison_df["site"].astype(str).eq("conalog")
            & comparison_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        assert_true(int(relaxed_row["pass_flag"]) == 1, "relaxed_group_share should pass on the synthetic case")
        assert_true(int(medium_row["pass_flag"]) == 1, "precursor_like_medium should pass on the synthetic case")
        assert_true(int(broad_row["pass_flag"]) == 1, "precursor_like_broad should pass on the synthetic case")
        assert_true(
            int(schema_row["precursor_candidate_flag"]) == 1 and "broad_3g_10p" in str(schema_row["precursor_tier_ids_seen"]),
            "precursor overlap context should join when available",
        )

        no_signal_row = comparison_df.loc[
            comparison_df["tier_id"].astype(str).eq("schema_default")
            & comparison_df["site"].astype(str).eq("gangui")
            & comparison_df["date"].astype(str).eq("2025-02-01")
        ].iloc[0]
        assert_true(
            no_signal_row["fail_reason_code"] == "no_signal",
            "fail_reason_code should report no_signal when no grouped signal exists",
        )

        day_row = days_df.loc[
            days_df["site"].astype(str).eq("conalog") & days_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        assert_true(int(day_row["schema_default_pass_flag"]) == 0, "gate days output should carry schema_default pass flag")
        assert_true(int(day_row["precursor_like_medium_pass_flag"]) == 1, "gate days output should carry precursor_like_medium pass flag")

        summary_row = summary_df.loc[
            summary_df["record_type"].astype(str).eq("summary") & summary_df["tier_id"].astype(str).eq("schema_default")
        ].iloc[0]
        assert_true(int(summary_row["fail_insufficient_group_share_count"]) >= 1, "summary should count insufficient_group_share failures")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] schema_default can fail while precursor_like tiers pass on a synthetic case")
    print("[OK] fail_reason_code is populated correctly")
    print("[OK] precursor overlap context is joined when available")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

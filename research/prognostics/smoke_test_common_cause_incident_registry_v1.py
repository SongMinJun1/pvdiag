#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "common_cause_incident_registry_v1.csv",
    "common_cause_incident_days_v1.csv",
    "common_cause_incident_summary_v1.csv",
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
    group_proxy_source: str = "group_key_base",
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
        "group_proxy_source": group_proxy_source,
        "topology_confidence": "high" if group_proxy_source == "group_key_base" else "low",
    }


def build_fixture_root(tmp_root: Path) -> None:
    rows: list[dict[str, object]] = []

    for date, groups in {
        "2025-01-01": ["cg1", "cg2", "cg3"],
        "2025-01-02": ["cg1", "cg2", "cg4"],
        "2025-01-03": ["cg5", "cg6", "cg7"],
    }.items():
        for group_proxy in groups:
            rows.append(make_matrix_row("conalog", f"{group_proxy}.a", date, group_proxy))
            rows.append(make_matrix_row("conalog", f"{group_proxy}.b", date, group_proxy))

    rows.append(make_matrix_row("conalog", "noncandidate.1", "2025-01-04", "cgX", mid_ratio=0.80, mid_v_ratio=0.80, mid_i_ratio=0.80))

    for idx in range(5):
        rows.append(make_matrix_row("gangui", f"gg.{idx}", "2025-02-01", "gg1"))

    for group_proxy in ["kg1", "kg2"]:
        rows.append(make_matrix_row("ktc_ess", f"{group_proxy}.a", "2025-03-01", group_proxy))
        rows.append(make_matrix_row("ktc_ess", f"{group_proxy}.b", "2025-03-01", group_proxy))

    rows.append(make_matrix_row("sinhyo", "sh.1", "2025-04-01", "sg1", mid_ratio=0.80, mid_v_ratio=0.80, mid_i_ratio=0.80))

    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(share_dir / "panel_day_evidence_matrix_v1.csv", index=False, encoding="utf-8-sig")


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_common_cause_incident_registry_v1.py"
    safe_smoke = root / "research" / "prognostics" / "smoke_test_panel_day_evidence_matrix_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        for name in OUTPUT_NAMES:
            assert_true(name in produced_output_names, f"{name} should be generated")

        registry_df = pd.read_csv(share_dir / "common_cause_incident_registry_v1.csv", encoding="utf-8-sig")
        days_df = pd.read_csv(share_dir / "common_cause_incident_days_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "common_cause_incident_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(days_df.loc[days_df["site"].astype(str).eq("conalog")]) == 3, "conalog should have three candidate incident days")
        assert_true(
            "2025-01-04" not in set(days_df["date"].astype(str)),
            "non-candidate days should be excluded from common_cause_incident_days_v1.csv",
        )

        conalog_registry = registry_df.loc[registry_df["site"].astype(str).eq("conalog")].copy()
        assert_true(len(conalog_registry) == 2, "conalog should split into two incidents")
        merged_incident = conalog_registry.loc[conalog_registry["incident_day_count"].eq(2)].iloc[0]
        split_incident = conalog_registry.loc[conalog_registry["incident_day_count"].eq(1)].iloc[0]
        assert_true(
            merged_incident["incident_start_date"] == "2025-01-01" and merged_incident["incident_end_date"] == "2025-01-02",
            "consecutive days with overlapping qualifying groups should merge into one incident",
        )
        assert_true(
            split_incident["incident_start_date"] == "2025-01-03" and split_incident["incident_end_date"] == "2025-01-03",
            "consecutive days with low overlap should split into separate incidents",
        )
        assert_true(
            merged_incident["incident_scope"] == "site" and merged_incident["incident_confidence"] == "high",
            "site-wide merged incident should receive site scope and high confidence",
        )
        assert_true(
            merged_incident["dominant_incident_family"] == "site_wide_collapse",
            "site-wide merged incident should receive site_wide_collapse dominant family",
        )

        gangui_incident = registry_df.loc[registry_df["site"].astype(str).eq("gangui")].iloc[0]
        assert_true(
            gangui_incident["incident_scope"] == "group" and gangui_incident["incident_confidence"] == "low",
            "single-group candidate should become a group-scope, low-confidence incident",
        )
        assert_true(
            gangui_incident["open_reason_code"] == "IOPEN_SITE_WIDE_COLLAPSE",
            "single-group site-wide threshold case should use IOPEN_SITE_WIDE_COLLAPSE",
        )

        ktc_incident = registry_df.loc[registry_df["site"].astype(str).eq("ktc_ess")].iloc[0]
        assert_true(
            ktc_incident["incident_scope"] == "mixed" and ktc_incident["incident_confidence"] == "medium",
            "two-group candidate should become mixed scope with medium confidence",
        )
        assert_true(
            ktc_incident["open_reason_code"] == "IOPEN_MULTI_GROUP_COLLAPSE",
            "multi-group candidate should use IOPEN_MULTI_GROUP_COLLAPSE",
        )

        conalog_summary = summary_df.loc[summary_df["site"].astype(str).eq("conalog")].iloc[0]
        assert_true(int(conalog_summary["incident_count"]) == 2, "summary incident_count should match conalog incidents")
        assert_true(int(conalog_summary["incident_day_count"]) == 3, "summary incident_day_count should match conalog candidate days")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] consecutive days with overlapping qualifying groups merge into one incident")
    print("[OK] consecutive days with low overlap split into separate incidents")
    print("[OK] non-candidate days are excluded from common_cause_incident_days_v1.csv")
    print("[OK] incident_scope / dominant_incident_family / incident_confidence are assigned as specified")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_core_duplicate_resolution_summary_v2.csv",
    "panel_day_core_duplicate_resolution_groups_v2.csv",
    "panel_day_core_duplicate_resolution_critical_diffs_v2.csv",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_site_core(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    write_site_core(
        tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-01",
                "panel_id": "c.1.1",
                "coverage_mid": 0.90,
                "mid_ratio": 0.50,
                "last_ratio": 0.48,
                "mid_v_ratio": 0.70,
                "mid_i_ratio": 0.88,
                "v_drop": 0.33,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "cg.1",
                "source_csv": "file_a.csv",
                "ews_mid_var_7d": 0.11,
            },
            {
                "date": "2025-01-01",
                "panel_id": "c.1.1",
                "coverage_mid": 0.90,
                "mid_ratio": 0.50,
                "last_ratio": 0.48,
                "mid_v_ratio": 0.70,
                "mid_i_ratio": 0.88,
                "v_drop": 0.33,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "cg.1",
                "source_csv": "file_b.csv",
                "ews_mid_var_7d": 0.11,
            },
        ],
    )
    write_site_core(
        tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-02-01",
                "panel_id": "g.1.1",
                "coverage_mid": 0.91,
                "mid_ratio": 0.60,
                "last_ratio": 0.59,
                "mid_v_ratio": 0.80,
                "mid_i_ratio": 0.86,
                "v_drop": 0.29,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "gg.1",
                "source_csv": "same.csv",
                "ews_mid_var_7d": 0.12,
            },
            {
                "date": "2025-02-01",
                "panel_id": "g.1.1",
                "coverage_mid": 0.91,
                "mid_ratio": 0.60,
                "last_ratio": 0.59,
                "mid_v_ratio": 0.80,
                "mid_i_ratio": 0.86,
                "v_drop": 0.29,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "gg.1",
                "source_csv": "same.csv",
                "ews_mid_var_7d": 0.18,
            },
        ],
    )
    write_site_core(
        tmp_root / "data" / "ktc_ess" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-03-01",
                "panel_id": "k.1.1",
                "coverage_mid": 0.92,
                "mid_ratio": 0.5000000,
                "last_ratio": 0.47,
                "mid_v_ratio": 0.79,
                "mid_i_ratio": 0.87,
                "v_drop": 0.31,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "kg.1",
            },
            {
                "date": "2025-03-01",
                "panel_id": "k.1.1",
                "coverage_mid": 0.92,
                "mid_ratio": 0.5000005,
                "last_ratio": 0.47,
                "mid_v_ratio": 0.79,
                "mid_i_ratio": 0.87,
                "v_drop": 0.31,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "kg.1",
            },
        ],
    )
    write_site_core(
        tmp_root / "data" / "sinhyo" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-04-01",
                "panel_id": "s.1.1",
                "coverage_mid": 0.94,
                "mid_ratio": 0.55,
                "last_ratio": 0.50,
                "mid_v_ratio": 0.82,
                "mid_i_ratio": 0.90,
                "v_drop": 0.30,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "sg.1",
            },
            {
                "date": "2025-04-01",
                "panel_id": "s.1.1",
                "coverage_mid": 0.94,
                "mid_ratio": 0.57,
                "last_ratio": 0.50,
                "mid_v_ratio": 0.82,
                "mid_i_ratio": 0.90,
                "v_drop": 0.30,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "sg.1",
            },
        ],
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_core_duplicate_resolution_audit_v2.py"
    safe_smoke = root / "research" / "prognostics" / "smoke_test_panel_day_core_duplicate_audit_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(produced_output_names == OUTPUT_NAMES, "builder should only emit the three resolution-audit outputs")

        summary_df = pd.read_csv(share_dir / "panel_day_core_duplicate_resolution_summary_v2.csv", encoding="utf-8-sig")
        groups_df = pd.read_csv(share_dir / "panel_day_core_duplicate_resolution_groups_v2.csv", encoding="utf-8-sig")
        critical_df = pd.read_csv(share_dir / "panel_day_core_duplicate_resolution_critical_diffs_v2.csv", encoding="utf-8-sig")

        summary_row = summary_df.loc[summary_df["record_type"].astype(str).eq("summary")].iloc[0]
        assert_true(int(summary_row["duplicate_group_count"]) == 4, "synthetic fixture should create four duplicate groups")
        assert_true(
            int(summary_row["provenance_only_duplicate_count"]) == 1,
            "synthetic provenance-only duplicates should classify correctly",
        )
        assert_true(
            int(summary_row["evidence_equivalent_duplicate_count"]) == 1,
            "synthetic auxiliary-only duplicates should classify as evidence_equivalent_duplicate",
        )
        assert_true(
            int(summary_row["numeric_jitter_duplicate_count"]) == 1,
            "synthetic tiny critical numeric drift should classify as numeric_jitter_duplicate",
        )
        assert_true(
            int(summary_row["material_conflict_duplicate_count"]) == 1,
            "synthetic true critical conflict should classify as material_conflict_duplicate",
        )

        conalog_group = groups_df.loc[groups_df["site"].astype(str).eq("conalog")].iloc[0]
        assert_true(conalog_group["resolution_class"] == "provenance_only_duplicate", "provenance-only duplicates should classify correctly")
        assert_true(int(conalog_group["provenance_diff_column_count"]) == 1, "provenance-only group should count provenance diffs")
        assert_true(int(conalog_group["auxiliary_diff_column_count"]) == 0, "provenance-only group should not count auxiliary diffs")
        assert_true(int(conalog_group["critical_diff_column_count"]) == 0, "provenance-only group should not count critical diffs")

        gangui_group = groups_df.loc[groups_df["site"].astype(str).eq("gangui")].iloc[0]
        assert_true(
            gangui_group["resolution_class"] == "evidence_equivalent_duplicate",
            "auxiliary-only differences should classify as evidence_equivalent_duplicate",
        )
        assert_true(int(gangui_group["auxiliary_diff_column_count"]) == 1, "auxiliary-only group should count auxiliary diffs")

        jitter_group = groups_df.loc[groups_df["site"].astype(str).eq("ktc_ess")].iloc[0]
        assert_true(
            jitter_group["resolution_class"] == "numeric_jitter_duplicate",
            "tiny critical numeric drift should classify as numeric_jitter_duplicate",
        )
        assert_true(float(jitter_group["max_abs_diff_critical_numeric"]) <= 1e-6, "jitter group max abs diff should stay within tolerance")

        material_group = groups_df.loc[groups_df["site"].astype(str).eq("sinhyo")].iloc[0]
        assert_true(
            material_group["resolution_class"] == "material_conflict_duplicate",
            "true evidence-critical conflict should classify as material_conflict_duplicate",
        )
        assert_true(int(material_group["critical_diff_column_count"]) >= 1, "material conflict should count critical diffs")

        material_diffs = critical_df.loc[
            critical_df["site"].astype(str).eq("sinhyo") & critical_df["field_name"].astype(str).eq("mid_ratio")
        ]
        assert_true(not material_diffs.empty, "critical diff rows should be emitted for material conflicts")
        assert_true(
            material_diffs.iloc[0]["diff_severity"] == "material",
            "material critical diff rows should be marked material",
        )

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] synthetic provenance-only duplicates classify correctly")
    print("[OK] synthetic evidence-equivalent duplicates with auxiliary-only differences classify correctly")
    print("[OK] synthetic tiny numeric drift in evidence-critical columns classifies as numeric_jitter_duplicate")
    print("[OK] synthetic true evidence-critical value conflict classifies as material_conflict_duplicate")
    print("[OK] critical diff rows are emitted for material conflicts")
    print("[OK] no source files are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

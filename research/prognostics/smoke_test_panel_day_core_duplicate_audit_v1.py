#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_core_duplicate_audit_summary_v1.csv",
    "panel_day_core_duplicate_groups_v1.csv",
    "panel_day_core_duplicate_rows_v1.csv",
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
                "panel_id": "p.1.1",
                "mid_ratio": "1.0",
                "shadow_like": 0,
                "note": " exact sample ",
            },
            {
                "date": "2025-01-01",
                "panel_id": "p.1.1",
                "mid_ratio": 1,
                "shadow_like": 0,
                "note": "exact sample",
            },
            {
                "date": "2025-01-02",
                "panel_id": "p.2.2",
                "mid_ratio": 0.5,
                "shadow_like": 0,
                "note": "",
            },
        ],
    )
    write_site_core(
        tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-02-01",
                "panel_id": "g.1.1",
                "mid_ratio": 0.50,
                "shadow_like": 0,
                "note": "first",
            },
            {
                "date": "2025-02-01",
                "panel_id": "g.1.1",
                "mid_ratio": 0.70,
                "shadow_like": 1,
                "note": "first",
            },
        ],
    )
    write_site_core(
        tmp_root / "data" / "ktc_ess" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-03-01",
                "panel_id": "k.1.1",
                "mid_ratio": 0.80,
                "shadow_like": 0,
            }
        ],
    )
    write_site_core(
        tmp_root / "data" / "sinhyo" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-04-01",
                "panel_id": "s.1.1",
                "mid_ratio": 0.90,
                "shadow_like": 0,
            }
        ],
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_core_duplicate_audit_v1.py"
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
        assert_true(produced_output_names == OUTPUT_NAMES, "builder should only emit the three duplicate-audit outputs")

        summary_df = pd.read_csv(share_dir / "panel_day_core_duplicate_audit_summary_v1.csv", encoding="utf-8-sig")
        groups_df = pd.read_csv(share_dir / "panel_day_core_duplicate_groups_v1.csv", encoding="utf-8-sig")
        rows_df = pd.read_csv(share_dir / "panel_day_core_duplicate_rows_v1.csv", encoding="utf-8-sig")

        summary_row = summary_df.loc[summary_df["record_type"].astype(str).eq("summary")].iloc[0]
        assert_true(int(summary_row["total_row_count"]) == 7, "total_row_count should match synthetic input")
        assert_true(int(summary_row["duplicate_group_count"]) == 2, "duplicate_group_count should match the two synthetic duplicate groups")
        assert_true(int(summary_row["duplicate_row_count"]) == 4, "duplicate_row_count should count all raw duplicated rows")

        exact_group = groups_df.loc[
            groups_df["site"].astype(str).eq("conalog")
            & groups_df["panel_id"].astype(str).eq("p.1.1")
            & groups_df["date"].astype(str).eq("2025-01-01")
        ].iloc[0]
        assert_true(
            exact_group["duplicate_group_type"] == "exact_duplicate_group",
            "synthetic exact duplicates should be classified as exact_duplicate_group",
        )
        assert_true(
            exact_group["recommended_handling"] == "safe_dedupe_candidate",
            "exact duplicate group should be marked as safe_dedupe_candidate",
        )

        conflicting_group = groups_df.loc[
            groups_df["site"].astype(str).eq("gangui")
            & groups_df["panel_id"].astype(str).eq("g.1.1")
            & groups_df["date"].astype(str).eq("2025-02-01")
        ].iloc[0]
        assert_true(
            conflicting_group["duplicate_group_type"] == "conflicting_duplicate_group",
            "synthetic conflicting duplicates should be classified as conflicting_duplicate_group",
        )
        assert_true(
            int(conflicting_group["differing_column_count"]) >= 1,
            "conflicting duplicate groups should report differing columns",
        )
        differing_columns = str(conflicting_group["differing_columns"])
        assert_true(
            "mid_ratio" in differing_columns and "shadow_like" in differing_columns,
            "differing_columns should be populated for conflicting groups",
        )

        assert_true(len(rows_df) == 4, "row-level output should preserve one row per raw duplicated row")
        conalog_rows = rows_df.loc[rows_df["site"].astype(str).eq("conalog")]
        assert_true(len(conalog_rows) == 2, "exact duplicate rows should both be preserved in row-level output")

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] synthetic exact duplicates are classified as exact_duplicate_group")
    print("[OK] synthetic conflicting duplicates are classified as conflicting_duplicate_group")
    print("[OK] differing_columns is populated for conflicting groups")
    print("[OK] no source files are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

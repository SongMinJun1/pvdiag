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


def normalize_token(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        as_float = float(text)
    except ValueError:
        return text
    if as_float.is_integer():
        return str(int(as_float))
    return text


def write_csv(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(root: Path) -> None:
    rows = {
        "conalog": (
            "site,panel_id,date\n"
            "conalog,11111111-1111-1111-1111-111111111111.0.0,2026-02-18\n"
            "conalog,11111111-1111-1111-1111-111111111111.0.1,2026-02-18\n"
            "conalog,bad-panel-id,2026-02-18\n"
        ),
        "gangui": (
            "site,panel_id,date\n"
            "gangui,22222222-2222-2222-2222-222222222222.1.0,2026-02-19\n"
            "gangui,22222222-2222-2222-2222-222222222222.1.2,2026-02-19\n"
        ),
        "ktc_ess": (
            "site,panel_id,date\n"
            "ktc_ess,33333333-3333-3333-3333-333333333333.2.5,2026-02-19\n"
        ),
        "sinhyo": (
            "site,panel_id,date\n"
            "sinhyo,33333333-3333-3333-3333-333333333333.2.5,2026-02-19\n"
        ),
    }
    for site, text in rows.items():
        write_csv(root / "data" / site / "out" / "latest_panel_status.csv", text)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_id_hypothesis.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], repo_root)
    assert_true(compile_res.returncode == 0, f"py_compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory(prefix="panel_id_hypothesis_smoke_") as tmpdir:
        root = Path(tmpdir)
        build_fixture(root)

        build_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest_path = root / "_share" / "site_panel_id_hypothesis_latest.csv"
        summary_path = root / "_share" / "site_panel_id_hypothesis_summary.csv"
        group_stats_path = root / "_share" / "site_panel_id_group_stats.csv"

        assert_true(latest_path.exists(), "site_panel_id_hypothesis_latest.csv was not generated")
        assert_true(summary_path.exists(), "site_panel_id_hypothesis_summary.csv was not generated")
        assert_true(group_stats_path.exists(), "site_panel_id_group_stats.csv was not generated")

        latest = pd.read_csv(latest_path, low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        group_stats = pd.read_csv(group_stats_path, low_memory=False, encoding="utf-8-sig")

        expected_latest_cols = {
            "site",
            "panel_id",
            "token0_uuid",
            "token1_group",
            "token2_index",
            "token2_index_int",
            "panel_id_pattern_valid",
            "parse_note",
        }
        expected_summary_cols = {
            "site",
            "repo_panel_count",
            "valid_pattern_count",
            "pattern_valid_rate",
            "token0_unique_count",
            "token1_unique_count",
            "token2_min",
            "token2_max",
            "token2_unique_count",
        }
        expected_group_cols = {
            "site",
            "token0_uuid",
            "token1_group",
            "panel_count",
            "token2_min",
            "token2_max",
            "token2_unique_count",
            "token2_contiguous_flag",
        }
        assert_true(expected_latest_cols <= set(latest.columns), "latest hypothesis columns are missing")
        assert_true(expected_summary_cols <= set(summary.columns), "summary hypothesis columns are missing")
        assert_true(expected_group_cols <= set(group_stats.columns), "group stats columns are missing")

        valid_row = latest.loc[latest["panel_id"].astype(str).eq("11111111-1111-1111-1111-111111111111.0.1")].iloc[0]
        assert_true(int(valid_row["panel_id_pattern_valid"]) == 1, "valid panel_id should parse successfully")
        assert_true(normalize_token(valid_row["token1_group"]) == "0", "token1_group parse mismatch")
        assert_true(normalize_token(valid_row["token2_index_int"]) == "1", "token2_index_int parse mismatch")

        malformed_row = latest.loc[latest["panel_id"].astype(str).eq("bad-panel-id")].iloc[0]
        assert_true(int(malformed_row["panel_id_pattern_valid"]) == 0, "malformed panel_id should be flagged")
        assert_true(str(malformed_row["parse_note"]) == "wrong_segment_count", "malformed panel_id parse_note mismatch")

        repeated_rows = latest.loc[latest["panel_id"].astype(str).eq("33333333-3333-3333-3333-333333333333.2.5")]
        assert_true(len(repeated_rows) == 2, "cross-site repeated panel fixture mismatch")
        assert_true(
            repeated_rows["repeated_panel_id_across_sites_flag"].fillna(0).astype(int).eq(1).all(),
            "cross-site repeated panel_id should be flagged",
        )

        conalog_summary = summary.loc[summary["site"].astype(str).eq("conalog")].iloc[0]
        assert_true(int(conalog_summary["repo_panel_count"]) == 3, "repo_panel_count mismatch")
        assert_true(round(float(conalog_summary["pattern_valid_rate"]), 6) == round(2.0 / 3.0, 6), "valid rate mismatch")

        contiguous_row = group_stats.loc[
            group_stats["site"].astype(str).eq("conalog")
            & group_stats["token0_uuid"].astype(str).eq("11111111-1111-1111-1111-111111111111")
            & group_stats["token1_group"].astype(str).eq("0")
        ].iloc[0]
        assert_true(int(contiguous_row["token2_contiguous_flag"]) == 1, "contiguous token2 group should be flagged as contiguous")

        noncontiguous_row = group_stats.loc[
            group_stats["site"].astype(str).eq("gangui")
            & group_stats["token0_uuid"].astype(str).eq("22222222-2222-2222-2222-222222222222")
            & group_stats["token1_group"].astype(str).eq("1")
        ].iloc[0]
        assert_true(int(noncontiguous_row["token2_contiguous_flag"]) == 0, "non-contiguous token2 group should be flagged")

    print("[OK] panel_id hypothesis scripts compile")
    print("[OK] outputs generate")
    print("[OK] parsing works on synthetic panel_id fixture")
    print("[OK] malformed ids are detected")
    print("[OK] contiguous and non-contiguous token2 groups are distinguished")


if __name__ == "__main__":
    main()

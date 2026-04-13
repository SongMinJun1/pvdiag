#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


EXPECTED_SITE_FILES = {"conalog.csv", "gangui.csv", "ktc_ess.csv", "sinhyo.csv"}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


def build_raw_fixture_root(tmp_root: Path) -> None:
    write_csv(
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
                "ews_mid_var_7d": 0.18,
            },
            {
                "date": "2025-01-02",
                "panel_id": "c.2.2",
                "coverage_mid": 0.95,
                "mid_ratio": 0.05,
                "last_ratio": 0.02,
                "mid_v_ratio": 0.05,
                "mid_i_ratio": 0.50,
                "v_drop": 0.95,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "",
                "source_csv": "file_c.csv",
                "ews_mid_var_7d": 0.10,
            },
        ],
    )
    write_csv(
        tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-03",
                "panel_id": "g.1.1",
                "coverage_mid": 0.92,
                "mid_ratio": 0.92,
                "last_ratio": 0.93,
                "mid_v_ratio": 0.97,
                "mid_i_ratio": 0.91,
                "v_drop": 0.08,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "gang.grp",
                "shape_flag": 1,
                "shape_score": 0.70,
            }
        ],
    )
    write_csv(
        tmp_root / "data" / "ktc_ess" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-04",
                "panel_id": "k.1.1",
                "coverage_mid": 0.80,
                "mid_ratio": 0.45,
                "last_ratio": 0.42,
                "mid_v_ratio": 0.95,
                "mid_i_ratio": 0.40,
                "v_drop": 0.12,
                "shadow_like": 0,
                "group_off_like": 0,
            }
        ],
    )
    write_csv(
        tmp_root / "data" / "sinhyo" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-05",
                "panel_id": "s.1.1",
                "coverage_mid": 0.88,
                "mid_ratio": 0.07,
                "last_ratio": 0.06,
                "mid_v_ratio": 0.96,
                "mid_i_ratio": 0.08,
                "v_drop": 0.05,
                "shadow_like": 0,
                "group_off_like": 1,
                "group_key_base": "sinhyo.g1",
            }
        ],
    )


def write_duplicate_resolution_outputs(tmp_root: Path, resolution_class: str) -> None:
    share_dir = tmp_root / "_share"
    share_dir.mkdir(parents=True, exist_ok=True)
    safe_count = 1 if resolution_class in {"provenance_only_duplicate", "evidence_equivalent_duplicate"} else 0
    jitter_count = 1 if resolution_class == "numeric_jitter_duplicate" else 0
    material_count = 1 if resolution_class == "material_conflict_duplicate" else 0
    summary_rows = [
        {
            "record_type": "summary",
            "site": "",
            "total_row_count": 6,
            "row_count": "",
            "duplicate_group_count": 1,
            "duplicate_row_count": 2,
            "provenance_only_duplicate_count": 1 if resolution_class == "provenance_only_duplicate" else 0,
            "evidence_equivalent_duplicate_count": 1 if resolution_class == "evidence_equivalent_duplicate" else 0,
            "numeric_jitter_duplicate_count": jitter_count,
            "material_conflict_duplicate_count": material_count,
        },
        {
            "record_type": "site",
            "site": "conalog",
            "total_row_count": "",
            "row_count": 3,
            "duplicate_group_count": 1,
            "duplicate_row_count": 2,
            "provenance_only_duplicate_count": 1 if resolution_class == "provenance_only_duplicate" else 0,
            "evidence_equivalent_duplicate_count": 1 if resolution_class == "evidence_equivalent_duplicate" else 0,
            "numeric_jitter_duplicate_count": jitter_count,
            "material_conflict_duplicate_count": material_count,
        },
        {"record_type": "site", "site": "gangui", "total_row_count": "", "row_count": 1, "duplicate_group_count": 0, "duplicate_row_count": 0, "provenance_only_duplicate_count": 0, "evidence_equivalent_duplicate_count": 0, "numeric_jitter_duplicate_count": 0, "material_conflict_duplicate_count": 0},
        {"record_type": "site", "site": "ktc_ess", "total_row_count": "", "row_count": 1, "duplicate_group_count": 0, "duplicate_row_count": 0, "provenance_only_duplicate_count": 0, "evidence_equivalent_duplicate_count": 0, "numeric_jitter_duplicate_count": 0, "material_conflict_duplicate_count": 0},
        {"record_type": "site", "site": "sinhyo", "total_row_count": "", "row_count": 1, "duplicate_group_count": 0, "duplicate_row_count": 0, "provenance_only_duplicate_count": 0, "evidence_equivalent_duplicate_count": 0, "numeric_jitter_duplicate_count": 0, "material_conflict_duplicate_count": 0},
    ]
    groups_rows = [
        {
            "duplicate_group_index": 1,
            "site": "conalog",
            "panel_id": "c.1.1",
            "date": "2025-01-01",
            "duplicate_row_count": 2,
            "provenance_diff_column_count": 1,
            "auxiliary_diff_column_count": 1,
            "critical_diff_column_count": 0,
            "max_abs_diff_critical_numeric": 0.0,
            "differing_critical_columns": "",
            "resolution_class": resolution_class,
            "recommended_handling": "safe_keep_one_after_equivalence_check" if safe_count else "blocked",
        }
    ]
    pd.DataFrame(summary_rows).to_csv(
        share_dir / "panel_day_core_duplicate_resolution_summary_v2.csv",
        index=False,
        encoding="utf-8-sig",
    )
    pd.DataFrame(groups_rows).to_csv(
        share_dir / "panel_day_core_duplicate_resolution_groups_v2.csv",
        index=False,
        encoding="utf-8-sig",
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    normalizer_script = root / "research" / "prognostics" / "build_panel_day_core_normalized_v1.py"
    evidence_builder = root / "research" / "prognostics" / "build_panel_day_evidence_matrix_v1.py"
    safe_smoke = root / "research" / "prognostics" / "smoke_test_panel_day_core_duplicate_resolution_audit_v2.py"

    compile_res = run(
        [sys.executable, "-m", "py_compile", str(normalizer_script), str(Path(__file__)), str(evidence_builder)],
        root,
    )
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_raw_fixture_root(tmp_root)
        write_duplicate_resolution_outputs(tmp_root, "evidence_equivalent_duplicate")
        raw_before = {
            site: (tmp_root / "data" / site / "out" / "panel_day_core.csv").read_bytes()
            for site in ["conalog", "gangui", "ktc_ess", "sinhyo"]
        }

        build_res = run([sys.executable, str(normalizer_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"normalizer build failed:\n{build_res.stdout}\n{build_res.stderr}")

        normalized_dir = tmp_root / "_share" / "panel_day_core_normalized_v1"
        produced_site_files = {path.name for path in normalized_dir.iterdir() if path.is_file()}
        assert_true(produced_site_files == EXPECTED_SITE_FILES, "normalizer should emit one normalized sidecar per site")

        summary_df = pd.read_csv(tmp_root / "_share" / "panel_day_core_normalized_summary_v1.csv", encoding="utf-8-sig")
        drop_df = pd.read_csv(tmp_root / "_share" / "panel_day_core_normalized_drop_manifest_v1.csv", encoding="utf-8-sig")
        conalog_df = pd.read_csv(normalized_dir / "conalog.csv", encoding="utf-8-sig")

        summary_row = summary_df.loc[summary_df["record_type"].astype(str).eq("summary")].iloc[0]
        assert_true(int(summary_row["total_safe_duplicate_group_count"]) == 1, "safe duplicate synthetic input should collapse one safe group")
        assert_true(int(summary_row["total_dropped_duplicate_row_count"]) == 1, "safe duplicate synthetic input should drop one duplicate row")
        assert_true(len(conalog_df.loc[conalog_df["panel_id"].astype(str).eq("c.1.1") & conalog_df["date"].astype(str).eq("2025-01-01")]) == 1, "safe duplicate synthetic input should collapse to one normalized row")
        assert_true(len(drop_df) == 1, "drop manifest should record one dropped duplicate row")
        assert_true(
            drop_df.iloc[0]["kept_row_index"] != drop_df.iloc[0]["dropped_row_index"],
            "drop manifest should record distinct kept/dropped row indices",
        )

        for site in ["conalog", "gangui", "ktc_ess", "sinhyo"]:
            raw_after = (tmp_root / "data" / site / "out" / "panel_day_core.csv").read_bytes()
            assert_true(raw_before[site] == raw_after, "raw source files must not be modified")

        evidence_res = run(
            [sys.executable, str(evidence_builder), "--root", str(tmp_root), "--panel-day-source", "normalized"],
            root,
        )
        assert_true(evidence_res.returncode == 0, f"evidence builder should succeed from normalized sidecar:\n{evidence_res.stdout}\n{evidence_res.stderr}")
        evidence_summary = pd.read_csv(tmp_root / "_share" / "panel_day_evidence_matrix_summary_v1.csv", encoding="utf-8-sig")
        assert_true(int(evidence_summary["row_count"].sum()) == 5, "evidence matrix builder should read normalized sidecars successfully")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_raw_fixture_root(tmp_root)
        write_duplicate_resolution_outputs(tmp_root, "numeric_jitter_duplicate")

        fail_res = run([sys.executable, str(normalizer_script), "--root", str(tmp_root)], root)
        assert_true(fail_res.returncode != 0, "unresolved duplicate classes should cause normalizer failure")
        assert_true(
            "unresolved duplicate classes block normalization" in f"{fail_res.stdout}\n{fail_res.stderr}",
            "normalizer failure should mention unresolved duplicate classes",
        )

    print("[OK] scripts compile")
    print("[OK] safe duplicate synthetic input collapses to one normalized row")
    print("[OK] unresolved duplicate classes cause normalizer failure")
    print("[OK] drop manifest records kept/dropped rows")
    print("[OK] evidence matrix builder succeeds from normalized sidecar on synthetic safe input")
    print("[OK] no raw source files are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

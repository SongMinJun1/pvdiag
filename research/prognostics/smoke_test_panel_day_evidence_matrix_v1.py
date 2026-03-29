#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


OUTPUT_NAMES = {
    "panel_day_evidence_matrix_v1.csv",
    "panel_day_evidence_matrix_summary_v1.csv",
}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def write_site_core(path: Path, rows: list[dict[str, object]], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    if columns is not None:
        df = df.reindex(columns=columns)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    common_cols = [
        "date",
        "panel_id",
        "coverage_mid",
        "mid_ratio",
        "last_ratio",
        "mid_v_ratio",
        "mid_i_ratio",
        "v_drop",
        "shadow_like",
        "group_off_like",
        "group_key_base",
    ]

    write_site_core(
        tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-01",
                "panel_id": "ca.10.1",
                "coverage_mid": 0.90,
                "mid_ratio": 0.60,
                "last_ratio": 0.55,
                "mid_v_ratio": 0.70,
                "mid_i_ratio": 0.90,
                "v_drop": 0.40,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "gk.conalog.a",
            },
            {
                "date": "2025-01-02",
                "panel_id": "cb.20.2",
                "coverage_mid": 0.95,
                "mid_ratio": 0.05,
                "last_ratio": 0.02,
                "mid_v_ratio": 0.05,
                "mid_i_ratio": 0.50,
                "v_drop": 0.95,
                "shadow_like": 0,
                "group_off_like": 0,
                "group_key_base": "",
            },
        ],
        columns=common_cols,
    )

    write_site_core(
        tmp_root / "data" / "gangui" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-03",
                "panel_id": "ga.30.3",
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
                "instability_flag": 0,
                "instability_score": 0.10,
            }
        ],
    )

    write_site_core(
        tmp_root / "data" / "ktc_ess" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-04",
                "panel_id": "ktc.8.9",
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
        columns=[col for col in common_cols if col != "group_key_base"],
    )

    write_site_core(
        tmp_root / "data" / "sinhyo" / "out" / "panel_day_core.csv",
        [
            {
                "date": "2025-01-05",
                "panel_id": "si.40.4",
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
        columns=common_cols,
    )


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    build_script = root / "research" / "prognostics" / "build_panel_day_evidence_matrix_v1.py"
    safe_smoke = root / "research" / "prognostics" / "smoke_test_anomaly_registry_schema_pack_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        build_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        share_dir = tmp_root / "_share"
        produced_output_names = {path.name for path in share_dir.iterdir() if path.is_file()}
        assert_true(produced_output_names == OUTPUT_NAMES, "builder should only emit the two evidence-matrix outputs")

        matrix_df = pd.read_csv(share_dir / "panel_day_evidence_matrix_v1.csv", encoding="utf-8-sig")
        summary_df = pd.read_csv(share_dir / "panel_day_evidence_matrix_summary_v1.csv", encoding="utf-8-sig")

        assert_true(len(matrix_df) == 5, "row count should be preserved on synthetic input")
        assert_true(matrix_df[["site", "panel_id", "date"]].duplicated().sum() == 0, "keys should stay unique")
        assert_true(int(summary_df["row_count"].sum()) == 5, "summary row count should match preserved matrix rows")

        electrical_row = matrix_df.loc[
            matrix_df["site"].eq("conalog") & matrix_df["panel_id"].eq("ca.10.1") & matrix_df["date"].eq("2025-01-01")
        ].iloc[0]
        assert_true(electrical_row["group_proxy_value"] == "gk.conalog.a", "group_key_base should be preferred when present")
        assert_true(electrical_row["group_proxy_source"] == "group_key_base", "group_key_base should set high-confidence source")
        assert_true(electrical_row["topology_confidence"] == "high", "group_key_base should map to high topology confidence")
        assert_true(int(electrical_row["electrical_like_flag"]) == 1, "electrical_like_flag should fire on synthetic electrical row")
        assert_true(
            "output_drop+voltage_drop+current_preserved" in electrical_row["local_signal_signature"],
            "local_signal_signature should include negative evidence tokens such as current_preserved",
        )
        assert_true(pd.isna(electrical_row["shape_flag"]), "missing shape columns should remain null")
        assert_true(pd.isna(electrical_row["instability_flag"]), "missing instability columns should remain null")

        open_row = matrix_df.loc[
            matrix_df["site"].eq("conalog") & matrix_df["panel_id"].eq("cb.20.2") & matrix_df["date"].eq("2025-01-02")
        ].iloc[0]
        assert_true(int(open_row["open_device_like_flag"]) == 1, "open_device_like_flag should fire on synthetic open-device row")
        assert_true(open_row["group_proxy_value"] == "cb.20", "panel_id token fallback should work when group_key_base is blank")
        assert_true(open_row["group_proxy_source"] == "panel_id_token_proxy", "fallback proxy should set panel_id_token_proxy source")
        assert_true(open_row["topology_confidence"] == "low", "fallback proxy should map to low topology confidence")
        assert_true("current_drop" in open_row["local_signal_signature"], "signature should include current_drop style negative evidence")

        shape_row = matrix_df.loc[
            matrix_df["site"].eq("gangui") & matrix_df["panel_id"].eq("ga.30.3") & matrix_df["date"].eq("2025-01-03")
        ].iloc[0]
        assert_true(int(shape_row["shape_flag"]) == 1, "optional shape evidence should map through when present")
        assert_true(shape_row["evidence_reason_code"] == "EVID_SHAPE_PERSISTENT", "shape presence should drive evidence reason code")
        assert_true("shape_present" in shape_row["local_signal_signature"], "optional shape evidence should appear in signature")

        token_proxy_row = matrix_df.loc[
            matrix_df["site"].eq("ktc_ess") & matrix_df["panel_id"].eq("ktc.8.9") & matrix_df["date"].eq("2025-01-04")
        ].iloc[0]
        assert_true(
            token_proxy_row["group_proxy_value"] == "ktc.8",
            "panel_id token fallback should work when group_key_base column is absent",
        )

        confounded_row = matrix_df.loc[
            matrix_df["site"].eq("sinhyo") & matrix_df["panel_id"].eq("si.40.4") & matrix_df["date"].eq("2025-01-05")
        ].iloc[0]
        assert_true("group_off_like" in confounded_row["local_signal_signature"], "confound tokens should appear when active")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_root = Path(tmpdir)
        build_fixture_root(tmp_root)

        duplicate_path = tmp_root / "data" / "conalog" / "out" / "panel_day_core.csv"
        duplicate_df = pd.read_csv(duplicate_path, encoding="utf-8-sig")
        duplicate_df = pd.concat([duplicate_df, duplicate_df.iloc[[0]]], ignore_index=True)
        duplicate_df.to_csv(duplicate_path, index=False, encoding="utf-8-sig")

        dup_res = run([sys.executable, str(build_script), "--root", str(tmp_root)], root)
        assert_true(dup_res.returncode != 0, "duplicate site/panel/date keys should fail loudly")
        assert_true(
            "duplicate site/panel/date" in f"{dup_res.stdout}\n{dup_res.stderr}",
            "duplicate failure should mention duplicate site/panel/date keys",
        )

    print("[OK] scripts compile")
    print("[OK] outputs generate")
    print("[OK] row count is preserved on synthetic input")
    print("[OK] duplicate site/panel/date keys fail loudly")
    print("[OK] group_key_base is preferred when present")
    print("[OK] panel_id token fallback works when group_key_base is absent")
    print("[OK] electrical_like_flag fires on a synthetic electrical row")
    print("[OK] open_device_like_flag fires on a synthetic open-device row")
    print("[OK] missing shape/instability columns remain null")
    print("[OK] local_signal_signature includes current_preserved or current_drop style negative evidence")
    print("[OK] no official outputs are modified")

    safe_smoke_res = run([sys.executable, str(safe_smoke)], root)
    assert_true(
        safe_smoke_res.returncode == 0,
        f"existing safe smoke failed:\n{safe_smoke_res.stdout}\n{safe_smoke_res.stderr}",
    )
    print("[OK] existing safe smoke paths still pass if invoked separately")


if __name__ == "__main__":
    main()

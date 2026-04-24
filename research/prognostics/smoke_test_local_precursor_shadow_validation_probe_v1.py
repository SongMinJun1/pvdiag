#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

from smoke_test_panel_day_engine_local_precursor_shadow_v1 import assert_true, build_fixture_root


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    probe_script = root / "research" / "prognostics" / "run_local_precursor_shadow_validation_probe_v1.py"
    build_script = root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_shadow_v1.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script), str(probe_script), str(Path(__file__))], root)
    assert_true(compile_res.returncode == 0, f"compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory() as tmpdir:
        src_root = Path(tmpdir) / "src"
        out_root = Path(tmpdir) / "probe_out"
        build_fixture_root(src_root)

        gate_path = src_root / "data" / "conalog" / "out" / "ae_simple_local_precursor_gate_daily.csv"
        gate_df = pd.read_csv(gate_path, encoding="utf-8-sig")
        conflict_row = gate_df.loc[
            gate_df["panel_id"].eq("panel.a") & gate_df["date"].eq("2025-01-02")
        ].iloc[0].copy()
        conflict_row["signal_count"] = int(conflict_row["signal_count"]) + 1
        conflict_row["ews_runlen"] = int(conflict_row["ews_runlen"]) + 2
        gate_df = pd.concat([gate_df, pd.DataFrame([conflict_row])], ignore_index=True)
        gate_df.to_csv(gate_path, index=False, encoding="utf-8-sig")

        probe_res = run(
            [
                sys.executable,
                str(probe_script),
                "--root",
                str(src_root),
                "--output-root",
                str(out_root),
                "--sites",
                "conalog",
            ],
            root,
        )
        assert_true(probe_res.returncode == 0, f"probe failed:\n{probe_res.stdout}\n{probe_res.stderr}")

        summary_df = pd.read_csv(out_root / "gate_duplicate_resolution_summary_v1.csv", encoding="utf-8-sig")
        assert_true(int(summary_df.loc[0, "conflicting_duplicate_keys"]) == 1, "wrapper should record one conflicting duplicate key")
        assert_true(int(summary_df.loc[0, "rows_dropped"]) == 2, "wrapper should collapse three source rows into one")
        assert_true(int(summary_df.loc[0, "used_sanitized_copy"]) == 1, "wrapper should materialize a sanitized gate file")

        audit_df = pd.read_csv(out_root / "gate_duplicate_resolution_key_audit_v1.csv", encoding="utf-8-sig")
        assert_true(len(audit_df) == 1, "key audit should capture the single duplicate key")
        assert_true(audit_df.loc[0, "duplicate_kind"] == "conflicting", "duplicate kind should be conflicting")
        assert_true(int(audit_df.loc[0, "source_rows"]) == 3, "the audited duplicate key should show all three source rows")
        assert_true(audit_df.loc[0, "varying_columns"] == "signal_count|ews_runlen", "varying columns should be recorded")

        source_gate_after = pd.read_csv(gate_path, encoding="utf-8-sig")
        assert_true(len(source_gate_after) == len(gate_df), "source gate file should remain unchanged")

        probe_gate = pd.read_csv(
            out_root / "probe_root" / "data" / "conalog" / "out" / "ae_simple_local_precursor_gate_daily.csv",
            encoding="utf-8-sig",
        )
        jan2 = probe_gate.loc[
            probe_gate["panel_id"].eq("panel.a") & probe_gate["date"].eq("2025-01-02")
        ].iloc[0]
        assert_true(int(jan2["signal_count"]) == 4, "conflicting duplicate rows should collapse by numeric max")
        assert_true(int(jan2["ews_runlen"]) == 8, "conflicting duplicate rows should collapse by numeric max")

        shadow_df = pd.read_csv(
            out_root / "probe_root" / "_share" / "panel_day_engine_local_precursor_shadow_v1.csv",
            encoding="utf-8-sig",
        )
        shadow_jan2 = shadow_df.loc[
            shadow_df["site"].eq("conalog")
            & shadow_df["panel_id"].eq("panel.a")
            & shadow_df["date"].eq("2025-01-02")
        ].iloc[0]
        assert_true(int(shadow_jan2["prefault_B_effective_flag"]) == 0, "common-cause-overlapped prefault should stay ineffective after probe build")
        assert_true(shadow_jan2["alert_pattern"] == "no_local_precursor", "shadow semantics should remain unchanged")

    print("[OK] local precursor shadow validation probe wrapper smoke test passed")


if __name__ == "__main__":
    main()

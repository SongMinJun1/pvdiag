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


def write_csv(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_fixture(root: Path) -> None:
    write_csv(
        root / "_share" / "site_panel_id_hypothesis_latest.csv",
        "site,panel_id,token0_uuid,token1_group,token2_index,token2_index_int,panel_id_pattern_valid,parse_note\n"
        "conalog,p1,u1,0,0,0,1,\n"
        "conalog,p2,u1,1,1,1,1,\n"
        "gangui,p3,u2,0,0,0,1,\n"
        "gangui,p4,u3,0,0,0,1,\n",
    )
    write_csv(
        root / "data" / "conalog" / "out" / "panel_day_risk_ensemble.csv",
        "site,panel_id,date,group_key_base\n"
        "conalog,p1,2026-02-18,u1.0\n"
        "conalog,p2,2026-02-18,u1.1\n",
    )
    write_csv(
        root / "data" / "gangui" / "out" / "panel_day_risk_ensemble.csv",
        "site,panel_id,date,group_key_base\n"
        "gangui,p3,2026-02-19,u2\n"
        "gangui,p4,2026-02-19,u9.9\n",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_grouping_equivalence_audit.py"
    smoke_weather = repo_root / "research" / "prognostics" / "smoke_test_site_weather_history.py"
    smoke_event = repo_root / "research" / "prognostics" / "smoke_test_site_event_dataset.py"
    smoke_frame = repo_root / "research" / "prognostics" / "smoke_test_site_day_event_frame.py"
    smoke_episode = repo_root / "research" / "prognostics" / "smoke_test_site_day_alert_episodes.py"
    smoke_field = repo_root / "research" / "prognostics" / "smoke_test_field_truth_validation.py"
    smoke_hypothesis = repo_root / "research" / "prognostics" / "smoke_test_panel_id_hypothesis.py"

    compile_res = run([sys.executable, "-m", "py_compile", str(build_script)], repo_root)
    assert_true(compile_res.returncode == 0, f"py_compile failed:\n{compile_res.stdout}\n{compile_res.stderr}")

    with tempfile.TemporaryDirectory(prefix="grouping_equivalence_smoke_") as tmpdir:
        root = Path(tmpdir)
        build_fixture(root)

        build_res = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(build_res.returncode == 0, f"build failed:\n{build_res.stdout}\n{build_res.stderr}")

        latest_path = root / "_share" / "site_grouping_equivalence_latest.csv"
        summary_path = root / "_share" / "site_grouping_equivalence_summary.csv"
        mismatch_path = root / "_share" / "site_grouping_mismatches.csv"

        assert_true(latest_path.exists(), "site_grouping_equivalence_latest.csv was not generated")
        assert_true(summary_path.exists(), "site_grouping_equivalence_summary.csv was not generated")
        assert_true(mismatch_path.exists(), "site_grouping_mismatches.csv was not generated")

        latest = pd.read_csv(latest_path, low_memory=False, encoding="utf-8-sig")
        summary = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")
        mismatches = pd.read_csv(mismatch_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not latest.empty, "latest equivalence output is unexpectedly empty")
        for col in ["match_rate_token0", "match_rate_token0_token1"]:
            numeric = pd.to_numeric(summary[col], errors="coerce")
            assert_true(numeric.between(0, 1, inclusive="both").all(), f"{col} must be within [0,1]")
        assert_true(not mismatches.empty, "synthetic fixture should emit mismatch rows")

        conalog_p2 = latest.loc[(latest["site"].astype(str) == "conalog") & (latest["panel_id"].astype(str) == "p2")].iloc[0]
        assert_true(int(conalog_p2["match_token0"]) == 0, "p2 should mismatch token0")
        assert_true(int(conalog_p2["match_token0_token1"]) == 1, "p2 should match token0.token1")

        gangui_p4 = latest.loc[(latest["site"].astype(str) == "gangui") & (latest["panel_id"].astype(str) == "p4")].iloc[0]
        assert_true(int(gangui_p4["match_token0"]) == 0, "p4 should mismatch token0")
        assert_true(int(gangui_p4["match_token0_token1"]) == 0, "p4 should mismatch token0.token1")

    for script in [smoke_weather, smoke_event, smoke_frame, smoke_episode, smoke_field, smoke_hypothesis]:
        res = run([sys.executable, str(script)], repo_root)
        assert_true(res.returncode == 0, f"stable smoke failed for {script.name}:\n{res.stdout}\n{res.stderr}")

    print("[OK] grouping equivalence audit scripts compile")
    print("[OK] outputs generate")
    print("[OK] match rates stay within [0,1]")
    print("[OK] mismatch rows are emitted on intentionally different fixture")
    print("[OK] existing weather/event/frame/episode/truth/panel-id-hypothesis smoke paths still pass")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_field_trial_real_capture_watchlist_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        schema_dir = tmp / "schema"
        readiness_dir = tmp / "readiness"
        intake_dir = tmp / "intake"
        manifest_dir = tmp / "manifest"
        guard_dir = tmp / "guard"
        br107_root = tmp / "br107_empty"
        br108_root = tmp / "br108_empty"
        dry_run_dir = tmp / "dry_run_gate"
        watchlist_dir = tmp / "watchlist"

        setup_commands = [
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_schema_v1.py",
                "--repo-root",
                str(repo_root),
                "--output-dir",
                str(schema_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--output-dir",
                str(readiness_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(schema_dir / "mlpe_field_trial_capture_template_v1.csv"),
                "--readiness-input",
                str(readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--output-dir",
                str(intake_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_package_manifest_v1.py",
                "--repo-root",
                str(repo_root),
                "--schema-dir",
                str(schema_dir),
                "--readiness-dir",
                str(readiness_dir),
                "--intake-dir",
                str(intake_dir),
                "--output-dir",
                str(manifest_dir),
            ],
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py",
                "--repo-root",
                str(repo_root),
                "--readiness-input",
                str(readiness_dir / "mlpe_field_trial_capture_readiness_packet_v1.csv"),
                "--manifest-summary-input",
                str(manifest_dir / "mlpe_field_trial_package_manifest_summary_v1.csv"),
                "--output-dir",
                str(guard_dir),
            ],
        ]
        for cmd in setup_commands:
            proc = run(cmd, repo_root)
            assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        # For this smoke, a minimal passing dry-run summary is enough to test watchlist gating.
        dry_run_dir.mkdir(parents=True, exist_ok=True)
        (dry_run_dir / "mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv").write_text(
            "owner_branch,gate_rows,passed_rows,failed_rows,overall_passed_flag,truth_intake_allowed_sum,threshold_patch_allowed_sum,engine_patch_allowed_sum\n"
            "BR-20260425-109,8,8,0,1,0,0,0\n",
            encoding="utf-8",
        )
        br107_root.mkdir()
        br108_root.mkdir()

        proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_real_capture_intake_watchlist_v1.py",
                "--repo-root",
                str(repo_root),
                "--operator-checklist",
                str(intake_dir / "mlpe_field_trial_operator_intake_checklist_v1.csv"),
                "--handoff-guard",
                str(guard_dir / "mlpe_field_trial_adjudication_handoff_guard_v1.csv"),
                "--dry-run-gate-summary",
                str(dry_run_dir / "mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv"),
                "--output-dir",
                str(watchlist_dir),
            ],
            repo_root,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        assert_true(payload["rows"] == 14, payload)
        assert_true(payload["dry_run_gate_passed_flag"] == 1, payload)
        assert_true(payload["real_capture_required_rows"] == 14, payload)
        assert_true(payload["truth_intake_allowed_sum"] == 0, payload)
        print(json.dumps({"smoke": "ok", "rows": payload["rows"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

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


def run_checked(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    proc = run(cmd, cwd)
    assert_true(proc.returncode == 0, proc.stderr or proc.stdout)
    return proc


def build_planned_watchlist(repo_root: Path, tmp: Path) -> tuple[Path, Path]:
    schema_dir = tmp / "schema"
    readiness_dir = tmp / "readiness"
    intake_dir = tmp / "intake"
    manifest_dir = tmp / "manifest"
    guard_dir = tmp / "guard"
    dry_run_dir = tmp / "dry_run_gate"
    watchlist_dir = tmp / "watchlist"

    commands = [
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
    for cmd in commands:
        run_checked(cmd, repo_root)

    dry_run_dir.mkdir(parents=True, exist_ok=True)
    (dry_run_dir / "mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv").write_text(
        "owner_branch,gate_rows,passed_rows,failed_rows,overall_passed_flag,truth_intake_allowed_sum,threshold_patch_allowed_sum,engine_patch_allowed_sum\n"
        "BR-20260425-109,8,8,0,1,0,0,0\n",
        encoding="utf-8",
    )
    run_checked(
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
    return (
        schema_dir / "mlpe_field_trial_capture_template_v1.csv",
        watchlist_dir / "mlpe_field_trial_real_capture_intake_watchlist_v1.csv",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_capture_return_validator_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        planned_capture, watchlist = build_planned_watchlist(repo_root, tmp)

        waiting_dir = tmp / "waiting_validation"
        waiting_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--watchlist",
                str(watchlist),
                "--returned-capture",
                str(planned_capture),
                "--output-dir",
                str(waiting_dir),
            ],
            repo_root,
        )
        waiting_payload = json.loads(waiting_proc.stdout)
        assert_true(waiting_payload["rows"] == 14, waiting_payload)
        assert_true(waiting_payload["still_waiting_rows"] == 14, waiting_payload)
        assert_true(waiting_payload["returned_ready_rows"] == 0, waiting_payload)
        assert_true(waiting_payload["validation_failed_rows"] == 0, waiting_payload)
        assert_true(waiting_payload["truth_intake_allowed_sum"] == 0, waiting_payload)
        waiting_artifact = json.loads(
            (waiting_dir / "mlpe_field_trial_capture_return_validation_v1.json").read_text(
                encoding="utf-8"
            )
        )
        waiting_note = (waiting_dir / "mlpe_field_trial_capture_return_validation_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(waiting_artifact["input_resolution_sources"]["returned_capture"] == "explicit_cli", waiting_artifact)
        assert_true("evidence input manifest: `not provided`" in waiting_note, waiting_note)
        assert_true("`returned_capture`: `explicit_cli`" in waiting_note, waiting_note)

        manifest_path = tmp / "capture_return_validator_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"returned_capture": str(planned_capture)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_dir = tmp / "manifest_validation"
        manifest_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--watchlist",
                str(watchlist),
                "--input-manifest",
                str(manifest_path),
                "--output-dir",
                str(manifest_dir),
            ],
            repo_root,
        )
        manifest_payload = json.loads(manifest_proc.stdout)
        manifest_artifact = json.loads(
            (manifest_dir / "mlpe_field_trial_capture_return_validation_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (manifest_dir / "mlpe_field_trial_capture_return_validation_note_v1.md").read_text(
            encoding="utf-8"
        )
        assert_true(manifest_payload["still_waiting_rows"] == waiting_payload["still_waiting_rows"], manifest_payload)
        assert_true(manifest_artifact["input_resolution_sources"]["returned_capture"] == "input_manifest", manifest_artifact)
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`returned_capture`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_capture_return_validator_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"returned_capture": str(tmp / "missing_returned_capture.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_dir = tmp / "override_validation"
        override_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--watchlist",
                str(watchlist),
                "--input-manifest",
                str(bad_manifest_path),
                "--returned-capture",
                str(planned_capture),
                "--output-dir",
                str(override_dir),
            ],
            repo_root,
        )
        override_payload = json.loads(override_proc.stdout)
        assert_true(override_payload["input_resolution_sources"]["returned_capture"] == "explicit_cli", override_payload)

        missing_key_manifest = tmp / "missing_key_capture_return_validator_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, indent=2) + "\n", encoding="utf-8")
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--watchlist",
                str(watchlist),
                "--input-manifest",
                str(missing_key_manifest),
                "--output-dir",
                str(tmp / "missing_key_validation"),
            ],
            repo_root,
        )
        assert_true(missing_key_proc.returncode != 0, "missing-key manifest unexpectedly passed")
        assert_true(
            "missing `returned_capture`" in (missing_key_proc.stderr + missing_key_proc.stdout),
            missing_key_proc.stderr,
        )

        fixture_dir = tmp / "fixture"
        fixture_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_filled_capture_fixture_v1.py",
                "--repo-root",
                str(repo_root),
                "--capture-input",
                str(planned_capture),
                "--output-dir",
                str(fixture_dir),
            ],
            repo_root,
        )
        fixture_payload = json.loads(fixture_proc.stdout)
        filled_capture = Path(fixture_payload["outputs"]["capture"])

        returned_dir = tmp / "returned_validation"
        returned_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
                "--repo-root",
                str(repo_root),
                "--watchlist",
                str(watchlist),
                "--returned-capture",
                str(filled_capture),
                "--output-dir",
                str(returned_dir),
            ],
            repo_root,
        )
        returned_payload = json.loads(returned_proc.stdout)
        assert_true(returned_payload["rows"] == 14, returned_payload)
        assert_true(returned_payload["still_waiting_rows"] == 0, returned_payload)
        assert_true(returned_payload["returned_ready_rows"] == 14, returned_payload)
        assert_true(returned_payload["validation_failed_rows"] == 0, returned_payload)
        assert_true(returned_payload["truth_intake_allowed_sum"] == 0, returned_payload)
        print(json.dumps({"smoke": "ok", "waiting_rows": 14, "returned_ready_rows": 14}, ensure_ascii=False))


if __name__ == "__main__":
    main()

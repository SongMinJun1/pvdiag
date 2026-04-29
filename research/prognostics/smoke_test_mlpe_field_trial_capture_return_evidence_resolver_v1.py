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


def validate_return(repo_root: Path, watchlist: Path, returned_capture: Path, validation_dir: Path) -> Path:
    run_checked(
        [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py",
            "--repo-root",
            str(repo_root),
            "--watchlist",
            str(watchlist),
            "--returned-capture",
            str(returned_capture),
            "--output-dir",
            str(validation_dir),
        ],
        repo_root,
    )
    return validation_dir / "mlpe_field_trial_capture_return_validation_v1.csv"


def resolve_evidence(repo_root: Path, validation: Path, returned_capture: Path, output_dir: Path) -> dict[str, object]:
    proc = run_checked(
        [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
            "--repo-root",
            str(repo_root),
            "--validation",
            str(validation),
            "--returned-capture",
            str(returned_capture),
            "--output-dir",
            str(output_dir),
        ],
        repo_root,
    )
    return json.loads(proc.stdout)


def resolve_evidence_with_manifest(
    repo_root: Path,
    validation: Path,
    input_manifest: Path,
    output_dir: Path,
) -> dict[str, object]:
    proc = run_checked(
        [
            sys.executable,
            "research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
            "--repo-root",
            str(repo_root),
            "--validation",
            str(validation),
            "--input-manifest",
            str(input_manifest),
            "--output-dir",
            str(output_dir),
        ],
        repo_root,
    )
    return json.loads(proc.stdout)


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="mlpe_capture_return_evidence_resolver_smoke_") as tmpdir:
        tmp = Path(tmpdir)
        planned_capture, watchlist = build_planned_watchlist(repo_root, tmp)

        waiting_validation = validate_return(repo_root, watchlist, planned_capture, tmp / "waiting_validation")
        waiting_payload = resolve_evidence(repo_root, waiting_validation, planned_capture, tmp / "waiting_evidence")
        assert_true(waiting_payload["events"] == 14, waiting_payload)
        assert_true(waiting_payload["waiting_events"] == 14, waiting_payload)
        assert_true(waiting_payload["returned_ready_events"] == 0, waiting_payload)
        assert_true(waiting_payload["evidence_rows"] == 56, waiting_payload)
        assert_true(waiting_payload["evidence_file_exists_rows"] == 0, waiting_payload)
        assert_true(waiting_payload["required_evidence_problem_rows"] == 0, waiting_payload)
        assert_true(waiting_payload["truth_intake_allowed_sum"] == 0, waiting_payload)
        waiting_artifact = json.loads(
            (tmp / "waiting_evidence" / "mlpe_field_trial_capture_return_evidence_resolution_v1.json").read_text(
                encoding="utf-8"
            )
        )
        waiting_note = (
            tmp / "waiting_evidence" / "mlpe_field_trial_capture_return_evidence_resolution_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(waiting_artifact["input_resolution_sources"]["returned_capture"] == "explicit_cli", waiting_artifact)
        assert_true("evidence input manifest: `not provided`" in waiting_note, waiting_note)
        assert_true("`returned_capture`: `explicit_cli`" in waiting_note, waiting_note)

        manifest_path = tmp / "capture_return_evidence_resolver_inputs.json"
        manifest_path.write_text(
            json.dumps(
                {"inputs": {"returned_capture": str(planned_capture)}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest_payload = resolve_evidence_with_manifest(
            repo_root,
            waiting_validation,
            manifest_path,
            tmp / "manifest_evidence",
        )
        manifest_artifact = json.loads(
            (tmp / "manifest_evidence" / "mlpe_field_trial_capture_return_evidence_resolution_v1.json").read_text(
                encoding="utf-8"
            )
        )
        manifest_note = (
            tmp / "manifest_evidence" / "mlpe_field_trial_capture_return_evidence_resolution_note_v1.md"
        ).read_text(encoding="utf-8")
        assert_true(manifest_payload["waiting_events"] == waiting_payload["waiting_events"], manifest_payload)
        assert_true(manifest_artifact["input_resolution_sources"]["returned_capture"] == "input_manifest", manifest_artifact)
        assert_true(f"evidence input manifest: `{manifest_path}`" in manifest_note, manifest_note)
        assert_true("`returned_capture`: `input_manifest`" in manifest_note, manifest_note)

        bad_manifest_path = tmp / "bad_capture_return_evidence_resolver_inputs.json"
        bad_manifest_path.write_text(
            json.dumps(
                {"inputs": {"returned_capture": str(tmp / "missing_returned_capture.csv")}},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        override_proc = run_checked(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
                "--repo-root",
                str(repo_root),
                "--validation",
                str(waiting_validation),
                "--input-manifest",
                str(bad_manifest_path),
                "--returned-capture",
                str(planned_capture),
                "--output-dir",
                str(tmp / "override_evidence"),
            ],
            repo_root,
        )
        override_payload = json.loads(override_proc.stdout)
        assert_true(override_payload["input_resolution_sources"]["returned_capture"] == "explicit_cli", override_payload)

        missing_key_manifest = tmp / "missing_key_capture_return_evidence_resolver_inputs.json"
        missing_key_manifest.write_text(json.dumps({"inputs": {}}, indent=2) + "\n", encoding="utf-8")
        missing_key_proc = run(
            [
                sys.executable,
                "research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py",
                "--repo-root",
                str(repo_root),
                "--validation",
                str(waiting_validation),
                "--input-manifest",
                str(missing_key_manifest),
                "--output-dir",
                str(tmp / "missing_key_evidence"),
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
        filled_capture = Path(json.loads(fixture_proc.stdout)["outputs"]["capture"])
        returned_validation = validate_return(repo_root, watchlist, filled_capture, tmp / "returned_validation")
        returned_payload = resolve_evidence(repo_root, returned_validation, filled_capture, tmp / "returned_evidence")
        assert_true(returned_payload["events"] == 14, returned_payload)
        assert_true(returned_payload["waiting_events"] == 0, returned_payload)
        assert_true(returned_payload["returned_ready_events"] == 14, returned_payload)
        assert_true(returned_payload["evidence_rows"] == 56, returned_payload)
        assert_true(returned_payload["evidence_file_exists_rows"] == 56, returned_payload)
        assert_true(returned_payload["required_evidence_problem_rows"] == 0, returned_payload)
        assert_true(returned_payload["evidence_file_size_total_bytes"] > 0, returned_payload)
        assert_true(returned_payload["truth_intake_allowed_sum"] == 0, returned_payload)
        print(json.dumps({"smoke": "ok", "waiting_events": 14, "resolved_evidence_rows": 56}, ensure_ascii=False))


if __name__ == "__main__":
    main()

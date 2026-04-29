#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def write_fixture_repo(root: Path) -> None:
    private_tmp = "/private" + "/tmp"
    research = root / "research" / "prognostics"
    research.mkdir(parents=True)
    (research / "build_panel_day_engine_latest_evidence_handoff_manifest_v1.py").write_text(
        "\n".join(
            [
                "BR_FIX_001_REPRO = (",
                '    "python3 build.py "',
                f'    "--packet-input {private_tmp}/in/a.csv "',
                f'    "--output-dir {private_tmp}/out"',
                ")",
                "BR_FIX_003_REPRO = (",
                '    "python3 gate.py "',
                f'    "--repo-root {private_tmp}/old_checkout "',
                f'    "--review-input {private_tmp}/in/b.csv "',
                f'    "--output-dir {private_tmp}/gate"',
                ")",
                "",
                "BRANCH_SPECS = [",
                "    {",
                '        "branch_id": "BR-FIX-001",',
                '        "branch_title": "input_and_output",',
                '        "evidence_layer": "fault_family_candidate_pool",',
                '        "handoff_state": "indexed_for_review",',
                f'        "primary_artifact_path": "{private_tmp}/out/packet.csv",',
                '        "repro_command": BR_FIX_001_REPRO,',
                "    },",
                "    {",
                '        "branch_id": "BR-FIX-002",',
                '        "branch_title": "repo_doc",',
                '        "evidence_layer": "handoff_navigation",',
                '        "handoff_state": "repo_doc",',
                '        "primary_artifact_path": "docs/repo_doc.md",',
                '        "repro_command": "python3 -m py_compile pv_ae/panel_day_engine.py",',
                "    },",
                "    {",
                '        "branch_id": "BR-FIX-003",',
                '        "branch_title": "repo_root_plus_input",',
                '        "evidence_layer": "prepatch_safety_gate",',
                '        "handoff_state": "required_before_algorithm_review",',
                f'        "primary_artifact_path": "{private_tmp}/gate/gate.csv",',
                '        "repro_command": BR_FIX_003_REPRO,',
                "    },",
                "]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_latest_handoff_manifest_repro_refresh_plan_v1.py"
    with tempfile.TemporaryDirectory(prefix="latest_handoff_repro_refresh_plan_") as tmpdir:
        fixture_root = Path(tmpdir) / "fixture_repo"
        output_dir = Path(tmpdir) / "out"
        write_fixture_repo(fixture_root)
        proc = subprocess.run(
            [
                sys.executable,
                str(builder),
                "--repo-root",
                str(fixture_root),
                "--output-dir",
                str(output_dir),
            ],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        payload = json.loads(
            (output_dir / "latest_handoff_manifest_repro_refresh_plan_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "latest_handoff_manifest_repro_refresh_plan_v1.csv")
        summary = pd.read_csv(
            output_dir / "latest_handoff_manifest_repro_refresh_plan_summary_v1.csv"
        )
        note = (output_dir / "latest_handoff_manifest_repro_refresh_plan_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["branch_spec_rows"] == 3, payload)
        assert_true(payload["refresh_required_branch_rows"] == 2, payload)
        assert_true(payload["repo_doc_no_refresh_branch_rows"] == 1, payload)
        assert_true(payload["latest_handoff_repro_literal_rows_from_br228"] == 5, payload)
        assert_true(payload["planned_repro_temp_literal_rows"] == 5, payload)
        assert_true(payload["temp_input_literal_rows"] == 2, payload)
        assert_true(payload["temp_output_literal_rows"] == 2, payload)
        assert_true(payload["temp_repo_root_literal_rows"] == 1, payload)
        assert_true(payload["manifest_input_required_branch_rows"] == 2, payload)
        assert_true(payload["output_parameterization_required_branch_rows"] == 2, payload)
        assert_true(payload["repo_root_refresh_required_branch_rows"] == 1, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["latest_literal_count_match"] == 1, payload)
        assert_true(payload["refresh_plan_complete"] == 1, payload)

        buckets = set(detail["refresh_bucket"])
        assert_true("manifest_inputs_and_parameterized_output_plan" in buckets, detail.to_dict("records"))
        assert_true("repo_doc_no_repro_refresh_needed" in buckets, detail.to_dict("records"))
        assert_true("repo_root_plus_manifest_input_refresh_plan" in buckets, detail.to_dict("records"))
        assert_true("Do not edit latest handoff repro literals one by one" in note, note)
        assert_true(
            int(summary[summary["key"].eq("planned_repro_temp_literal_rows")]["count"].iloc[0])
            == 5,
            summary.to_dict("records"),
        )

    print("smoke ok: latest_handoff_manifest_repro_refresh_plan_v1")


if __name__ == "__main__":
    main()

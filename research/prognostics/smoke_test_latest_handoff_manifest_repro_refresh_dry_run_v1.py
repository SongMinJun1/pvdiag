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

    for script_name in [
        "build.py",
        "gate.py",
    ]:
        (research / script_name).write_text(
            "\n".join(
                [
                    "import argparse",
                    "parser = argparse.ArgumentParser()",
                    "parser.add_argument('--input-manifest')",
                    "parser.add_argument('--output-dir', required=True)",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

    (research / "build_panel_day_engine_latest_evidence_handoff_manifest_v1.py").write_text(
        "\n".join(
            [
                "BR_FIX_001_REPRO = (",
                '    "python3 research/prognostics/build.py "',
                f'    "--packet-input {private_tmp}/in/a.csv "',
                f'    "--output-dir {private_tmp}/out"',
                ")",
                "BR_FIX_002_REPRO = (",
                '    "python3 research/prognostics/build.py "',
                f'    "--packet-input {private_tmp}/different/packet.csv "',
                f'    "--output-dir {private_tmp}/other"',
                ")",
                "BR_FIX_004_REPRO = (",
                '    "python3 research/prognostics/gate.py "',
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
                '        "branch_title": "same_flag_different_artifact",',
                '        "evidence_layer": "fault_family_candidate_pool",',
                '        "handoff_state": "indexed_for_review",',
                f'        "primary_artifact_path": "{private_tmp}/other/other.csv",',
                '        "repro_command": BR_FIX_002_REPRO,',
                "    },",
                "    {",
                '        "branch_id": "BR-FIX-003",',
                '        "branch_title": "repo_doc",',
                '        "evidence_layer": "handoff_navigation",',
                '        "handoff_state": "repo_doc",',
                '        "primary_artifact_path": "docs/repo_doc.md",',
                '        "repro_command": "python3 -m py_compile pv_ae/panel_day_engine.py",',
                "    },",
                "    {",
                '        "branch_id": "BR-FIX-004",',
                '        "branch_title": "repo_root_plus_input",',
                '        "evidence_layer": "prepatch_safety_gate",',
                '        "handoff_state": "required_before_algorithm_review",',
                f'        "primary_artifact_path": "{private_tmp}/gate/gate.csv",',
                '        "repro_command": BR_FIX_004_REPRO,',
                "    },",
                "]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_latest_handoff_manifest_repro_refresh_dry_run_v1.py"
    with tempfile.TemporaryDirectory(prefix="latest_handoff_repro_refresh_dry_run_") as tmpdir:
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
            (output_dir / "latest_handoff_manifest_repro_refresh_dry_run_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "latest_handoff_manifest_repro_refresh_dry_run_v1.csv")
        summary = pd.read_csv(
            output_dir / "latest_handoff_manifest_repro_refresh_dry_run_summary_v1.csv"
        )
        templates = json.loads(
            (
                output_dir
                / "latest_handoff_manifest_repro_refresh_input_manifest_templates_v1.json"
            ).read_text(encoding="utf-8")
        )
        note = (output_dir / "latest_handoff_manifest_repro_refresh_dry_run_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["branch_spec_rows"] == 4, payload)
        assert_true(payload["refresh_required_branch_rows"] == 3, payload)
        assert_true(payload["repo_doc_unchanged_branch_rows"] == 1, payload)
        assert_true(payload["old_private_tmp_literal_rows"] == 7, payload)
        assert_true(payload["proposed_private_tmp_literal_rows"] == 0, payload)
        assert_true(payload["input_manifest_added_rows"] == 3, payload)
        assert_true(payload["input_flags_removed_rows"] == 3, payload)
        assert_true(payload["output_literals_replaced_rows"] == 3, payload)
        assert_true(payload["repo_root_literals_replaced_rows"] == 1, payload)
        assert_true(payload["global_manifest_key_conflict_rows"] == 1, payload)
        assert_true(payload["branch_manifest_key_collision_rows"] == 0, payload)
        assert_true(payload["plan_count_match"] == 1, payload)
        assert_true(payload["dry_run_complete"] == 1, payload)

        changed = detail[detail["command_changed"].eq(1)]
        assert_true(len(changed) == 3, detail.to_dict("records"))
        assert_true(
            changed["proposed_repro_command"].str.contains("--input-manifest").all(),
            changed.to_dict("records"),
        )
        assert_true(
            changed["proposed_repro_command"].str.contains("LATEST_HANDOFF_OUTPUT_ROOT").all(),
            changed.to_dict("records"),
        )
        assert_true(
            not changed["proposed_repro_command"].str.contains("/private/tmp").any(),
            changed.to_dict("records"),
        )
        assert_true(
            "BR-FIX-001" in templates["branches"] and "BR-FIX-002" in templates["branches"],
            templates,
        )
        assert_true(
            templates["branches"]["BR-FIX-001"]["inputs"]["packet_input"]["path"]
            != templates["branches"]["BR-FIX-002"]["inputs"]["packet_input"]["path"],
            templates,
        )
        assert_true("branch-local input manifest" in note, note)
        assert_true(
            int(summary[summary["key"].eq("dry_run_complete")]["count"].iloc[0]) == 1,
            summary.to_dict("records"),
        )

    print("smoke ok: latest_handoff_manifest_repro_refresh_dry_run_v1")


if __name__ == "__main__":
    main()

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
                "REPRO = (",
                f'    "python3 build.py --input {private_tmp}/latest/in.csv --output-dir {private_tmp}/latest/out"',
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (research / "build_panel_day_engine_evidence_manifest_v1.py").write_text(
        f'REPRO = "python3 build.py --result-root {private_tmp}/evidence/result"\n',
        encoding="utf-8",
    )
    (research / "build_panel_day_engine_episode_truth_map_v1.py").write_text(
        f'REPRO = "python3 build.py --repo-root {private_tmp}/old_checkout --output-dir {{output_dir}}"\n',
        encoding="utf-8",
    )
    (research / "check_panel_day_engine_patch_safety_gate_v1.py").write_text(
        "\n".join(
            [
                "VALIDATION_COMMANDS = [",
                f'    "python3 run.py --output-root {private_tmp}/panel_engine_patch_safety_rerun",',
                "]",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_generated_handoff_repro_literal_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="generated_handoff_repro_literal_audit_") as tmpdir:
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
            (output_dir / "generated_handoff_repro_literal_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "generated_handoff_repro_literal_audit_v1.csv")
        summary = pd.read_csv(
            output_dir / "generated_handoff_repro_literal_audit_summary_v1.csv"
        )
        note = (output_dir / "generated_handoff_repro_literal_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["path_portability_total_matches"] == 5, payload)
        assert_true(payload["generated_handoff_repro_literal_rows"] == 5, payload)
        assert_true(payload["latest_handoff_manifest_repro_rows"] == 2, payload)
        assert_true(payload["evidence_manifest_repro_rows"] == 1, payload)
        assert_true(payload["episode_note_repro_rows"] == 1, payload)
        assert_true(payload["validation_output_literal_rows"] == 1, payload)
        assert_true(payload["manifestized_rebuild_candidate_rows"] == 3, payload)
        assert_true(payload["manual_literal_edit_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["audit_complete"] == 1, payload)

        roles = set(detail["literal_role"])
        assert_true("latest_evidence_handoff_manifest_repro" in roles, detail.to_dict("records"))
        assert_true("evidence_pack_manifest_repro" in roles, detail.to_dict("records"))
        assert_true("generated_note_repo_root_repro" in roles, detail.to_dict("records"))
        assert_true("validation_output_dir_literal" in roles, detail.to_dict("records"))
        assert_true("Do not edit individual generated temp literals by hand" in note, note)
        assert_true(
            int(summary[summary["key"].eq("generated_handoff_repro_literal_rows")]["count"].iloc[0])
            == 5,
            summary.to_dict("records"),
        )

    print("smoke ok: generated_handoff_repro_literal_audit_v1")


if __name__ == "__main__":
    main()

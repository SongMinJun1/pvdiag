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
    repo_abs = "/Users" + "/b9gc/pvdiag"
    docs = root / "docs"
    research = root / "research" / "prognostics"
    docs.mkdir(parents=True)
    research.mkdir(parents=True)
    (docs / "historical.md").write_text(
        "\n".join(
            [
                "# Historical Fixture",
                f"- Evidence output: `{private_tmp}/old_branch/evidence.csv`",
                f"- Repro root: `{repo_abs}/research/prognostics/build_old_packet.py`",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (research / "build_handoff.py").write_text(
        "\n".join(
            [
                "REPRO = (",
                f'    "python3 research/prognostics/build_old_packet.py --input {private_tmp}/old_branch/evidence.csv"',
                ")",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder = repo_root / "research/prognostics/build_p2_historical_reference_boundary_audit_v1.py"
    with tempfile.TemporaryDirectory(prefix="p2_historical_boundary_audit_") as tmpdir:
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
            (output_dir / "p2_historical_reference_boundary_audit_v1.json").read_text(
                encoding="utf-8"
            )
        )
        detail = pd.read_csv(output_dir / "p2_historical_reference_boundary_audit_v1.csv")
        summary = pd.read_csv(
            output_dir / "p2_historical_reference_boundary_audit_summary_v1.csv"
        )
        note = (output_dir / "p2_historical_reference_boundary_audit_note_v1.md").read_text(
            encoding="utf-8"
        )

        assert_true(payload["path_portability_total_matches"] == 3, payload)
        assert_true(payload["p2_historical_total_rows"] == 3, payload)
        assert_true(payload["p2_historical_evidence_rows"] == 1, payload)
        assert_true(payload["p2_historical_repro_rows"] == 2, payload)
        assert_true(payload["stable_replacement_required_rows"] == 1, payload)
        assert_true(payload["refresh_only_when_touching_doc_rows"] == 1, payload)
        assert_true(payload["current_handoff_rebuild_candidate_rows"] == 1, payload)
        assert_true(payload["immediate_bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["operator_facing_change_allowed_rows"] == 0, payload)
        assert_true(payload["historical_boundary_complete"] == 1, payload)

        classes = set(detail["boundary_class"])
        assert_true("historical_evidence_provenance_pointer" in classes, detail.to_dict("records"))
        assert_true("historical_doc_repro_reference" in classes, detail.to_dict("records"))
        assert_true("generated_handoff_repro_literal" in classes, detail.to_dict("records"))
        assert_true("bulk historical path cleanup" in note, note)
        assert_true(
            int(summary[summary["key"].eq("p2_historical_total_rows")]["count"].iloc[0]) == 3,
            summary.to_dict("records"),
        )

    print("smoke ok: p2_historical_reference_boundary_audit_v1")


if __name__ == "__main__":
    main()

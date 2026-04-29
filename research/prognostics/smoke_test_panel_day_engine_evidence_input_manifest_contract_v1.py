#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


DETAIL_NAME = "panel_day_engine_evidence_input_manifest_contract_v1.csv"
SUMMARY_NAME = "panel_day_engine_evidence_input_manifest_contract_summary_v1.csv"
NOTE_NAME = "panel_day_engine_evidence_input_manifest_contract_note_v1.md"
JSON_NAME = "panel_day_engine_evidence_input_manifest_contract_v1.json"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise AssertionError(message)


def write_file(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fixture(repo_root: Path) -> None:
    private_tmp = "/private" + "/tmp"
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py",
        [
            "#!/usr/bin/env python3",
            f'BR079_ROOT_DEFAULT = "{private_tmp}/panel_day_engine_algorithm_evolution_map_br079_check"',
            f'BR080_ROOT_DEFAULT = "{private_tmp}/panel_day_engine_subtype_truth_expansion_backlog_br080_check"',
            f'BR081_ROOT_DEFAULT = "{private_tmp}/panel_day_engine_episode_truth_map_br081_check"',
            f'BR082_ROOT_DEFAULT = "{private_tmp}/panel_day_engine_episode_truth_review_packet_br082_check"',
            "NOTE = '''",
            f"python3 research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py --repo-root {private_tmp}/pvdiag_postmerge_j --output-dir {{output_dir}}",
            "'''",
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_exact_family_closure_readiness_review_v1.py",
        [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f'LOCAL_INPUT = Path("{private_tmp}/local_morphology_exact_seed_search_check.csv")',
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_evidence_manifest_v1.py",
        [
            "#!/usr/bin/env python3",
            f'TEMP_PREFIXES = ["{private_tmp}/"]',
        ],
    )


def main() -> None:
    source_repo = Path(__file__).resolve().parents[2]
    builder = source_repo / "research/prognostics/build_panel_day_engine_evidence_input_manifest_contract_v1.py"
    with tempfile.TemporaryDirectory(prefix="panel_day_engine_evidence_input_manifest_contract_smoke_") as tmpdir:
        fixture_repo = Path(tmpdir) / "repo"
        output_dir = Path(tmpdir) / "out"
        write_fixture(fixture_repo)

        proc = subprocess.run(
            [
                sys.executable,
                str(builder),
                "--repo-root",
                str(fixture_repo),
                "--output-dir",
                str(output_dir),
            ],
            cwd=source_repo,
            text=True,
            capture_output=True,
            check=False,
        )
        assert_true(proc.returncode == 0, proc.stderr or proc.stdout)

        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))
        detail = pd.read_csv(output_dir / DETAIL_NAME, encoding="utf-8-sig")
        summary = pd.read_csv(output_dir / SUMMARY_NAME, encoding="utf-8-sig")
        note = (output_dir / NOTE_NAME).read_text(encoding="utf-8")

        assert_true(payload["workflow_lane"] == "panel_day_engine_evidence", payload)
        assert_true(payload["evidence_reference_rows"] == 7, payload)
        assert_true(payload["manifest_required_rows"] == 5, payload)
        assert_true(payload["explicit_input_supported_rows"] == 5, payload)
        assert_true(payload["literal_or_repro_only_rows"] == 2, payload)
        assert_true(payload["unmapped_required_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true(len(detail) == 7, detail.to_dict("records"))
        assert_true(
            {
                "--br079-root",
                "--br080-root",
                "--br081-root",
                "--br082-root",
                "--local-morphology-input",
            }.issubset(set(detail["consumer_input_flag"].fillna(""))),
            detail.to_dict("records"),
        )
        assert_true(
            int(summary[summary["key"].eq("unmapped_required_rows")]["count"].iloc[0]) == 0,
            summary.to_dict("records"),
        )
        assert_true("contract table only" in note, note)
        assert_true("Existing panel-day evidence builders are not rewritten" in note, note)

    print(json.dumps({"smoke": "ok", "evidence_reference_rows": payload["evidence_reference_rows"]}))


if __name__ == "__main__":
    main()

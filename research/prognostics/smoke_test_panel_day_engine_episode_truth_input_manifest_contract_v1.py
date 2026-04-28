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


def write_file(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fixture(repo_root: Path) -> None:
    private_tmp = "/private" + "/tmp"
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py",
        [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f'TRACE_INPUT = Path("{private_tmp}/panel_day_engine_episode_truth_source_trace_audit_br086_check/")',
            f'INDEX_INPUT = Path("{private_tmp}/panel_day_engine_episode_truth_evidence_attachment_br085_check/")',
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py",
        [
            "#!/usr/bin/env python3",
            "NOTE = '''",
            f"Keep repro prose realistic: --repo-root {private_tmp}/pvdiag_postmerge_j --output-dir {{output_dir}}",
            "'''",
        ],
    )


def main() -> None:
    source_repo = Path(__file__).resolve().parents[2]
    builder = source_repo / "research/prognostics/build_panel_day_engine_episode_truth_input_manifest_contract_v1.py"
    with tempfile.TemporaryDirectory(prefix="episode_truth_input_manifest_contract_smoke_") as tmpdir:
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

        payload = json.loads((output_dir / "panel_day_engine_episode_truth_input_manifest_contract_v1.json").read_text())
        detail = pd.read_csv(output_dir / "panel_day_engine_episode_truth_input_manifest_contract_v1.csv")
        summary = pd.read_csv(output_dir / "panel_day_engine_episode_truth_input_manifest_contract_summary_v1.csv")
        note = (output_dir / "panel_day_engine_episode_truth_input_manifest_contract_note_v1.md").read_text(encoding="utf-8")

        assert_true(payload["episode_truth_reference_rows"] == 3, payload)
        assert_true(len(detail) == 3, detail.to_dict("records"))
        assert_true(
            payload["episode_truth_reference_rows"]
            == int(summary[summary["key"].eq("episode_truth_reference_rows")]["count"].iloc[0]),
            payload,
        )
        assert_true(payload["manifest_required_rows"] == 2, payload)
        assert_true(payload["explicit_input_supported_rows"] == 2, payload)
        assert_true(payload["literal_or_repro_only_rows"] == 1, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true({"--trace-input", "--index-input"}.issubset(set(detail["consumer_input_flag"])), detail.to_dict("records"))
        assert_true("contract table only" in note, note)

    print(
        json.dumps(
            {"smoke": "ok", "episode_truth_reference_rows": int(payload["episode_truth_reference_rows"])},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

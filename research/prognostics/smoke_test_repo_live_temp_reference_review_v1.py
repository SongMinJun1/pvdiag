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
        repo_root / "research/prognostics/build_panel_day_engine_static_input_v1.py",
        [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f'INPUT_DEFAULT = Path("{private_tmp}/static_input_check/input.csv")',
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_static_dir_v1.py",
        [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f'DIR_INPUT = Path("{private_tmp}/static_dir_check/")',
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_note_repro_v1.py",
        [
            "#!/usr/bin/env python3",
            "NOTE = '''",
            f"Repro command after this prose marker keeps context realistic: --repo-root {private_tmp}/pvdiag_postmerge_j --output-dir {{output_dir}}",
            "'''",
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_evidence_manifest_v1.py",
        [
            "#!/usr/bin/env python3",
            f'temp_prefixes = ("{private_tmp}/", "/tmp/")',
        ],
    )
    write_file(
        repo_root / "research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py",
        [
            "#!/usr/bin/env python3",
            "from pathlib import Path",
            f'RUNTIME_RESULT = Path("{private_tmp}/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv")',
        ],
    )


def main() -> None:
    source_repo = Path(__file__).resolve().parents[2]
    builder = source_repo / "research/prognostics/build_repo_live_temp_reference_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="repo_live_temp_reference_review_smoke_") as tmpdir:
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

        payload = json.loads((output_dir / "repo_live_temp_reference_review_v1.json").read_text())
        detail = pd.read_csv(output_dir / "repo_live_temp_reference_review_v1.csv")
        summary = pd.read_csv(output_dir / "repo_live_temp_reference_review_summary_v1.csv")
        note = (output_dir / "repo_live_temp_reference_review_note_v1.md").read_text(encoding="utf-8")

        assert_true(payload["live_temp_reference_rows"] == 5, payload)
        assert_true(len(detail) == 5, detail.to_dict("records"))
        assert_true(
            payload["live_temp_reference_rows"]
            == int(summary[summary["key"].eq("live_temp_reference_rows")]["count"].iloc[0]),
            payload,
        )
        expected_kinds = {
            "static_upstream_artifact_input",
            "static_upstream_directory_input",
            "embedded_note_repro_command",
            "intentional_temp_detection_literal",
            "runtime_result_bundle_input",
        }
        assert_true(set(detail["live_reference_kind"]) == expected_kinds, detail.to_dict("records"))
        assert_true(payload["requires_manifest_or_explicit_input_rows"] == 3, payload)
        assert_true(payload["literal_or_repro_only_rows"] == 2, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["bulk_rewrite_allowed_rows"] == 0, payload)
        assert_true("manifest or explicit input" in note, note)

    print(json.dumps({"smoke": "ok", "live_temp_reference_rows": int(payload["live_temp_reference_rows"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

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


def write_fixture(repo_root: Path) -> None:
    script = repo_root / "research/prognostics/build_mlpe_field_trial_fixture_output_v1.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "\n".join(
            [
                "#!/usr/bin/env python3",
                "from __future__ import annotations",
                "",
                "import argparse",
                "",
                'DEFAULT_OUTPUT_DIR = "/private/tmp/mlpe_field_trial_fixture_output_br168_check"',
                'DEFAULT_LABEL_INPUT = "/private/tmp/mlpe_field_trial_fixture_label_input.csv"',
                "",
                "def main() -> None:",
                "    parser = argparse.ArgumentParser()",
                '    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR)',
                '    parser.add_argument("--label-input", default=DEFAULT_LABEL_INPUT)',
                "    parser.parse_args()",
                "",
                'if __name__ == "__main__":',
                "    main()",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    source_repo = Path(__file__).resolve().parents[2]
    builder = source_repo / "research/prognostics/build_mlpe_field_trial_output_default_review_v1.py"
    with tempfile.TemporaryDirectory(prefix="mlpe_output_default_review_smoke_") as tmpdir:
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

        payload = json.loads((output_dir / "mlpe_field_trial_output_default_review_v1.json").read_text())
        detail = pd.read_csv(output_dir / "mlpe_field_trial_output_default_review_v1.csv")
        summary = pd.read_csv(output_dir / "mlpe_field_trial_output_default_review_summary_v1.csv")
        note = (output_dir / "mlpe_field_trial_output_default_review_note_v1.md").read_text(encoding="utf-8")

        assert_true(payload["output_default_rows"] == 1, payload)
        assert_true(len(detail) == 1, detail.to_dict("records"))
        assert_true(payload["output_default_rows"] == int(summary[summary["key"].eq("output_default_rows")]["count"].iloc[0]), payload)
        assert_true(payload["cli_output_dir_override_rows"] == 1, payload)
        assert_true(payload["missing_cli_output_dir_override_rows"] == 0, payload)
        assert_true(payload["input_dependency_rows"] == 0, payload)
        assert_true(payload["generated_dependency_rows"] == 0, payload)
        assert_true(payload["runtime_semantic_change_allowed_rows"] == 0, payload)
        assert_true(payload["mass_rewrite_recommended_rows"] == 0, payload)
        assert_true(detail["default_variable"].iloc[0] == "DEFAULT_OUTPUT_DIR", detail.to_dict("records"))
        assert_true(int(detail["writes_only_default_flag"].iloc[0]) == 1, detail.to_dict("records"))
        assert_true("--output-dir" in note, note)

    print(json.dumps({"smoke": "ok", "output_default_rows": int(payload["output_default_rows"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path


DETAIL_NAME = "repo_path_portability_detail_v1.csv"
SUMMARY_NAME = "repo_path_portability_summary_v1.csv"
FILE_KIND_NAME = "repo_path_portability_file_kind_v1.csv"
NOTE_NAME = "repo_path_portability_note_v1.md"
JSON_NAME = "repo_path_portability_summary_v1.json"


def assert_true(condition: bool, message: object) -> None:
    if not condition:
        raise SystemExit(str(message))


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def build_fixture(repo_root: Path) -> None:
    write_text(
        repo_root / "docs" / "runbook.md",
        "Use /Users/b9gc/pvdiag/docs/runbook.md as a repo absolute example.\n",  # pp-self
    )
    write_text(
        repo_root / "research" / "prognostics" / "builder.py",
        "TMP = '/private/tmp/path_portability_fixture/output.csv'\n",  # pp-self
    )
    write_text(
        repo_root / "research" / "prognostics" / "smoke_test_builder.py",
        "FIXTURE = '/private/tmp/path_portability_fixture/smoke.csv'\n",  # pp-self
    )
    write_text(
        repo_root / "pv_ae" / "panel_day_engine.py",
        "WORKTREE = '/Users/b9gc/pvdiag_worktrees/old_fixture_branch'\n",  # pp-self
    )
    write_text(
        repo_root
        / "release"
        / "conalog_full_runtime_v1"
        / "package"
        / "runtime"
        / "windows_x64"
        / "python"
        / "excluded.py",
        "EXCLUDED = '/private/tmp/should_not_be_scanned'\n",  # pp-self
    )
    write_text(
        repo_root / "release" / "conalog_full_runtime_v1" / "package" / "app" / "run.py",
        "print('package surface without absolute path')\n",
    )
    write_text(
        repo_root / "research" / "prognostics" / "self_noise.py",
        "PATTERN = '/Users/b9gc/pvdiag_worktrees/self_noise_fixture'  # pp-self\n",
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "research" / "prognostics" / "build_repo_path_portability_audit_v1.py"

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_repo_path_portability_audit_v1.py",
            "research/prognostics/smoke_test_repo_path_portability_audit_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="repo_path_portability_") as tmp_dir:
        fixture_root = Path(tmp_dir) / "fixture_repo"
        output_dir = Path(tmp_dir) / "out"
        fixture_root.mkdir(parents=True, exist_ok=True)
        build_fixture(fixture_root)

        completed = run(
            [
                sys.executable,
                str(script),
                "--repo-root",
                str(fixture_root),
                "--output-dir",
                str(output_dir),
            ],
            repo_root,
        )
        assert_true(completed.returncode == 0, completed.stderr or completed.stdout)

        detail = read_csv(output_dir / DETAIL_NAME)
        summary = read_csv(output_dir / SUMMARY_NAME)
        file_kind = read_csv(output_dir / FILE_KIND_NAME)
        note = (output_dir / NOTE_NAME).read_text(encoding="utf-8")
        payload = json.loads((output_dir / JSON_NAME).read_text(encoding="utf-8"))

        match_counts = {row["key"]: int(row["count"]) for row in summary if row["kind"] == "match_kind"}
        role_counts = {row["key"]: int(row["count"]) for row in summary if row["kind"] == "match_role"}
        priority_counts = {
            row["key"]: int(row["count"])
            for row in summary
            if row["kind"] == "triage_priority"
        }
        skipped_counts = {row["key"]: int(row["count"]) for row in summary if row["kind"] == "skipped"}
        file_kind_pairs = {(row["file_kind"], row["match_kind"]) for row in file_kind}
        roles = {(row["match_kind"], row["relative_path"]): row["match_role"] for row in detail}
        priorities = {
            (row["match_kind"], row["relative_path"]): row["triage_priority"]
            for row in detail
        }

        assert_true(len(detail) == 4, detail)
        assert_true(match_counts == {"private_tmp": 2, "repo_absolute": 1, "worktree_absolute": 1}, match_counts)
        assert_true(
            roles
            == {
                ("private_tmp", "research/prognostics/builder.py"): "temp_reference_in_research_code",
                (
                    "private_tmp",
                    "research/prognostics/smoke_test_builder.py",
                ): "test_fixture_temp_reference",
                ("repo_absolute", "docs/runbook.md"): "repo_doc_absolute_reference",
                ("worktree_absolute", "pv_ae/panel_day_engine.py"): "stale_worktree_reference",
            },
            roles,
        )
        assert_true(
            priority_counts
            == {
                "p0_stale_worktree": 1,
                "p1_live_temp_reference": 1,
                "p3_test_fixture_reference": 1,
                "p3_doc_reference": 1,
            },
            priority_counts,
        )
        assert_true(
            priorities[("worktree_absolute", "pv_ae/panel_day_engine.py")] == "p0_stale_worktree",
            priorities,
        )
        assert_true(
            not any(row["relative_path"].endswith("self_noise.py") for row in detail),
            detail,
        )
        assert_true(skipped_counts.get("excluded_runtime_payload", 0) == 1, skipped_counts)
        assert_true(("repo_doc", "repo_absolute") in file_kind_pairs, file_kind)
        assert_true(("research_prognostics", "private_tmp") in file_kind_pairs, file_kind)
        assert_true(("source_engine", "worktree_absolute") in file_kind_pairs, file_kind)
        assert_true("Do not bulk rewrite" in note, note)
        assert_true("## Triage Roles" in note, note)
        assert_true(role_counts["stale_worktree_reference"] == 1, role_counts)
        assert_true(payload["match_kind_counts"]["worktree_absolute"] == 1, payload)
        assert_true(payload["match_role_counts"]["repo_doc_absolute_reference"] == 1, payload)
        assert_true(payload["match_role_counts"]["test_fixture_temp_reference"] == 1, payload)
        assert_true(payload["triage_priority_counts"]["p0_stale_worktree"] == 1, payload)


if __name__ == "__main__":
    main()

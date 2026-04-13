#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_common_panel_table(share: Path) -> None:
    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {"site": "siteA", "panel_id": "panel_1"},
            {"site": "siteA", "panel_id": "panel_2"},
            {"site": "siteB", "panel_id": "panel_3"},
        ],
        ["site", "panel_id"],
    )


def build_attachable_fixture(root: Path) -> None:
    share = root / "_share"
    docs = root / "docs" / "reports"
    gpvs_out = root / "data" / "gpvs" / "out"
    share.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)

    build_common_panel_table(share)

    write_csv(
        share / "gpvs_fault_family_eval_cases.csv",
        [
            {
                "site": "siteA",
                "panel_id": "panel_1",
                "truth_fault_family": "electrical_fault_like",
                "pred_fault_family": "electrical_fault_like",
                "prediction_source": "critical_phenotype_v3",
                "fallback_rule_used": "resolved_by_critical_phenotype_v3",
                "error_type": "correct",
                "vendor_fault_family": "diode_like",
            },
            {
                "site": "siteA",
                "panel_id": "panel_2",
                "truth_fault_family": "group_or_inverter_side_like",
                "pred_fault_family": "group_or_inverter_side_like",
                "prediction_source": "strict_day_core_fallback",
                "fallback_rule_used": "same_day_group_collapse",
                "error_type": "correct",
                "vendor_fault_family": "group_or_inverter_side_like",
            },
            {
                "site": "siteZ",
                "panel_id": "panel_extra",
                "truth_fault_family": "none_visible",
                "pred_fault_family": "none_visible",
                "prediction_source": "strict_day_core_fallback",
                "fallback_rule_used": "fallback_none_visible",
                "error_type": "correct",
                "vendor_fault_family": "none_visible",
            },
        ],
        [
            "site",
            "panel_id",
            "truth_fault_family",
            "pred_fault_family",
            "prediction_source",
            "fallback_rule_used",
            "error_type",
            "vendor_fault_family",
        ],
    )

    write_csv(
        share / "gpvs_fault_family_f1_summary.csv",
        [{"evaluation_mode": "closed_world", "class_label": "electrical_fault_like", "macro_f1": 0.9}],
        ["evaluation_mode", "class_label", "macro_f1"],
    )
    write_csv(
        share / "gpvs_fault_family_confusion.csv",
        [{"truth_fault_family": "electrical_fault_like", "pred_fault_family": "electrical_fault_like", "row_count": 1}],
        ["truth_fault_family", "pred_fault_family", "row_count"],
    )
    write_csv(
        gpvs_out / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [{"fault_type": "F1", "sid": 0, "score": "dtw_like", "auc": 0.9, "ap": 0.8, "f1_fpr1": 0.7}],
        ["fault_type", "sid", "score", "auc", "ap", "f1_fpr1"],
    )
    write_csv(
        gpvs_out / "EXTERNAL_GPVS_METRICS.csv",
        [{"score": "dtw_like", "auc": 0.9, "ap": 0.8, "f1_fpr1": 0.7}],
        ["score", "auc", "ap", "f1_fpr1"],
    )
    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        [{"sample_id": "F1::0", "source_id": "F1", "window_idx": 0, "fault_type": "F1", "level_drop_like": 0.9}],
        ["sample_id", "source_id", "window_idx", "fault_type", "level_drop_like"],
    )
    (docs / "gpvs_final_summary.md").write_text("# gpvs summary\n", encoding="utf-8")


def build_non_attachable_fixture(root: Path) -> None:
    share = root / "_share"
    docs = root / "docs" / "reports"
    gpvs_out = root / "data" / "gpvs" / "out"
    share.mkdir(parents=True, exist_ok=True)
    docs.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)

    build_common_panel_table(share)

    write_csv(
        gpvs_out / "EXTERNAL_GPVS_BYTYPE_METRICS.csv",
        [{"fault_type": "F1", "sid": 0, "score": "dtw_like", "auc": 0.9, "ap": 0.8, "f1_fpr1": 0.7}],
        ["fault_type", "sid", "score", "auc", "ap", "f1_fpr1"],
    )
    write_csv(
        gpvs_out / "EXTERNAL_GPVS_METRICS.csv",
        [{"score": "dtw_like", "auc": 0.9, "ap": 0.8, "f1_fpr1": 0.7}],
        ["score", "auc", "ap", "f1_fpr1"],
    )
    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        [{"sample_id": "F1::0", "source_id": "F1", "window_idx": 0, "fault_type": "F1", "level_drop_like": 0.9}],
        ["sample_id", "source_id", "window_idx", "fault_type", "level_drop_like"],
    )
    (docs / "gpvs_final_summary.md").write_text("# gpvs summary\n", encoding="utf-8")


def run_builder_and_load(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_panel_attach_audit_v1.py"
    result = run([sys.executable, str(build_script), "--root", str(root)], cwd=repo_root)
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or "builder failed")

    share = root / "_share"
    inventory_df = pd.read_csv(share / "panel_day_engine_gpvs_panel_attach_inventory_v1.csv", low_memory=False, encoding="utf-8-sig")
    feasibility_df = pd.read_csv(share / "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv", low_memory=False, encoding="utf-8-sig")
    candidates_path = share / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv"
    candidates_df = pd.read_csv(candidates_path, low_memory=False, encoding="utf-8-sig")
    return inventory_df, feasibility_df, candidates_df


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_panel_attach_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(__file__), doraise=True)

    official_outputs = [
        repo_root / "_share" / "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        repo_root / "_share" / "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
        repo_root / "_share" / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="tmp_gpvs_attach_yes_") as tmpdir:
        root = Path(tmpdir)
        build_attachable_fixture(root)
        inventory_df, feasibility_df, candidates_df = run_builder_and_load(root)

        assert_true(not inventory_df.empty, "inventory rows must be emitted")
        attach_row = inventory_df.loc[inventory_df["경로"] == "_share/gpvs_fault_family_eval_cases.csv"]
        assert_true(not attach_row.empty, "attachable eval cases file must be inventoried")
        assert_true(int(attach_row.iloc[0]["panel_attach_candidate_flag"]) == 1, "eval cases should be an attach candidate")
        assert_true(int(attach_row.iloc[0]["overlap_panel_count"]) == 2, "attach overlap should be 2")
        assert_true(feasibility_df.iloc[0]["GPVS_패널별_직접판정_가능여부"] == "가능", "attachable fixture should be feasible")
        assert_true(feasibility_df.iloc[0]["최선_후보_파일"] == "_share/gpvs_fault_family_eval_cases.csv", "best candidate path mismatch")
        assert_true(len(candidates_df) == 2, "attachable fixture should emit 2 matched panel rows")
        assert_true(set(candidates_df["GPVS_참고유형_ko"]) == {"전기적 고장 계열", "공통원인/인버터측 계열"}, "type mapping mismatch")

    with tempfile.TemporaryDirectory(prefix="tmp_gpvs_attach_no_") as tmpdir:
        root = Path(tmpdir)
        build_non_attachable_fixture(root)
        inventory_df, feasibility_df, candidates_df = run_builder_and_load(root)

        assert_true(not inventory_df.empty, "inventory rows must still emit in non-attachable case")
        assert_true(feasibility_df.iloc[0]["GPVS_패널별_직접판정_가능여부"] == "불가", "non-attachable fixture should be infeasible")
        assert_true(list(candidates_df.columns) == CANDIDATE_COLS, "empty candidate file must preserve headers")
        assert_true(candidates_df.empty, "non-attachable fixture should emit header-only candidates file")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "smoke test must not modify official outputs")


CANDIDATE_COLS = [
    "site",
    "panel_id",
    "GPVS_참고유형_ko",
    "source_path",
    "source_key_ko",
    "비고_ko",
]


if __name__ == "__main__":
    main()

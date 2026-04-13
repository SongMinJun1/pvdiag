#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import py_compile
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    assert_true(spec is not None and spec.loader is not None, f"failed to load module: {path.name}")
    spec.loader.exec_module(module)
    return module


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_project_eval_matrix_v1.csv",
        [
            {
                "eval_scope": "step1_taxonomy",
                "eval_part_name": "taxonomy_support",
                "metric_kind": "structural_coverage_metric",
                "unit_type": "family",
                "positive_set_name": "bucket_a",
                "negative_set_name": "",
                "target_name": "bucket_a",
                "support_positive": 3,
                "support_negative": "",
                "tp": "",
                "fp": "",
                "fn": "",
                "tn": "",
                "recall": "",
                "precision": "",
                "f1": "",
                "note_ko": "structural row",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "eval_part_name": "precursor",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "pos",
                "negative_set_name": "neg",
                "target_name": "perfect_but_tiny",
                "support_positive": 3,
                "support_negative": 10,
                "tp": 3,
                "fp": 0,
                "fn": 0,
                "tn": 10,
                "recall": 1.0,
                "precision": 1.0,
                "f1": 1.0,
                "note_ko": "tiny support",
            },
            {
                "eval_scope": "step3_precursor_performance",
                "eval_part_name": "precursor",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "pos",
                "negative_set_name": "neg",
                "target_name": "usable_low_support",
                "support_positive": 6,
                "support_negative": 12,
                "tp": 4,
                "fp": 1,
                "fn": 2,
                "tn": 11,
                "recall": 0.6666666667,
                "precision": 0.8,
                "f1": 0.7272727273,
                "note_ko": "low support",
            },
            {
                "eval_scope": "step4_abrupt_no_precursor",
                "eval_part_name": "abrupt",
                "metric_kind": "true_case_metric",
                "unit_type": "case",
                "positive_set_name": "pos",
                "negative_set_name": "neg",
                "target_name": "pure_abrupt_target",
                "support_positive": 3,
                "support_negative": 8,
                "tp": 3,
                "fp": 1,
                "fn": 0,
                "tn": 7,
                "recall": 1.0,
                "precision": 0.75,
                "f1": 0.8571428571,
                "note_ko": "benchmark reset pure abrupt support 3",
            },
            {
                "eval_scope": "operator_policy_proxy",
                "eval_part_name": "policy",
                "metric_kind": "retrospective_proxy_metric",
                "unit_type": "panel",
                "positive_set_name": "proxy_pos",
                "negative_set_name": "proxy_neg",
                "target_name": "workflow_default",
                "support_positive": 10,
                "support_negative": 10,
                "tp": 7,
                "fp": 3,
                "fn": 3,
                "tn": 7,
                "recall": 0.7,
                "precision": 0.7,
                "f1": 0.7,
                "note_ko": "proxy",
            },
        ],
        [
            "eval_scope",
            "eval_part_name",
            "metric_kind",
            "unit_type",
            "positive_set_name",
            "negative_set_name",
            "target_name",
            "support_positive",
            "support_negative",
            "tp",
            "fp",
            "fn",
            "tn",
            "recall",
            "precision",
            "f1",
            "note_ko",
        ],
    )
    write_csv(
        share / "panel_day_engine_project_eval_matrix_summary_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "best_target_name": "", "best_f1": "", "best_recall": "", "best_precision": "", "note_ko": "n/a"},
            {"eval_scope": "step3_precursor_performance", "best_target_name": "usable_low_support", "best_f1": 0.7272727273, "best_recall": 0.6666666667, "best_precision": 0.8, "note_ko": "summary"},
            {"eval_scope": "step4_abrupt_no_precursor", "best_target_name": "pure_abrupt_target", "best_f1": 0.8181818182, "best_recall": 0.75, "best_precision": 0.9, "note_ko": "summary"},
            {"eval_scope": "operator_policy_proxy", "best_target_name": "workflow_default", "best_f1": 0.7, "best_recall": 0.7, "best_precision": 0.7, "note_ko": "summary"},
        ],
        ["eval_scope", "best_target_name", "best_f1", "best_recall", "best_precision", "note_ko"],
    )
    write_csv(
        share / "panel_day_engine_project_eval_notes_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "why_prf_is_valid_or_not": "not classifier", "caveat_ko": "coverage only"},
            {"eval_scope": "step3_precursor_performance", "why_prf_is_valid_or_not": "valid", "caveat_ko": "tiny support can mislead"},
            {"eval_scope": "step4_abrupt_no_precursor", "why_prf_is_valid_or_not": "valid", "caveat_ko": "read interval too"},
            {"eval_scope": "operator_policy_proxy", "why_prf_is_valid_or_not": "proxy", "caveat_ko": "proxy only"},
        ],
        ["eval_scope", "why_prf_is_valid_or_not", "caveat_ko"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    builder_path = repo_root / "research/prognostics/build_panel_day_engine_project_eval_reliability_audit_v1.py"
    builder_mod = load_module(builder_path, "project_eval_reliability_builder")

    official_paths = [
        repo_root / "_share" / "panel_day_engine_project_eval_reliability_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_reliability_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_project_eval_freeze_candidates_v1.csv",
    ]
    official_digests_before = {path: file_digest(path) for path in official_paths}

    py_compile.compile(str(builder_path), doraise=True)
    py_compile.compile(str(Path(__file__).resolve()), doraise=True)

    with tempfile.TemporaryDirectory(prefix="project_eval_reliability_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture(tmp_root)
        result = run([sys.executable, str(builder_path), "--root", str(tmp_root)], repo_root)
        assert_true(result.returncode == 0, result.stderr or result.stdout)

        reliability = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_reliability_v1.csv",
            encoding="utf-8-sig",
        )
        summary = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_reliability_summary_v1.csv",
            encoding="utf-8-sig",
        )
        freeze = pd.read_csv(
            tmp_root / "_share" / "panel_day_engine_project_eval_freeze_candidates_v1.csv",
            encoding="utf-8-sig",
        )

        assert_true(reliability.columns.tolist() == builder_mod.RELIABILITY_COLS, "reliability schema mismatch")
        assert_true(summary.columns.tolist() == builder_mod.RELIABILITY_SUMMARY_COLS, "summary schema mismatch")
        assert_true(freeze.columns.tolist() == builder_mod.FREEZE_CANDIDATES_COLS, "freeze schema mismatch")

        structural_row = reliability.loc[reliability["eval_scope"].astype(str).eq("step1_taxonomy")].iloc[0]
        assert_true(structural_row["reliability_class"] == "structural_only", "structural reliability_class mismatch")
        assert_true(structural_row["freeze_recommendation"] == "freeze_with_caution", "structural freeze recommendation mismatch")
        assert_true(pd.isna(structural_row["recall"]), "structural recall should be blank")
        assert_true(pd.isna(structural_row["precision"]), "structural precision should be blank")

        underpowered_row = reliability.loc[reliability["target_name"].astype(str).eq("perfect_but_tiny")].iloc[0]
        assert_true(underpowered_row["reliability_class"] == "underpowered", "underpowered classification mismatch")
        assert_true(underpowered_row["freeze_recommendation"] == "do_not_freeze", "underpowered freeze mismatch")
        assert_true(float(underpowered_row["recall_ci_low"]) > 0.4, "Wilson interval should be computed for recall")
        assert_true(float(underpowered_row["precision_ci_high"]) == 1.0, "Wilson interval upper bound mismatch")

        low_support_row = reliability.loc[reliability["target_name"].astype(str).eq("usable_low_support")].iloc[0]
        assert_true(low_support_row["reliability_class"] == "low_support", "low_support classification mismatch")
        assert_true(low_support_row["freeze_recommendation"] == "freeze_with_caution", "low_support freeze mismatch")

        abrupt_row = reliability.loc[reliability["target_name"].astype(str).eq("pure_abrupt_target")].iloc[0]
        assert_true(abrupt_row["reliability_class"] == "underpowered", "corrected pure abrupt classification mismatch")
        assert_true(abrupt_row["freeze_recommendation"] == "do_not_freeze", "corrected pure abrupt freeze mismatch")
        assert_true(
            "pure abrupt benchmark positive support는 3" in abrupt_row["reliability_reason_ko"]
            and "c42997" in abrupt_row["reliability_reason_ko"]
            and "pure abrupt benchmark에서는 제외된다" in abrupt_row["reliability_reason_ko"],
            "corrected pure abrupt reason should mention the benchmark-reset abrupt basis and c429 exclusion",
        )

        proxy_row = reliability.loc[reliability["eval_scope"].astype(str).eq("operator_policy_proxy")].iloc[0]
        assert_true(proxy_row["reliability_class"] == "proxy_only", "proxy reliability_class mismatch")
        assert_true(proxy_row["freeze_recommendation"] == "freeze_with_caution", "proxy freeze mismatch")

        freeze_step3 = freeze.loc[freeze["eval_scope"].astype(str).eq("step3_precursor_performance")].iloc[0]
        assert_true(
            str(freeze_step3["recommended_target_name"]) == "usable_low_support",
            "step3 freeze candidate should skip do_not_freeze row",
        )
        freeze_step4 = freeze.loc[freeze["eval_scope"].astype(str).eq("step4_abrupt_no_precursor")].iloc[0]
        assert_true(
            normalize_text(freeze_step4["recommended_target_name"]) == "",
            "step4 corrected underpowered scope should not recommend a freeze target",
        )

        summary_step3 = summary.loc[summary["eval_scope"].astype(str).eq("step3_precursor_performance")].iloc[0]
        assert_true(int(summary_step3["underpowered_count"]) == 1, "summary underpowered_count mismatch")
        assert_true(int(summary_step3["low_support_count"]) == 1, "summary low_support_count mismatch")
        assert_true(int(summary_step3["freeze_with_caution_count"]) == 1, "summary freeze_with_caution_count mismatch")
        assert_true(int(summary_step3["do_not_freeze_count"]) == 1, "summary do_not_freeze_count mismatch")

    official_digests_after = {path: file_digest(path) for path in official_paths}
    assert_true(
        official_digests_after == official_digests_before,
        "smoke test must not modify official project eval reliability outputs under repository _share",
    )

    print("smoke_test_panel_day_engine_project_eval_reliability_audit_v1.py: PASS")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def build_fixture_root(tmp_root: Path) -> None:
    write_text(tmp_root / "pv_ae" / "panel_day_engine.py", "# synthetic panel_day_engine core\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_LOCAL_PRECURSOR_ELIGIBILITY_AUDIT_V1.md", "# eligibility\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_RUN_FEATURE_SEPARABILITY_AUDIT_V1.md", "# separability\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_RUN_LABEL_PACK_V1.md", "# label pack\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_RUN_RANKER_V0_AUDIT.md", "# run ranker v0\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_RUN_RANKER_V1_HOLDOUT_AUDIT.md", "# run ranker holdout\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_OPERATOR_RUN_CONSOLIDATION_V1.md", "# operator consolidation\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_OPERATOR_BASELINE_V1.md", "# operator baseline\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_OPERATOR_REFRESH_V1.md", "# operator refresh\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_OPERATOR_REFRESH_QA_V1.md", "# operator refresh qa\n")
    write_text(tmp_root / "docs" / "OPS_PANEL_DAY_ENGINE_OPERATOR_PIPELINE_V1.md", "# operator pipeline\n")
    write_text(tmp_root / "docs" / "OPS_COMMON_CAUSE_PRECURSOR_AUDIT_V1.md", "# common cause precursor\n")
    write_text(tmp_root / "docs" / "OPS_GPVS_FAULT_FAMILY_F1.md", "# gpvs fault family\n")

    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_local_precursor_eligibility_audit_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_local_seed_carry_fate_audit_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_run_feature_separability_audit_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_run_ranker_v0_audit.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_run_ranker_v1_holdout_audit.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_run_label_pack_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_operator_run_consolidation_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_operator_baseline_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_operator_refresh_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_operator_refresh_qa_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_panel_day_engine_operator_pipeline_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "build_common_cause_precursor_audit_v1.py", "# build\n")
    write_text(tmp_root / "research" / "prognostics" / "evaluate_gpvs_fault_family_f1.py", "# eval\n")
    write_text(tmp_root / "research" / "prognostics" / "run_panel_day_site.py", "# wrapper\n")
    write_text(tmp_root / "research" / "prognostics" / "smoke_test_panel_day_engine_run_label_pack_v1.py", "# smoke\n")

    share = tmp_root / "_share"
    write_csv(
        share / "panel_day_engine_local_precursor_eligibility_cases_v1.csv",
        [
            {
                "site": "alpha",
                "panel_id": "p1",
                "vendor_fault_family": "diode_like",
                "temporality_class": "progressive_local_precursor_expected",
                "precursor_eligible_flag": 1,
                "temporality_reason_ko": "progressive",
            },
            {
                "site": "alpha",
                "panel_id": "p2",
                "vendor_fault_family": "module_damage_like",
                "temporality_class": "abrupt_local_precursor_unexpected",
                "precursor_eligible_flag": 0,
                "temporality_reason_ko": "abrupt",
            },
            {
                "site": "beta",
                "panel_id": "p3",
                "vendor_fault_family": "diode_like",
                "temporality_class": "unknown_local_temporality",
                "precursor_eligible_flag": 0,
                "temporality_reason_ko": "unknown",
            },
        ],
        ["site", "panel_id", "vendor_fault_family", "temporality_class", "precursor_eligible_flag", "temporality_reason_ko"],
    )
    write_csv(
        share / "panel_day_engine_local_pre_ews_replay_cases_v1.csv",
        [
            {"site": "alpha", "panel_id": "p4", "vendor_fault_family": "group_or_inverter_side_like", "cohort_type": "nuisance_nonlocal"},
            {"site": "beta", "panel_id": "p5", "vendor_fault_family": "none_visible", "cohort_type": "nuisance_nonlocal"},
        ],
        ["site", "panel_id", "vendor_fault_family", "cohort_type"],
    )
    write_csv(
        share / "panel_day_engine_local_seed_carry_fate_cases_v1.csv",
        [
            {"site": "alpha", "panel_id": "r1", "run_start_date": "2025-01-01", "run_end_date": "2025-01-03", "fate_class": "recurring_chronic_monitor_like"},
            {"site": "beta", "panel_id": "r2", "run_start_date": "2025-01-04", "run_end_date": "2025-01-06", "fate_class": "isolated_unexplained"},
        ],
        ["site", "panel_id", "run_start_date", "run_end_date", "fate_class"],
    )
    write_csv(
        share / "panel_day_engine_run_feature_table_v1.csv",
        [
            {"site": "alpha", "panel_id": "r1", "run_start_date": "2025-01-01", "run_end_date": "2025-01-03", "cohort_hint": "recurring_monitor_like"},
            {"site": "beta", "panel_id": "r2", "run_start_date": "2025-01-04", "run_end_date": "2025-01-06", "cohort_hint": "unmatched_other"},
        ],
        ["site", "panel_id", "run_start_date", "run_end_date", "cohort_hint"],
    )
    write_csv(
        share / "panel_day_engine_run_label_pack_v1.csv",
        [
            {"site": "alpha", "panel_id": "r1", "run_start_date": "2025-01-01", "run_end_date": "2025-01-03", "fate_class": "recurring_chronic_monitor_like", "label_bucket": "monitor_like", "training_label": "excluded"},
            {"site": "beta", "panel_id": "r2", "run_start_date": "2025-01-04", "run_end_date": "2025-01-06", "fate_class": "isolated_unexplained", "label_bucket": "nuisance_like", "training_label": "negative"},
        ],
        ["site", "panel_id", "run_start_date", "run_end_date", "fate_class", "label_bucket", "training_label"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_path = repo_root / "research/prognostics/build_panel_day_engine_branch_inventory_and_fault_taxonomy_v1.py"

    official_paths = [
        repo_root / "_share" / "panel_day_engine_branch_inventory_v1.csv",
        repo_root / "_share" / "panel_day_engine_method_layer_status_v1.csv",
        repo_root / "_share" / "panel_day_engine_fault_taxonomy_v1.csv",
        repo_root / "_share" / "panel_day_engine_fault_taxonomy_summary_v1.csv",
    ]
    official_bytes = {path: path.read_bytes() for path in official_paths if path.exists()}

    compile_result = run(
        [
            sys.executable,
            "-m",
            "py_compile",
            "research/prognostics/build_panel_day_engine_branch_inventory_and_fault_taxonomy_v1.py",
            "research/prognostics/smoke_test_panel_day_engine_branch_inventory_and_fault_taxonomy_v1.py",
        ],
        repo_root,
    )
    assert_true(compile_result.returncode == 0, compile_result.stderr)

    with tempfile.TemporaryDirectory(prefix="branch_inventory_taxonomy_") as tmp_dir:
        tmp_root = Path(tmp_dir)
        build_fixture_root(tmp_root)

        build_result = run([sys.executable, str(build_path), "--root", str(tmp_root)], repo_root)
        assert_true(build_result.returncode == 0, build_result.stderr or build_result.stdout)

        inventory = pd.read_csv(tmp_root / "_share" / "panel_day_engine_branch_inventory_v1.csv", encoding="utf-8-sig")
        method_status = pd.read_csv(tmp_root / "_share" / "panel_day_engine_method_layer_status_v1.csv", encoding="utf-8-sig")
        taxonomy = pd.read_csv(tmp_root / "_share" / "panel_day_engine_fault_taxonomy_v1.csv", encoding="utf-8-sig")
        taxonomy_summary = pd.read_csv(tmp_root / "_share" / "panel_day_engine_fault_taxonomy_summary_v1.csv", encoding="utf-8-sig")

        assert_true(not inventory.empty, "branch inventory should not be empty")
        assert_true(
            "pv_ae/panel_day_engine.py" in inventory["file_path"].astype(str).tolist(),
            "inventory should include panel_day_engine.py",
        )
        assert_true(
            set(method_status["layer_name"].astype(str).tolist()) == {"detector", "scorer", "operator", "label_truth", "evaluation", "packaging"},
            "method_layer_status should cover all required layers",
        )
        taxonomy_ids = set(taxonomy["fault_family_id"].astype(str).tolist())
        assert_true("electrical_fault_like_progressive_local" in taxonomy_ids, "progressive electrical taxonomy row missing")
        assert_true("group_or_inverter_side_like" in taxonomy_ids, "group/inverter taxonomy row missing")
        assert_true("recurring_chronic_monitor_like" in taxonomy_ids, "monitor-like taxonomy row missing")
        summary_buckets = set(taxonomy_summary["recommended_eval_bucket"].astype(str).tolist())
        assert_true("precursor_bearing" in summary_buckets, "precursor_bearing summary row missing")
        assert_true("abrupt_or_no_precursor" in summary_buckets, "abrupt_or_no_precursor summary row missing")
        assert_true("unknown_needs_review" in summary_buckets, "unknown_needs_review summary row missing")

    for path, previous_bytes in official_bytes.items():
        assert_true(path.read_bytes() == previous_bytes, f"official file changed during smoke: {path.name}")


if __name__ == "__main__":
    main()

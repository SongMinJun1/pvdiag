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


def build_safe_bridge_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {"site": "siteA", "panel_id": "famx.1.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "부착", "GPVS_참고유형_ko": "전기적 고장 계열"},
            {"site": "siteA", "panel_id": "famx.2.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "부착", "GPVS_참고유형_ko": "개방/장치이상 계열"},
            {"site": "siteB", "panel_id": "safey.1.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "부착", "GPVS_참고유형_ko": "공통원인/인버터측 계열"},
            {"site": "siteA", "panel_id": "famx.3.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "미부착", "GPVS_참고유형_ko": "미부착"},
            {"site": "siteB", "panel_id": "safey.1.1", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "미부착", "GPVS_참고유형_ko": "미부착"},
            {"site": "siteC", "panel_id": "nomatch.1.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "미부착", "GPVS_참고유형_ko": "미부착"},
            {"site": "siteN", "panel_id": "watchy.1.0", "GPVS_적용대상_ko": "비대상", "GPVS_부착상태_ko": "비대상", "GPVS_참고유형_ko": "비대상"},
        ],
        ["site", "panel_id", "GPVS_적용대상_ko", "GPVS_부착상태_ko", "GPVS_참고유형_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        [
            {"site": "siteA", "panel_id": "famx.1.0", "GPVS_참고유형_ko": "전기적 고장 계열", "source_path": "_share/gpvs_fault_family_eval_cases.csv", "source_key_ko": "site+panel_id", "비고_ko": "fixture"},
            {"site": "siteA", "panel_id": "famx.2.0", "GPVS_참고유형_ko": "개방/장치이상 계열", "source_path": "_share/gpvs_fault_family_eval_cases.csv", "source_key_ko": "site+panel_id", "비고_ko": "fixture"},
            {"site": "siteB", "panel_id": "safey.1.0", "GPVS_참고유형_ko": "공통원인/인버터측 계열", "source_path": "_share/gpvs_fault_family_eval_cases.csv", "source_key_ko": "site+panel_id", "비고_ko": "fixture"},
        ],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        [
            {
                "경로": "_share/gpvs_fault_family_eval_cases.csv",
                "존재여부": 1,
                "파일종류_ko": "테이블",
                "granularity_ko": "패널수준",
                "panel_id_컬럼존재_flag": 1,
                "site_컬럼존재_flag": 1,
                "유형_컬럼존재_flag": 1,
                "점수_컬럼존재_flag": 0,
                "panel_attach_candidate_flag": 1,
                "current_panel_count": 6,
                "candidate_panel_count": 4,
                "overlap_panel_count": 3,
                "overlap_rate": 0.5,
                "attachability_note_ko": "site+panel_id direct match 가능",
                "note_ko": "fixture candidate",
            },
            {
                "경로": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
                "존재여부": 1,
                "파일종류_ko": "테이블",
                "granularity_ko": "유형수준",
                "panel_id_컬럼존재_flag": 0,
                "site_컬럼존재_flag": 0,
                "유형_컬럼존재_flag": 1,
                "점수_컬럼존재_flag": 1,
                "panel_attach_candidate_flag": 0,
                "current_panel_count": "",
                "candidate_panel_count": "",
                "overlap_panel_count": "",
                "overlap_rate": "",
                "attachability_note_ko": "panel key 없음",
                "note_ko": "fixture type-only",
            },
        ],
        [
            "경로",
            "존재여부",
            "파일종류_ko",
            "granularity_ko",
            "panel_id_컬럼존재_flag",
            "site_컬럼존재_flag",
            "유형_컬럼존재_flag",
            "점수_컬럼존재_flag",
            "panel_attach_candidate_flag",
            "current_panel_count",
            "candidate_panel_count",
            "overlap_panel_count",
            "overlap_rate",
            "attachability_note_ko",
            "note_ko",
        ],
    )

    write_csv(
        share / "gpvs_fault_family_eval_cases.csv",
        [
            {"site": "siteA", "panel_id": "famx.1.0", "pred_fault_family": "electrical_fault_like", "truth_fault_family": "electrical_fault_like"},
            {"site": "siteA", "panel_id": "famx.2.0", "pred_fault_family": "open_or_device_issue_like", "truth_fault_family": "open_or_device_issue_like"},
            {"site": "siteB", "panel_id": "safey.1.0", "pred_fault_family": "group_or_inverter_side_like", "truth_fault_family": "group_or_inverter_side_like"},
            {"site": "siteC", "panel_id": "other.2.0", "pred_fault_family": "none_visible", "truth_fault_family": "none_visible"},
        ],
        ["site", "panel_id", "pred_fault_family", "truth_fault_family"],
    )


def build_keep_exact_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_panel_multiaxis_verdict_v1.csv",
        [
            {"site": "siteA", "panel_id": "same.1.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "부착", "GPVS_참고유형_ko": "전기적 고장 계열"},
            {"site": "siteA", "panel_id": "same.2.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "부착", "GPVS_참고유형_ko": "개방/장치이상 계열"},
            {"site": "siteA", "panel_id": "same.3.0", "GPVS_적용대상_ko": "적용대상", "GPVS_부착상태_ko": "미부착", "GPVS_참고유형_ko": "미부착"},
            {"site": "siteZ", "panel_id": "repeat.0.1", "GPVS_적용대상_ko": "비대상", "GPVS_부착상태_ko": "비대상", "GPVS_참고유형_ko": "비대상"},
        ],
        ["site", "panel_id", "GPVS_적용대상_ko", "GPVS_부착상태_ko", "GPVS_참고유형_ko"],
    )
    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        [
            {"site": "siteA", "panel_id": "same.1.0", "GPVS_참고유형_ko": "전기적 고장 계열", "source_path": "_share/gpvs_fault_family_eval_cases.csv", "source_key_ko": "site+panel_id", "비고_ko": "fixture"},
            {"site": "siteA", "panel_id": "same.2.0", "GPVS_참고유형_ko": "개방/장치이상 계열", "source_path": "_share/gpvs_fault_family_eval_cases.csv", "source_key_ko": "site+panel_id", "비고_ko": "fixture"},
        ],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
    )
    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_inventory_v1.csv",
        [
            {
                "경로": "_share/gpvs_fault_family_eval_cases.csv",
                "존재여부": 1,
                "파일종류_ko": "테이블",
                "granularity_ko": "패널수준",
                "panel_id_컬럼존재_flag": 1,
                "site_컬럼존재_flag": 1,
                "유형_컬럼존재_flag": 1,
                "점수_컬럼존재_flag": 0,
                "panel_attach_candidate_flag": 1,
                "current_panel_count": 3,
                "candidate_panel_count": 2,
                "overlap_panel_count": 2,
                "overlap_rate": 0.6667,
                "attachability_note_ko": "site+panel_id direct match 가능",
                "note_ko": "fixture candidate",
            }
        ],
        [
            "경로",
            "존재여부",
            "파일종류_ko",
            "granularity_ko",
            "panel_id_컬럼존재_flag",
            "site_컬럼존재_flag",
            "유형_컬럼존재_flag",
            "점수_컬럼존재_flag",
            "panel_attach_candidate_flag",
            "current_panel_count",
            "candidate_panel_count",
            "overlap_panel_count",
            "overlap_rate",
            "attachability_note_ko",
            "note_ko",
        ],
    )
    write_csv(
        share / "gpvs_fault_family_eval_cases.csv",
        [
            {"site": "siteA", "panel_id": "same.1.0", "pred_fault_family": "electrical_fault_like", "truth_fault_family": "electrical_fault_like"},
            {"site": "siteA", "panel_id": "same.2.0", "pred_fault_family": "open_or_device_issue_like", "truth_fault_family": "open_or_device_issue_like"},
        ],
        ["site", "panel_id", "pred_fault_family", "truth_fault_family"],
    )


def run_builder_and_load(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_panel_key_bridge_audit_v1.py"
    result = run([sys.executable, str(build_script), "--root", str(root)], cwd=repo_root)
    if result.returncode != 0:
        raise SystemExit(result.stderr or result.stdout or "builder failed")

    share = root / "_share"
    candidates_df = pd.read_csv(share / "panel_day_engine_gpvs_panel_key_bridge_candidates_v1.csv", low_memory=False, encoding="utf-8-sig")
    summary_df = pd.read_csv(share / "panel_day_engine_gpvs_panel_key_bridge_summary_v1.csv", low_memory=False, encoding="utf-8-sig")
    recommendation_df = pd.read_csv(share / "panel_day_engine_gpvs_panel_key_bridge_recommendation_v1.csv", low_memory=False, encoding="utf-8-sig")
    return candidates_df, summary_df, recommendation_df


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_gpvs_panel_key_bridge_audit_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(__file__), doraise=True)

    official_outputs = [
        repo_root / "_share" / "panel_day_engine_gpvs_panel_key_bridge_candidates_v1.csv",
        repo_root / "_share" / "panel_day_engine_gpvs_panel_key_bridge_summary_v1.csv",
        repo_root / "_share" / "panel_day_engine_gpvs_panel_key_bridge_recommendation_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="tmp_gpvs_bridge_safe_") as tmpdir:
        root = Path(tmpdir)
        build_safe_bridge_fixture(root)
        candidates_df, summary_df, recommendation_df = run_builder_and_load(root)

        assert_true(not candidates_df.empty, "candidate bridge rows must be emitted")
        assert_true(len(candidates_df) == 12, "3 unmatched panels x 4 rules expected")
        assert_true(
            not candidates_df["panel_id"].eq("watchy.1.0").any(),
            "non-target rows must be excluded from GPVS bridge audit base",
        )
        safe_row = candidates_df.loc[
            (candidates_df["site"].eq("siteB"))
            & (candidates_df["panel_id"].eq("safey.1.1"))
            & (candidates_df["rule_name"].eq("site_plus_two_level_prefix"))
        ].iloc[0]
        assert_true(int(safe_row["matched_gpvs_row_count"]) == 1, "two-level prefix should find one GPVS row")
        assert_true(int(safe_row["unique_attachable_flag"]) == 1, "two-level prefix should be uniquely attachable")
        assert_true(int(safe_row["conflict_flag"]) == 0, "two-level prefix should avoid conflict")

        conflict_row = candidates_df.loc[
            (candidates_df["site"].eq("siteA"))
            & (candidates_df["panel_id"].eq("famx.3.0"))
            & (candidates_df["rule_name"].eq("site_plus_parent_uuid"))
        ].iloc[0]
        assert_true(int(conflict_row["matched_gpvs_row_count"]) == 2, "parent uuid should hit two GPVS rows")
        assert_true(int(conflict_row["conflict_flag"]) == 1, "parent uuid conflict should be detected")

        parent_summary = summary_df.loc[summary_df["rule_name"].eq("site_plus_parent_uuid")].iloc[0]
        assert_true(int(parent_summary["contradiction_on_matched_count"]) > 0, "matched-panel contradiction should be detected for parent uuid rule")
        assert_true(int(parent_summary["safe_attachable_count"]) == 0, "unsafe rule should not have safe attachable count")

        two_level_summary = summary_df.loc[summary_df["rule_name"].eq("site_plus_two_level_prefix")].iloc[0]
        assert_true(int(two_level_summary["unmatched_panel_count"]) == 3, "only applicable unmatched fault panels should count")
        assert_true(int(two_level_summary["safe_attachable_count"]) == 1, "two-level prefix should keep one safe bridge")

        recommendation_row = recommendation_df.iloc[0]
        assert_true(recommendation_row["recommended_action"] == "use_safe_bridge_rule", "safe fixture should recommend bridge use")
        assert_true(recommendation_row["recommended_rule_name"] == "site_plus_two_level_prefix", "two-level prefix should be preferred safe rule")

    with tempfile.TemporaryDirectory(prefix="tmp_gpvs_bridge_keep_exact_") as tmpdir:
        root = Path(tmpdir)
        build_keep_exact_fixture(root)
        candidates_df, summary_df, recommendation_df = run_builder_and_load(root)

        assert_true(not candidates_df.empty, "candidate bridge rows must still emit")
        assert_true(
            not candidates_df["panel_id"].eq("repeat.0.1").any(),
            "non-target rows must be excluded in keep-exact fixture too",
        )
        exact_row = candidates_df.loc[
            (candidates_df["panel_id"].eq("same.3.0"))
            & (candidates_df["rule_name"].eq("site_plus_parent_uuid"))
        ].iloc[0]
        assert_true(int(exact_row["conflict_flag"]) == 1, "conflict path must still work in keep-exact fixture")
        recommendation_row = recommendation_df.iloc[0]
        assert_true(recommendation_row["recommended_action"] == "keep_exact_match_only", "unsafe fixture should keep exact match only")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "smoke test must not modify official outputs")


if __name__ == "__main__":
    main()

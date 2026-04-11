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


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() == "nan" else text


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).reindex(columns=columns).to_csv(path, index=False, encoding="utf-8-sig")


def file_digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_fixture(root: Path) -> None:
    share = root / "_share"
    gpvs_out = root / "data" / "gpvs" / "out"
    share.mkdir(parents=True, exist_ok=True)
    gpvs_out.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_operator_workflow_default_v1.csv",
        [
            {
                "preview_attention_class": "queue_run",
                "site": "siteA",
                "display_entity_id": "abrupt_1",
                "display_start_date": "2026-02-01",
                "display_end_date": "2026-02-02",
                "display_span_or_day_count": 2,
                "display_shape_or_cluster_kind": "short_alert_run",
                "display_status_or_tier": "ongoing_run",
                "display_score": 9.0,
                "linked_ref_flag": 1,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "queue item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "queue_priority",
                "workflow_reason_ko": "기본 queue attention",
            },
            {
                "preview_attention_class": "watch_now_panel",
                "site": "siteB",
                "display_entity_id": "panel_repeat",
                "display_start_date": "2026-01-10",
                "display_end_date": "2026-02-10",
                "display_span_or_day_count": 32,
                "display_shape_or_cluster_kind": "chronic_alert_run",
                "display_status_or_tier": "watch_now",
                "display_score": 5.5,
                "linked_ref_flag": 0,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "watch item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "watch_priority",
                "workflow_reason_ko": "기본 watch attention",
            },
            {
                "preview_attention_class": "queue_run",
                "site": "siteQ",
                "display_entity_id": "panel_queue_only",
                "display_start_date": "2026-02-03",
                "display_end_date": "2026-02-05",
                "display_span_or_day_count": 3,
                "display_shape_or_cluster_kind": "medium_alert_run",
                "display_status_or_tier": "ongoing_run",
                "display_score": 6.5,
                "linked_ref_flag": 0,
                "truth_ref_flag": 0,
                "cluster_panel_count": 1,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "queue item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "primary_attention",
                "workflow_priority_class": "queue_priority",
                "workflow_reason_ko": "기본 queue attention",
            },
            {
                "preview_attention_class": "secondary_value_cluster",
                "site": "siteC",
                "display_entity_id": "cluster_001",
                "display_start_date": "2026-02-02",
                "display_end_date": "2026-02-03",
                "display_span_or_day_count": 2,
                "display_shape_or_cluster_kind": "discovery_cluster",
                "display_status_or_tier": "secondary_discovery_cluster",
                "display_score": 6.2,
                "linked_ref_flag": 1,
                "truth_ref_flag": 0,
                "cluster_panel_count": 3,
                "changed_since_previous_flag": 0,
                "latest_delta_source": "none",
                "latest_delta_class": "",
                "latest_delta_reason_ko": "",
                "digest_reason_ko": "cluster item",
                "workflow_policy_name": "baseline_plus_discovery_cluster",
                "workflow_role": "supplemental_discovery",
                "workflow_priority_class": "discovery_priority",
                "workflow_reason_ko": "기본 workflow에 포함된 discovery cluster",
            },
        ],
        [
            "preview_attention_class",
            "site",
            "display_entity_id",
            "display_start_date",
            "display_end_date",
            "display_span_or_day_count",
            "display_shape_or_cluster_kind",
            "display_status_or_tier",
            "display_score",
            "linked_ref_flag",
            "truth_ref_flag",
            "cluster_panel_count",
            "changed_since_previous_flag",
            "latest_delta_source",
            "latest_delta_class",
            "latest_delta_reason_ko",
            "digest_reason_ko",
            "workflow_policy_name",
            "workflow_role",
            "workflow_priority_class",
            "workflow_reason_ko",
        ],
    )

    abrupt_rows = [
        {"site": "siteA", "panel_id": "abrupt_1", "고장시점": "2025-01-01", "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_2", "고장시점": "2025-01-02", "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_3", "고장시점": "2025-01-03", "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_4", "고장시점": "2025-01-04", "증상명_ko": "다이오드형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_5", "고장시점": "2025-01-05", "증상명_ko": "개방/장치이상형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
        {"site": "siteA", "panel_id": "abrupt_6", "고장시점": "2025-01-06", "증상명_ko": "모듈손상형", "세부근거_ko": "fixture", "source_field_ko": "vendor_fault_family", "비고_ko": "fixture"},
    ]
    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        abrupt_rows,
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
    )

    # overlap one precursor with one abrupt panel to verify representative collapse but history preservation.
    write_csv(
        share / "panel_day_engine_precursor_onset_truth_v1.csv",
        [
            {"site": "siteA", "panel_id": "abrupt_6", "preferred_precursor_onset_date": "2025-01-01"},
            {"site": "siteP", "panel_id": "precursor_2", "preferred_precursor_onset_date": "2025-01-11"},
        ],
        ["site", "panel_id", "preferred_precursor_onset_date"],
    )

    write_csv(
        share / "panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv",
        [
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_1", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_2", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_3", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
            {"eval_bucket_v2": "non_panel_or_common_cause", "site": "siteCC", "panel_id": "common_4", "current_marker_only_flag": 0, "breadth_marker_only_flag": 1, "combined_marker_flag": 1},
        ],
        ["eval_bucket_v2", "site", "panel_id", "current_marker_only_flag", "breadth_marker_only_flag", "combined_marker_flag"],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {"커널로그_증상명": "출력 저하형", "주_프로젝트분류": "전조형 고장", "보조_프로젝트분류": "급작 고장", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "전압 변화형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "전조형 고장", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "패턴 이상형", "주_프로젝트분류": "공통원인 이벤트", "보조_프로젝트분류": "오경보", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "불안정형", "주_프로젝트분류": "반복 이상", "보조_프로젝트분류": "오경보", "설명_ko": "fixture", "주의_ko": "fixture"},
            {"커널로그_증상명": "복합형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "공통원인 이벤트", "설명_ko": "fixture", "주의_ko": "fixture"},
        ],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpv7_perf_summary_v1.csv",
        [
            {
                "고장유형_번호": idx,
                "고장유형_설명_ko": f"GPVS Fault{idx}",
                "성능요약_ko": "stored by-type metric",
                "수치_ko": f"auc=0.{idx}000",
                "source_ref_ko": "data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv",
            }
            for idx in range(1, 8)
        ],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_final_decision_pack_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "current_data_decision": "freeze_with_caution", "final_usage_decision": "bounded_reporting_use", "final_reason_ko": "fixture"},
            {"eval_scope": "step2_onset_truth", "current_data_decision": "freeze_with_caution", "final_usage_decision": "bounded_reporting_use", "final_reason_ko": "fixture"},
            {"eval_scope": "step3_precursor_performance", "current_data_decision": "exploratory_only", "final_usage_decision": "exploratory_only", "final_reason_ko": "fixture"},
            {"eval_scope": "step4_abrupt_no_precursor", "current_data_decision": "freeze_with_caution", "final_usage_decision": "bounded_reporting_use", "final_reason_ko": "fixture"},
            {"eval_scope": "step4_common_cause_routing", "current_data_decision": "exploratory_only", "final_usage_decision": "exploratory_only", "final_reason_ko": "fixture"},
            {"eval_scope": "operator_policy_proxy", "current_data_decision": "workflow_proxy_only", "final_usage_decision": "workflow_only", "final_reason_ko": "fixture"},
        ],
        ["eval_scope", "current_data_decision", "final_usage_decision", "final_reason_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_feasibility_v1.csv",
        [
            {
                "GPVS_패널별_직접판정_가능여부": "가능",
                "근거_ko": "fixture gpvs eval cases can be joined by site+panel_id",
                "최선_후보_파일": "_share/gpvs_fault_family_eval_cases.csv",
                "overlap_panel_count": 2,
                "overlap_rate": 2 / 13,
                "다음권장조치_ko": "fixture attach",
            }
        ],
        ["GPVS_패널별_직접판정_가능여부", "근거_ko", "최선_후보_파일", "overlap_panel_count", "overlap_rate", "다음권장조치_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpvs_panel_attach_candidates_v1.csv",
        [
            {
                "site": "siteA",
                "panel_id": "abrupt_6",
                "GPVS_참고유형_ko": "전기적 고장 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "prediction_source=critical_phenotype_v3",
            },
            {
                "site": "siteCC",
                "panel_id": "common_1",
                "GPVS_참고유형_ko": "공통원인/인버터측 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "prediction_source=strict_day_core_fallback",
            },
            {
                "site": "siteZ",
                "panel_id": "panel_extra",
                "GPVS_참고유형_ko": "무가시형 계열",
                "source_path": "_share/gpvs_fault_family_eval_cases.csv",
                "source_key_ko": "site+panel_id",
                "비고_ko": "not in panel table",
            },
        ],
        ["site", "panel_id", "GPVS_참고유형_ko", "source_path", "source_key_ko", "비고_ko"],
    )

    write_csv(
        gpvs_out / "gpvs_window_scores.csv",
        [
            {
                "sample_id": "F1::w0",
                "source_id": "F1",
                "window_idx": 0,
                "fault_type": "F1",
                "level_drop_like": 0.9,
            }
        ],
        ["sample_id", "source_id", "window_idx", "fault_type", "level_drop_like"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research/prognostics/build_panel_day_engine_panel_multiaxis_verdict_v1.py"
    smoke_script = repo_root / "research/prognostics/smoke_test_panel_day_engine_panel_multiaxis_verdict_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv",
        repo_root / "_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv",
    ]
    before = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="panel_day_engine_multiaxis_verdict_smoke_") as tmp_dir:
        root = Path(tmp_dir)
        build_fixture(root)

        result = run([sys.executable, str(build_script), "--root", str(root)], repo_root)
        assert_true(result.returncode == 0, f"builder failed: {result.stderr or result.stdout}")

        verdict_path = root / "_share/panel_day_engine_panel_multiaxis_verdict_v1.csv"
        event_path = root / "_share/panel_day_engine_panel_multiaxis_event_supplement_v1.csv"
        cluster_path = root / "_share/panel_day_engine_panel_multiaxis_cluster_supplement_v1.csv"
        summary_path = root / "_share/panel_day_engine_panel_multiaxis_verdict_summary_v1.csv"
        assert_true(verdict_path.exists(), "missing verdict csv")
        assert_true(event_path.exists(), "missing event supplement csv")
        assert_true(cluster_path.exists(), "missing cluster supplement csv")
        assert_true(summary_path.exists(), "missing summary csv")

        verdict_df = pd.read_csv(verdict_path, low_memory=False, encoding="utf-8-sig")
        event_df = pd.read_csv(event_path, low_memory=False, encoding="utf-8-sig")
        cluster_df = pd.read_csv(cluster_path, low_memory=False, encoding="utf-8-sig")
        summary_df = pd.read_csv(summary_path, low_memory=False, encoding="utf-8-sig")

        assert_true(not verdict_df.duplicated(subset=["site", "panel_id"]).any(), "main table must be unique by panel")
        assert_true(len(verdict_df) == 13, f"expected 13 unique panels, found {len(verdict_df)}")

        overlap_row = verdict_df.loc[(verdict_df["site"].eq("siteA")) & (verdict_df["panel_id"].eq("abrupt_6"))].iloc[0]
        precursor_only_row = verdict_df.loc[(verdict_df["site"].eq("siteP")) & (verdict_df["panel_id"].eq("precursor_2"))].iloc[0]
        common_row = verdict_df.loc[(verdict_df["site"].eq("siteCC")) & (verdict_df["panel_id"].eq("common_1"))].iloc[0]
        repeat_row = verdict_df.loc[(verdict_df["site"].eq("siteB")) & (verdict_df["panel_id"].eq("panel_repeat"))].iloc[0]
        unknown_row = verdict_df.loc[(verdict_df["site"].eq("siteQ")) & (verdict_df["panel_id"].eq("panel_queue_only"))].iloc[0]

        assert_true(overlap_row["대표판정_ko"] == "급작 고장", "representative priority should favor abrupt")
        assert_true(overlap_row["사건이력_ko"] == "전조형 고장+급작 고장", "event history should preserve overlap in fixed order")
        assert_true(int(overlap_row["전조형이력_flag"]) == 1, "overlap precursor flag missing")
        assert_true(int(overlap_row["급작고장이력_flag"]) == 1, "overlap abrupt flag missing")
        assert_true(overlap_row["패널고장여부_ko"] == "고장", "panel fault status should mark overlap as fault")
        assert_true(overlap_row["커널로그_원인군_ko"] == "모듈손상형", "abrupt symptom map should stay highest priority")

        assert_true(precursor_only_row["대표판정_ko"] == "전조형 고장", "precursor-only representative mapping failed")
        assert_true(precursor_only_row["사건이력_ko"] == "전조형 고장", "precursor-only history mapping failed")
        assert_true(precursor_only_row["패널고장여부_ko"] == "고장", "precursor-only fault status mapping failed")

        assert_true(common_row["대표판정_ko"] == "공통원인 이벤트", "common-cause representative mapping failed")
        assert_true(common_row["패널고장여부_ko"] == "비고장", "common-cause fault status mapping failed")
        assert_true(common_row["커널로그_증상명_ko"] == "패턴 이상형", "common-cause symptom mapping failed")

        assert_true(repeat_row["대표판정_ko"] == "반복 이상", "repeat representative mapping failed")
        assert_true(repeat_row["패널고장여부_ko"] == "미확정", "repeat fault status mapping failed")
        assert_true(repeat_row["사건이력_ko"] == "반복 이상", "repeat history mapping failed")

        assert_true(unknown_row["대표판정_ko"] == "불충분", "queue-only row should stay insufficient")
        assert_true(unknown_row["패널고장여부_ko"] == "미확정", "queue-only fault status mapping failed")
        assert_true(normalize_text(unknown_row["사건이력_ko"]) == "", "queue-only history should stay blank")

        assert_true(len(event_df) == 13, f"expected 13 event supplement rows, found {len(event_df)}")
        overlap_event_rows = event_df.loc[(event_df["site"].eq("siteA")) & (event_df["panel_id"].eq("abrupt_6"))]
        assert_true(len(overlap_event_rows) == 2, "event supplement should preserve overlap memberships")
        assert_true(
            set(overlap_event_rows["사건유형_ko"]) == {"전조형 고장", "급작 고장"},
            "overlap event supplement types mismatch",
        )
        abrupt_rep_flag = overlap_event_rows.loc[overlap_event_rows["사건유형_ko"].eq("급작 고장"), "대표판정여부_flag"].iloc[0]
        precursor_rep_flag = overlap_event_rows.loc[overlap_event_rows["사건유형_ko"].eq("전조형 고장"), "대표판정여부_flag"].iloc[0]
        assert_true(int(abrupt_rep_flag) == 1 and int(precursor_rep_flag) == 0, "representative flag propagation failed")

        assert_true(len(cluster_df) == 1, f"expected 1 cluster supplement row, found {len(cluster_df)}")
        cluster_row = cluster_df.iloc[0]
        assert_true(cluster_row["대표판정_ko"] == "공통원인 이벤트", "cluster representative mapping failed")
        assert_true(cluster_row["운영위치_ko"] == "추가 발견 후보", "cluster operating location mapping failed")

        assert_true(overlap_row["GPVS_참고유형_ko"] == "전기적 고장 계열", "matched abrupt row should attach GPVS type")
        assert_true("site+panel_id" in str(overlap_row["GPVS_근거_ko"]), "matched abrupt row should carry compact GPVS evidence")
        assert_true(common_row["GPVS_참고유형_ko"] == "공통원인/인버터측 계열", "matched common row should attach GPVS type")
        assert_true(precursor_only_row["GPVS_참고유형_ko"] == "미부착", "unmatched precursor row should stay unattached")
        assert_true(
            "패널별 GPVS 직접 판정이 없음" in str(precursor_only_row["GPVS_근거_ko"]),
            "unmatched row should keep GPVS absence reason",
        )
        assert_true(
            int((verdict_df["GPVS_참고유형_ko"] != "미부착").sum()) == 2,
            "GPVS attach count must equal feasibility overlap count",
        )

        summary_row = summary_df.iloc[0]
        rep_counts = verdict_df["대표판정_ko"].value_counts().to_dict()
        fault_counts = verdict_df["패널고장여부_ko"].value_counts().to_dict()
        assert_true(int(summary_row["전체_패널수"]) == 13, "summary total panel count mismatch")
        assert_true(int(summary_row["급작이력_패널수"]) == int(pd.to_numeric(verdict_df["급작고장이력_flag"]).sum()), "abrupt membership summary must come from final rows")
        assert_true(int(summary_row["전조형이력_패널수"]) == int(pd.to_numeric(verdict_df["전조형이력_flag"]).sum()), "precursor membership summary must come from final rows")
        assert_true(int(summary_row["공통원인이력_패널수"]) == int(pd.to_numeric(verdict_df["공통원인이력_flag"]).sum()), "common membership summary must come from final rows")
        assert_true(int(summary_row["반복이상이력_패널수"]) == int(pd.to_numeric(verdict_df["반복이상이력_flag"]).sum()), "repeat membership summary must come from final rows")
        assert_true(int(summary_row["대표판정_급작수"]) == int(rep_counts.get("급작 고장", 0)), "representative abrupt summary mismatch")
        assert_true(int(summary_row["대표판정_전조형수"]) == int(rep_counts.get("전조형 고장", 0)), "representative precursor summary mismatch")
        assert_true(int(summary_row["대표판정_공통원인수"]) == int(rep_counts.get("공통원인 이벤트", 0)), "representative common summary mismatch")
        assert_true(int(summary_row["대표판정_반복이상수"]) == int(rep_counts.get("반복 이상", 0)), "representative repeat summary mismatch")
        assert_true(int(summary_row["대표판정_불충분수"]) == int(rep_counts.get("불충분", 0)), "representative insufficient summary mismatch")
        assert_true(int(summary_row["고장_패널수"]) == int(fault_counts.get("고장", 0)), "fault-status summary mismatch")
        assert_true(int(summary_row["비고장_패널수"]) == int(fault_counts.get("비고장", 0)), "non-fault summary mismatch")
        assert_true(int(summary_row["미확정_패널수"]) == int(fault_counts.get("미확정", 0)), "unknown-status summary mismatch")
        assert_true(int(summary_row["GPVS_참고유형_부착수"]) == 2, "GPVS attached summary mismatch")
        assert_true(int(summary_row["GPVS_미부착수"]) == 11, "GPVS unattached summary mismatch")
        assert_true(int(summary_row["사건보조행수"]) == len(event_df), "event supplement summary mismatch")
        assert_true(int(summary_row["클러스터_보조행수"]) == len(cluster_df), "cluster supplement summary mismatch")
        assert_true("event supplement" in str(summary_row["note_ko"]), "summary note should mention event supplement")
        assert_true("partially attached" in str(summary_row["note_ko"]), "summary note should mention partial GPVS attach")

        assert_true(cluster_row["GPVS_참고유형_ko"] == "미부착", "cluster row must stay GPVS unattached")
        assert_true(cluster_row["GPVS_근거_ko"] == "현재 저장 산출물에는 패널별 GPVS 직접 판정이 없음", "cluster row must keep GPVS absence reason")

    after = {path: file_digest(path) for path in official_outputs}
    assert_true(before == after, "official outputs changed during smoke test")


if __name__ == "__main__":
    main()

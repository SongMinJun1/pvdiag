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


def build_fixture(root: Path) -> None:
    share = root / "_share"
    share.mkdir(parents=True, exist_ok=True)

    write_csv(
        share / "panel_day_engine_latest_perf_internal_share_v1.csv",
        [
            {
                "구분": "전조형 고장",
                "현재_대표기준": "first_signalcount2",
                "양성_표본수": 2,
                "재현율": 1.0,
                "정밀도": 1.0,
                "F1": 1.0,
                "선행시간_중앙값_일": 11.5,
                "선행시간_범위_일": "6~17",
                "현재_판정_ko": "표본이 작아 탐색적으로만 본다.",
            },
            {
                "구분": "급작 고장",
                "현재_대표기준": "final_fault_hit_by_anchor",
                "양성_표본수": 6,
                "재현율": 0.8333333333,
                "정밀도": 0.8333333333,
                "F1": 0.8333333333,
                "선행시간_중앙값_일": "",
                "선행시간_범위_일": "",
                "현재_판정_ko": "현재 데이터 기준에서는 가장 상대적으로 안정적이다.",
            },
            {
                "구분": "common-cause routing",
                "현재_대표기준": "breadth_marker_only",
                "양성_표본수": 4,
                "재현율": 1.0,
                "정밀도": 1.0,
                "F1": 1.0,
                "선행시간_중앙값_일": "",
                "선행시간_범위_일": "",
                "현재_판정_ko": "descriptive/exploratory 수준으로만 유지한다.",
            },
        ],
        ["구분", "현재_대표기준", "양성_표본수", "재현율", "정밀도", "F1", "선행시간_중앙값_일", "선행시간_범위_일", "현재_판정_ko"],
    )

    write_csv(
        share / "panel_day_engine_abrupt6_symptom_map_v1.csv",
        [
            {"site": "sitea", "panel_id": "p1", "고장시점": "2025-01-01", "증상명_ko": "다이오드형", "세부근거_ko": "vendor_fault_family=diode_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
            {"site": "sitea", "panel_id": "p2", "고장시점": "2025-01-02", "증상명_ko": "다이오드형", "세부근거_ko": "vendor_fault_family=diode_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
            {"site": "sitea", "panel_id": "p3", "고장시점": "2025-01-03", "증상명_ko": "다이오드형", "세부근거_ko": "vendor_fault_family=diode_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
            {"site": "siteb", "panel_id": "p4", "고장시점": "2025-01-04", "증상명_ko": "다이오드형", "세부근거_ko": "vendor_fault_family=diode_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
            {"site": "siteb", "panel_id": "p5", "고장시점": "2025-01-05", "증상명_ko": "개방/장치이상형", "세부근거_ko": "vendor_fault_family=open_or_device_issue_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
            {"site": "siteb", "panel_id": "p6", "고장시점": "2025-01-06", "증상명_ko": "모듈손상형", "세부근거_ko": "vendor_fault_family=module_damage_like", "source_field_ko": "vendor_fault_family", "비고_ko": "ok"},
        ],
        ["site", "panel_id", "고장시점", "증상명_ko", "세부근거_ko", "source_field_ko", "비고_ko"],
    )

    write_csv(
        share / "panel_day_engine_kernellog_project_mapping_v1.csv",
        [
            {"커널로그_증상명": "출력 저하형", "주_프로젝트분류": "전조형 고장", "보조_프로젝트분류": "급작 고장", "설명_ko": "출력 축", "주의_ko": "과장 금지"},
            {"커널로그_증상명": "전압 변화형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "전조형 고장", "설명_ko": "전압 축", "주의_ko": "과장 금지"},
            {"커널로그_증상명": "패턴 이상형", "주_프로젝트분류": "같이 흔들리는 이상", "보조_프로젝트분류": "오경보", "설명_ko": "패턴 축", "주의_ko": "과장 금지"},
            {"커널로그_증상명": "불안정형", "주_프로젝트분류": "반복 이상", "보조_프로젝트분류": "오경보", "설명_ko": "반복 축", "주의_ko": "과장 금지"},
            {"커널로그_증상명": "복합형", "주_프로젝트분류": "급작 고장", "보조_프로젝트분류": "같이 흔들리는 이상", "설명_ko": "복합 축", "주의_ko": "과장 금지"},
        ],
        ["커널로그_증상명", "주_프로젝트분류", "보조_프로젝트분류", "설명_ko", "주의_ko"],
    )

    write_csv(
        share / "panel_day_engine_gpv7_perf_summary_v1.csv",
        [
            {"고장유형_번호": "1", "고장유형_설명_ko": "GPVS Fault1", "성능요약_ko": "F1M representative", "수치_ko": "auc=0.91, ap=0.94", "source_ref_ko": "bytype"},
            {"고장유형_번호": "2", "고장유형_설명_ko": "GPVS Fault2", "성능요약_ko": "F2L representative", "수치_ko": "auc=0.57, ap=0.54", "source_ref_ko": "bytype"},
            {"고장유형_번호": "3", "고장유형_설명_ko": "GPVS Fault3", "성능요약_ko": "F3L representative", "수치_ko": "auc=0.57, ap=0.62", "source_ref_ko": "bytype"},
            {"고장유형_번호": "4", "고장유형_설명_ko": "GPVS Fault4", "성능요약_ko": "F4M representative", "수치_ko": "auc=0.53, ap=0.53", "source_ref_ko": "bytype"},
            {"고장유형_번호": "5", "고장유형_설명_ko": "GPVS Fault5", "성능요약_ko": "F5L representative", "수치_ko": "auc=0.97, ap=0.93", "source_ref_ko": "bytype"},
            {"고장유형_번호": "6", "고장유형_설명_ko": "GPVS Fault6", "성능요약_ko": "F6L representative", "수치_ko": "auc=0.52, ap=0.52", "source_ref_ko": "bytype"},
            {"고장유형_번호": "7", "고장유형_설명_ko": "GPVS Fault7", "성능요약_ko": "F7M representative", "수치_ko": "auc=0.55, ap=0.55", "source_ref_ko": "bytype"},
        ],
        ["고장유형_번호", "고장유형_설명_ko", "성능요약_ko", "수치_ko", "source_ref_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_progress_snapshot_v1.csv",
        [
            {"항목": "연구/알고리즘 큰 줄기", "현재_완료율_추정": 85, "현재_상태_ko": "주요 줄기는 완료", "근거_ko": "step3/common-cause underpowered"},
            {"항목": "운영 스택", "현재_완료율_추정": 95, "현재_상태_ko": "운영 스택 거의 완료", "근거_ko": "pipeline/release gate 완료"},
            {"항목": "내부 공유/정리 문서", "현재_완료율_추정": 70, "현재_상태_ko": "정리 문서 진행 중", "근거_ko": "appendix까지 보강"},
        ],
        ["항목", "현재_완료율_추정", "현재_상태_ko", "근거_ko"],
    )

    write_csv(
        share / "panel_day_engine_project_final_decision_pack_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "current_data_decision": "freeze_with_caution", "allowed_claim_strength": "bounded_current_data_claim", "chosen_operational_workflow_name": "", "final_usage_decision": "bounded_reporting_use"},
            {"eval_scope": "step2_onset_truth", "current_data_decision": "freeze_with_caution", "allowed_claim_strength": "bounded_current_data_claim", "chosen_operational_workflow_name": "", "final_usage_decision": "bounded_reporting_use"},
            {"eval_scope": "step3_precursor_performance", "current_data_decision": "exploratory_only", "allowed_claim_strength": "exploratory_claim_only", "chosen_operational_workflow_name": "", "final_usage_decision": "exploratory_only"},
            {"eval_scope": "step4_abrupt_no_precursor", "current_data_decision": "freeze_with_caution", "allowed_claim_strength": "bounded_current_data_claim", "chosen_operational_workflow_name": "", "final_usage_decision": "bounded_reporting_use"},
            {"eval_scope": "step4_common_cause_routing", "current_data_decision": "exploratory_only", "allowed_claim_strength": "exploratory_claim_only", "chosen_operational_workflow_name": "", "final_usage_decision": "exploratory_only"},
            {"eval_scope": "operator_policy_proxy", "current_data_decision": "workflow_proxy_only", "allowed_claim_strength": "workflow_claim_only", "chosen_operational_workflow_name": "baseline_plus_discovery_cluster", "final_usage_decision": "workflow_only"},
        ],
        ["eval_scope", "current_data_decision", "allowed_claim_strength", "chosen_operational_workflow_name", "final_usage_decision"],
    )

    write_csv(
        share / "panel_day_engine_project_handoff_summary_v1.csv",
        [
            {"eval_scope": "step1_taxonomy", "handoff_status_ko": "주의해서 사용", "chosen_operational_workflow_name": ""},
            {"eval_scope": "step2_onset_truth", "handoff_status_ko": "주의해서 사용", "chosen_operational_workflow_name": ""},
            {"eval_scope": "step3_precursor_performance", "handoff_status_ko": "탐색용으로만 유지", "chosen_operational_workflow_name": ""},
            {"eval_scope": "step4_abrupt_no_precursor", "handoff_status_ko": "주의해서 사용", "chosen_operational_workflow_name": ""},
            {"eval_scope": "step4_common_cause_routing", "handoff_status_ko": "탐색용으로만 유지", "chosen_operational_workflow_name": ""},
            {"eval_scope": "operator_policy_proxy", "handoff_status_ko": "운영 workflow 용", "chosen_operational_workflow_name": "baseline_plus_discovery_cluster"},
        ],
        ["eval_scope", "handoff_status_ko", "chosen_operational_workflow_name"],
    )


def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    build_script = repo_root / "research" / "prognostics" / "build_panel_day_engine_internal_share_clean_pack_v1.py"
    smoke_script = repo_root / "research" / "prognostics" / "smoke_test_panel_day_engine_internal_share_clean_pack_v1.py"

    py_compile.compile(str(build_script), doraise=True)
    py_compile.compile(str(smoke_script), doraise=True)

    official_outputs = [
        repo_root / "_share" / "panel_day_engine_internal_share_clean_pack_v1.md",
        repo_root / "_share" / "panel_day_engine_internal_share_clean_summary_v1.csv",
    ]
    before_digests = {path: file_digest(path) for path in official_outputs}

    with tempfile.TemporaryDirectory(prefix="tmp_internal_share_clean_pack_v1_") as tmp_dir:
        temp_root = Path(tmp_dir)
        build_fixture(temp_root)

        for forbidden in [
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_episode_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_output_normal_candidates_v1.csv",
        ]:
            assert_true(not forbidden.exists(), f"fixture unexpectedly includes seed output: {forbidden.name}")

        result = run([sys.executable, str(build_script), "--root", str(temp_root)], repo_root)
        assert_true(result.returncode == 0, f"build failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

        pack_text = (temp_root / "_share" / "panel_day_engine_internal_share_clean_pack_v1.md").read_text(encoding="utf-8-sig")
        summary_df = pd.read_csv(
            temp_root / "_share" / "panel_day_engine_internal_share_clean_summary_v1.csv",
            low_memory=False,
            encoding="utf-8-sig",
        )

        for heading in [
            "## 1. 최신 성능 요약",
            "## 2. 급작 고장 6건 증상 분류",
            "## 3. 커널로그 분류와 프로젝트 분류 관계",
            "## 4. GPV 7종 정리",
            "## 5. 현재 진행률",
            "## 6. 지금 말해도 되는 것 / 말하면 안 되는 것",
        ]:
            assert_true(heading in pack_text, f"markdown heading missing: {heading}")

        expected_sections = {
            "최신 성능",
            "급작 고장 6건",
            "커널로그-프로젝트 매핑",
            "GPV 7종",
            "진행률",
            "말해도 되는 것 / 말하면 안 되는 것",
        }
        assert_true(expected_sections <= set(summary_df["섹션"]), "summary sections missing")
        assert_true("같이 흔들리는 이상" in summary_df["항목"].tolist(), "latest perf remap row missing")
        assert_true("baseline_plus_discovery_cluster" in pack_text, "operator workflow name missing in pack")

        for forbidden in [
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_case_episode_review_v1.csv",
            temp_root / "_share" / "panel_day_engine_ae_dtw_output_normal_candidates_v1.csv",
        ]:
            assert_true(not forbidden.exists(), f"seed output should not be read or created: {forbidden.name}")

    after_digests = {path: file_digest(path) for path in official_outputs}
    assert_true(before_digests == after_digests, "smoke test modified official outputs")

    print("[OK] clean pack scripts compile")
    print("[OK] outputs generate")
    print("[OK] markdown sections are emitted")
    print("[OK] summary rows are emitted")
    print("[OK] seed-panel outputs are not read")
    print("[OK] official outputs unchanged")


if __name__ == "__main__":
    main()

# OPS Fault Coverage And Model Performance V1

## 1. 보고 목적
- 본 문서는 current frozen panel day engine stack이 어떤 fault/anomaly target을 직접 다루고 어떤 target을 보조적으로만 다루는지 concise하게 정리한 coverage/performance 보고서임.
- panel multiaxis verdict가 primary 임. conalog는 direct operational interpretation layer 임. GPVS는 reference-only 임. cause candidate heuristic은 triage-only 임.
- 25 panel / 6 fault sample은 설명용 current frozen sample이며 전체 공식 대표셋으로 일반화하면 안 됨.

## 2. 현재 알고리즘 스택
- panel multiaxis verdict가 최종 primary 판정층임.
- 사건유형/고장양상 판단은 event type과 terminal pattern을 분리하여 frozen output에 직접 반영함.
- conalog 해석층은 direct operational interpretation layer로서 conalog 원인군을 직접 부착함.
- GPVS reference layer는 current frozen sample 기준 core_reference_count=2, auxiliary_reference_count=4 로만 사용하며 direct root-cause classifier가 아님.
- cause candidate heuristic은 current frozen 6 fault sample 기준 unique_top1_candidate_count=3 의 triage-only suspected-cause ranking 층임.

## 3. 입력 데이터와 학습/참조 자산
- panel multiaxis verdict, integrated table, GPVS evidence pack, cause candidate heuristic summary를 현재 frozen front-facing stack의 직접 입력 자산으로 사용하였음.
- recovered GPVS by-type artifact와 GPVS evidence pack은 reference attach provenance와 usage rule 설명에 사용하였음.
- outputs/validation/fault_validation_report_v1.csv 는 current framework validation support count를 보조적으로 인용하였음.
- full_algorithm_f1_summary_v3.csv, critical_actionability_f1_summary.csv, gpvs_fault_family_f1_summary.csv, panel_day_engine_project_final_decision_pack_v1.csv 를 current frozen metric artifact로 사용하였음.

## 4. fault/anomaly 커버리지 1대1 매핑
- 패널고장여부, 사건유형, 최종고장양상, conalog 원인군은 직접커버 target 임.
- GPVS reference attach와 heuristic suspected-cause ranking은 보조커버 target 임.
- GPVS는 reference-only layer이므로 physical root-cause 1대1 classifier로 읽으면 안 됨.

## 5. 레이어별 성능지표 원칙
- panel multiaxis verdict와 사건유형/고장양상 판단은 공식 frozen artifact가 있을 때에만 F1/Precision/Recall을 사용함.
- conalog 해석층은 coverage/agreement 스타일 지표를 우선 사용함.
- GPVS reference layer는 attach coverage, support count, reference-only policy 지표를 사용함.
- cause candidate heuristic은 triage-only layer이므로 ranking ground truth가 없으면 support count와 validation support count만 사용하고 과장된 ranking metric을 만들지 않음.

## 6. 현재 확보된 지표와 해석
- current frozen integrated summary 기준 total_panel_count=25, fault_panel_count=6 임.
- full_algorithm_f1_summary_v3 에는 strict/operational overall precision, recall, f1 이 존재하였음. 다만 broader frozen algorithm scope 수치이므로 25 panel / 6 fault 설명용 sample과 동일시하면 안 됨.
- panel_day_engine_project_final_decision_pack_v1 에는 step3 precursor performance 와 step4 abrupt no-precursor scope의 current_best_f1 이 존재하였음. 다만 support가 작고 final_usage_decision이 exploratory_only 로 표시된 scope임.
- GPVS evidence summary 에는 external evidence available count, core reference count, auxiliary reference count가 존재하였음. 이는 reference-only support metric 임.
- cause candidate summary 와 validation framework 는 triage-only heuristic의 support count와 action-note alignment support count만 제공하며 official ranking metric은 제공하지 않음.

## 7. 현재 한계와 주의사항
- current frozen sample 25 panel / 6 fault는 설명용 current snapshot 이며 전체 성능 대표셋으로 일반화하면 안 됨.
- GPVS는 reference-only layer 이므로 attach count나 family-eval artifact를 direct root-cause classifier 성능처럼 읽으면 안 됨.
- cause candidate heuristic은 triage-only layer 이므로 suspected-cause narrowing 과 competition guidance 용도로만 읽어야 하며 final diagnosis로 사용하면 안 됨.
- 본 문서는 report/build layer only 단계이며 detector logic이나 frozen front-facing output meaning을 다시 정의하지 않았음.

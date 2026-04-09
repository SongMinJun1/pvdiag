# OPS_PANEL_DAY_ENGINE_PROJECT_HANDOFF_PACK_V1

## 목적
- completed final decision pack 을 사람이 바로 읽고 넘길 수 있는 handoff artifact 로 바꾼다.
- 핵심은 metric table 을 하나 더 늘리는 것이 아니라, 현재 프로젝트 결론을 한국어 문장으로 간단히 전달하는 것이다.

## 왜 지금 handoff pack 이 필요한가
- final decision pack 까지 오면 scope 별 current-data decision, final usage decision, claim boundary 는 이미 정리돼 있다.
- 하지만 실제 내부 인수인계나 보고에서는 CSV 여러 장보다 "지금 뭘 확정해서 쓰고, 뭘 조심하고, 뭘 탐색으로 남기나" 를 한 페이지로 말할 수 있어야 한다.
- 그래서 다음 단계는 metric 세부표가 아니라 human-readable handoff 문서가 맞다.

## 입력과 해석 원칙
- 입력은 다음 산출물을 그대로 재사용한다.
  - `panel_day_engine_project_final_decision_pack_v1.csv`
  - `panel_day_engine_project_final_decision_summary_v1.csv`
  - `panel_day_engine_project_final_do_and_dont_v1.csv`
  - `panel_day_engine_operator_attention_policy_recommendation_v1.csv`
  - `panel_day_engine_operator_release_gate_manifest_v1.csv`
  - `panel_day_engine_operator_pipeline_manifest_v1.csv`
- 이 pack 은 detector/scorer 동작을 바꾸지 않는다.
- final decision pack 의 결론을 사람이 읽기 쉬운 handoff 문장으로 다시 정리할 뿐이다.

## Markdown 구성
- `_share/panel_day_engine_project_handoff_pack_v1.md` 는 정확히 다섯 섹션만 가진다.
  - `1. 지금 확정해서 쓸 수 있는 것`
  - `2. 조심해서만 써야 하는 것`
  - `3. 아직 탐색적으로만 봐야 하는 것`
  - `4. 운영 기본 workflow`
  - `5. 말해도 되는 것 / 말하면 안 되는 것`

## Scope 해석 기준
- `step1_taxonomy`
  - structural coverage only 로 적는다.
  - detector 성능 best target 처럼 표현하지 않는다.
- `step2_onset_truth`
  - structural coverage/reference only 로 적는다.
  - onset availability / lead reference 를 classifier 성능으로 과장하지 않는다.
- `step3_precursor_performance`
  - exploratory only 로 적는다.
- `step4_abrupt_no_precursor`
  - bounded use / caution 으로 적는다.
- `step4_common_cause_routing`
  - exploratory only 로 적는다.
- `operator workflow`
  - policy recommendation 이 고른 chosen operational workflow 이름을 적는다.
  - 이 workflow 선택은 detector generalization claim 이 아니라 운영 workflow choice 라는 점을 함께 적는다.

## Release / Pipeline 상태
- handoff 문서에는 release gate 와 pipeline 상태를 plain Korean 으로 같이 적는다.
- source of truth:
  - `final_release_gate_pass_flag` from `panel_day_engine_operator_release_gate_manifest_v1.csv`
  - `final_pipeline_pass_flag` from `panel_day_engine_operator_pipeline_manifest_v1.csv`
- 현재 v1 handoff pack 은 recommended workflow 가 `baseline_plus_discovery_cluster` 로 해석되는 현재 상태를 전제로 만든다.

## Summary CSV
- `_share/panel_day_engine_project_handoff_summary_v1.csv` 는 eval_scope 당 1행을 둔다.
- `handoff_status_ko` 는 `final_usage_decision` 을 아래처럼 사람이 읽는 상태값으로 바꾼다.
  - `operational_default` -> `지금 기본값으로 사용`
  - `bounded_reporting_use` -> `주의해서 사용`
  - `exploratory_only` -> `탐색용으로만 유지`
  - `workflow_only` -> `운영 workflow 용`

## 사용법
- 내부 전달:
  - markdown handoff pack 을 먼저 읽는다.
  - 필요할 때만 summary CSV 로 scope 별 상태를 확인한다.
- 보고/발표:
  - handoff markdown 의 section 5 를 claim boundary 체크리스트처럼 사용한다.
  - workflow validation 결과를 detector 일반 성능 주장으로 바꾸지 않는다.

## 주의
- 이 문서는 detector/scorer 변경안이 아니다.
- final decision pack 다음 단계의 human-readable handoff / reporting pack 이다.

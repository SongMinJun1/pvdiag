# OPS_PANEL_DAY_ENGINE_PROJECT_FINAL_DECISION_PACK_V1

## 목적
- 더 이상 fault case 를 추가 수집할 수 없다는 hard constraint 아래에서, 프로젝트 전체의 현재 결론을 한 번 더 handoff 가능한 형태로 정리한다.
- 이전 `project_current_data_freeze_pack_v1` 이 scope별 freeze boundary 를 보여줬다면, 이번 final decision pack 은 그 결과에 operator workflow 선택과 release/pipeline 상태를 합쳐서 "지금 무엇을 실제로 넘길 것인가" 를 정리한다.

## 왜 지금 final decision pack 이 필요한가
- truth expansion / acquisition backlog 까지 정리했더라도, 추가 수집이 막힌 순간 collection 계획만으로는 현재 writing/reporting/handoff 결정을 대신할 수 없다.
- 그래서 지금은:
  - 무엇을 operational default 로 둘 수 있는지
  - 무엇을 bounded reporting 용도로만 써야 하는지
  - 무엇을 exploratory 로만 남겨야 하는지
  - 무엇을 operator workflow proxy 로만 넘겨야 하는지를 한 파일 세트로 닫아야 한다.

## no-new-fault constraint 가 바꾸는 것
- positive support 가 부족한 scope 는 좋은 수치가 있어도 freeze upgrade 를 더 밀어붙일 수 없다.
- 따라서 final decision 은 “최고 수치” 보다 “현재 data 로 허용되는 claim boundary” 를 우선한다.
- 특히:
  - step3 precursor performance 는 informative 해도 exploratory only 로 남는다.
  - step4 abrupt/no-precursor 는 precursor-abrupt consistency audit overlap 2건과 single-panel forensic holdout `c42997...1.1` 을 제외한 pure abrupt support 3 기준으로 다시 읽고, 현재는 exploratory only 로 남긴다.
  - step4 common-cause routing 은 descriptive / exploratory 로만 유지한다.
  - operator workflow 는 detector 성능 freeze 가 아니라 packaging/QA/pipeline/release gate 를 통과한 workflow handoff 로 읽는다.

## final_usage_decision 해석
- `operational_default`
  - 현재 data 제약 안에서도 기본 결론/기본 운용값으로 handoff 가능
- `bounded_reporting_use`
  - 현재 data 범위 안에서만 조심스럽게 보고/발표/핸드오프 가능
- `exploratory_only`
  - informative 하지만 안정적 기본 결론처럼 쓰면 안 됨
- `workflow_only`
  - detector/scorer 일반화 성능이 아니라 operator workflow 정당화로만 사용

## chosen operational workflow 해석
- `operator_policy_proxy` scope 에만 `chosen_operational_workflow_name` 이 채워진다.
- 이 값은 retrospective proxy best target 이 아니라 policy recommendation 이 고른 실제 operational workflow 다.
- final pack 은 여기에 release gate / pipeline pass 상태를 붙여, "현재 운영에 넘겨도 되는 workflow 인가" 를 함께 보여준다.

## do-and-don't table 사용법
- handoff 문서, 발표, 요약 메일, 발표 대본에서 그대로 옮겨 쓸 수 있는 최소 행동 규칙 표다.
- `do_text_ko`
  - 지금 허용되는 사용 방식
- `dont_text_ko`
  - 금지해야 하는 과장/오해 유도 표현
- 권장 사용 순서:
  - 먼저 project-wide current data limit 를 밝힌다.
  - 다음으로 step1/step2 구조적 scope 를 classifier 성능처럼 쓰지 않도록 고정한다.
  - 그다음 step3/step4/operator workflow scope 의 허용 범위를 각각 설명한다.

## 주의
- 이 문서는 detector/scorer 변경안이 아니다.
- current-data-limited final reporting / operational-default / handoff pack 이다.
- 여기서 abrupt 는 pure abrupt event type 만 가리키고, precursor 가 있는 사건의 급격 종료는 terminal failure pattern 으로만 남긴다.
- `c42997a6-5881-47e7-9035-7de8a2673b54.1.1` 은 fault panel 이지만 current stored data 기준 pure abrupt typing 은 holdout 이고, current re-audit family hint `open_or_device_issue_like` 만 보조 힌트로 남긴다.

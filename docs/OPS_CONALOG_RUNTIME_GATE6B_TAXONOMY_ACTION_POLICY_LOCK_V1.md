<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1

## 1. 목적
Gate 6A는 현재 존재하는 축을 inventory로 모았다.
Gate 6B는 그 축들을 실제 운영/분석 산출물에서 어떻게 잠글지 정한다.

이 문서의 목적은 다음과 같다.
- operator-facing에 직접 노출할 축과 analyst-facing에만 남길 축을 구분한다.
- maintenance lane과 safety/control lane을 결과 구조에서 어떻게 분리할지 잠근다.
- `problem_class`, `operational_category`, `electrical_phenotype`, `scope`, `action lane`, `confidence`를 어떤 깊이로 보여줄지 정한다.
- Gate 5 projection policy가 실제 표시 정책으로 내려앉을 수 있게 한다.

## 2. 사용 규칙
- 이 문서는 taxonomy를 더 늘리는 문서가 아니라 `노출 정책 lock` 문서다.
- operator-facing에 노출하는 축은 적을수록 좋지만, 의미 손실이 크면 안 된다.
- analyst-facing은 canonical result object 대부분을 허용할 수 있다.
- maintenance lane과 safety/control lane은 같은 등급표나 같은 단일 action label로 접지 않는다.
- `cause`, `phenotype`, `scope`, `action`, `confidence`를 하나의 top1 label로 접지 않는다.

## 3. 상태
- 상태: `draft`
- 현재 목적:
  - Gate 5 projection policy와 Gate 2B canonical object를 실제 표시 정책으로 연결
- 현재 우선 기준:
  - operator-facing headline 경계와 raw-only/official 공식성 구분은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)를 따른다.
- 아직 하지 않는 것:
  - csv/xlsx 컬럼 patch
  - 현재 산출물 wording patch
  - 점수/threshold patch

## 4. Gate 6B가 잠그는 것

### 4.1 top-level operator-facing 결과 구조
operator-facing에서 기본으로 읽는 축은 아래 여섯 개만 허용한다.
- `operational_state`
- `operational_category`
- `electrical_phenotype` 또는 완곡한 패턴 설명
- `maintenance_lane` 축약
- `confidence_level` 축약
- 필요 시 `추가 확인 필요`/`보류` 메모

직접 headline으로 금지하는 것:
- `candidate_ranked` 전체
- `event_type`
- `terminal_pattern`
- `problem_class`
- `common_cause_flag` 원문값
- `control_scope_candidate`

### 4.2 analyst-facing 결과 구조
analyst-facing에서는 아래 축을 직접 볼 수 있다.
- `operational_state`
- `problem_class`
- `operational_category`
- `candidate_ranked`
- `electrical_phenotype`
- `event_type`
- `terminal_pattern`
- `locus`
- `common_cause_flag`
- `maintenance_lane`
- `safety_lane`
- `confidence_level`
- `competition_state`
- `abstain_reason`
- `primary_evidence_path`
- `supporting_evidence`

### 4.3 safety/control lane의 표시 원칙
operator-facing 기본 묶음에서는 safety/control lane을 direct primary action으로 전면 배치하지 않는다.

허용:
- `추가 센서 확인 필요`
- `원격 차단 연계 검토`
- `안전 정책 검토 필요`

보류:
- `모듈 차단 후보`
- `스트링/접속반 차단 후보`
- `화재안전 우선 정책`

조건:
- E5 열/외부 센서
- E6 제어/차단 범위
가 약하면 direct recommendation으로 승격 금지

## 5. 축별 노출 정책

### 5.1 `problem_class`
역할:
- 최상위 문제 대분류

operator-facing:
- 기본 숨김
- master report나 analyst note에서만 설명

analyst-facing:
- 직접 노출 허용

이유:
- `electrical / shape / instability / common-cause / control`은 operator에게는 너무 추상적일 수 있다.

### 5.2 `operational_category`
역할:
- 운영 분류

operator-facing:
- 직접 노출 허용
- 다만 1개 headline으로만 노출

analyst-facing:
- 직접 노출 허용
- ranked candidate와 함께 볼 수 있음

허용 예:
- `음영`
- `오염`
- `다이오드`
- `접속`
- `센서`
- `MLPE 응답`
- `외부 전원`
- `원인 미확정`

### 5.3 `candidate_ranked`
역할:
- 상세 원인 후보

operator-facing:
- 기본 숨김
- 필요 시 `상위 해석 후보` 1개만 축약 허용

analyst-facing:
- top1/top2/top3 직접 노출 허용

### 5.4 `electrical_phenotype`
역할:
- 전기적 현상 축

operator-facing:
- 직접 노출 가능
- 다만 너무 기술적이면 완곡한 패턴 설명으로 변환

analyst-facing:
- 직접 노출 허용

허용 예:
- `전압강하형`
- `전류단절형`
- `출력붕괴형`
- `전압 유지 + 전류 저하형`
- `간헐 회복/재발형`

### 5.5 `event_type` / `terminal_pattern`
역할:
- retrospective 사건 해석

operator-facing:
- 기본 숨김
- direct field 노출 금지
- official current에서만 softened secondary summary의 입력으로 제한적 허용

analyst-facing:
- 직접 노출 허용

금지:
- current preview headline
- precursor report headline

### 5.6 `locus` / `common_cause_flag`
역할:
- 범위/공통원인 축

operator-facing:
- direct raw field 노출은 기본 숨김
- 대신 action wording에 간접 반영
  - `공통원인 확인 필요`
  - `그룹 영향 확인`

analyst-facing:
- 직접 노출 허용

### 5.7 `maintenance_lane`
역할:
- 운영자가 실제로 해야 할 유지관리 행동

operator-facing:
- 직접 노출 허용

허용 예:
- `모니터링`
- `현장 점검`
- `공통원인 확인`
- `세척 확인`
- `배선/접속 확인`
- `MLPE/계측 확인`

analyst-facing:
- 세부 lane과 근거 함께 노출 가능

### 5.8 `safety_lane`
역할:
- 안전/제어 행동

operator-facing:
- 기본 숨김 또는 제한적 보조 노출

허용 예:
- `추가 센서 확인 필요`
- `원격 차단 연계 검토`

금지:
- E5/E6 불충분 상태에서 direct shutdown recommendation

analyst-facing:
- 직접 노출 허용

### 5.9 `confidence_level` / `competition_state` / `abstain_reason`
역할:
- 확신도와 보류 이유

operator-facing:
- `confidence_level`은 축약해서 허용
- `competition_state`와 `abstain_reason`은 `추가 확인 필요`로 완곡화

analyst-facing:
- 직접 노출 허용

## 6. operator-facing 기본 표시 규칙

### 6.1 precursor report
기본 표시:
- `operational_state`
- `operational_category`
- 완곡한 `electrical_phenotype`
- `maintenance_lane`
- `confidence` 축약

기본 숨김:
- `event_type`
- `terminal_pattern`
- `candidate_ranked`
- `problem_class`
- `safety_lane`

### 6.2 official current
기본 표시:
- `operational_state`
- 필요 시 `operational_category`
- `maintenance_lane`

기본 숨김:
- `candidate_ranked`
- `event semantics`
- `raw-only provenance`

### 6.3 master report
기본 표시:
- artifact 역할
- 각 artifact가 어떤 축을 보여주는지
- 읽는 순서

기본 숨김:
- 개별 row 판정 상세

## 7. analyst-facing 기본 표시 규칙

### 7.1 raw-only fault signal report
기본 표시:
- `operational_state`
- `primary_evidence_path`
- `candidate_ranked`
- `electrical_phenotype`
- `locus`
- `common_cause_flag`
- `maintenance_lane`
- `confidence_level`

선택 표시:
- `event_type`
- `terminal_pattern`
- `safety_lane`

### 7.2 detailed report
기본 표시:
- canonical result object 대부분
- lineage / timeline / definitions

## 8. 현재 정책으로 고정하는 top-level 표시 개수

### 8.1 operator-facing
operator-facing headline은 최대 3축까지만 직접 headline으로 쓴다.
- 상태
- 운영 분류
- 유지관리 행동

추가 정보는 보조 설명으로만 붙인다.

### 8.2 analyst-facing
analyst-facing은 최대 6축까지 한 row에서 볼 수 있다.
- 상태
- 증거 경로
- 원인 후보
- 현상
- 범위
- 확신도

## 9. 금지 규칙
- `cause + phenotype + action`을 한 단어 top1로 합치기
- `maintenance_lane + safety_lane`을 같은 action field로 합치기
- `event_type/terminal_pattern`을 current state headline으로 승격하기
- `problem_class`를 operator-facing 필수 헤드라인으로 강제하기
- `candidate_ranked`를 operator-facing 기본 표에 그대로 노출하기
- `common_cause_flag`를 근거 없이 panel-local label과 같이 두기

## 10. 보류/미확정 정책
- `operational_category = 원인 미확정`은 허용 상태다
- `maintenance_lane = 공통원인 확인`은 허용 상태다
- `confidence_level = low`와 함께 `추가 확인 필요`를 붙이는 것은 정상 정책이다
- 불확실성을 숨기기 위해 강한 top1 category로 밀어 올리지 않는다

## 11. 현재 코드/문서 기준으로 이 정책이 해결하는 것
- Gate 6A inventory를 operator-facing/analyst-facing 노출 정책으로 실제 연결한다
- Gate 5 projection policy가 표시 대상 축을 명확히 갖게 된다
- maintenance lane과 safety lane이 같은 칼럼/등급표로 접히는 문제를 줄인다
- event semantics가 current headline을 먹어버리는 문제를 막는다

## 12. Decision Log에 바로 올릴 질문
- operator-facing에서 `operational_category`를 항상 보여줄지, 필요 시만 보여줄지
- `electrical_phenotype`를 operator-facing 기본 칼럼으로 둘지, 설명문으로만 둘지
- `원인 미확정`을 operator-facing current에도 직접 허용할지
- `공통원인 확인`을 maintenance lane으로 둘지 별도 investigation lane으로 둘지
- `safety_lane` 보조 노출을 precursor report에도 허용할지

## 13. Gate 6B 체크리스트
- operator-facing과 analyst-facing이 같은 축 깊이를 쓰지 않는가
- maintenance lane과 safety lane이 분리되어 있는가
- current artifact에서 event semantics headline이 사라졌는가
- ranked candidate가 operator-facing 기본 표에서 숨겨져 있는가
- uncertainty가 `원인 미확정/추가 확인 필요`로 설계되어 있는가

## 14. 근거 source
- [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

## 15. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 5 output policy:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 2B canonical result model:
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- Gate 4A semantics contract:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)

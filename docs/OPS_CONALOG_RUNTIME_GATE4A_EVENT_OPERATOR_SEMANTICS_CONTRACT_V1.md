<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1

## 1. 목적
같은 신호라도 아래 셋은 같은 뜻이 아니다.
- `runtime event semantics`
- `operator-facing current semantics`
- `analyst-facing explanation semantics`

이 문서는 그 차이를 계약으로 고정한다.

목표:
- event semantics에서 사건을 닫는 기준과 operator-facing에서 현재 상태를 보여주는 기준을 분리한다.
- `fault_like_day`, `critical_fault`, `critical_confirmed`, `final_fault`, `event_type`, `terminal_pattern`이 각 층에서 어떻게 읽혀야 하는지 잠근다.
- Gate 3, Gate 4, Gate 5, Gate 2B가 같은 semantics 계약을 공유하게 한다.

## 2. 사용 규칙
- event semantics에 쓰인다고 해서 operator-facing direct label로 승격하지 않는다.
- operator-facing에 보인다고 해서 runtime event를 닫는 기준으로 역추론하지 않는다.
- analyst-facing 설명은 event semantics와 operator-facing 상태를 중개하지만, 독립 판정을 새로 만들지 않는다.
- 같은 row에서 `event_type/terminal_pattern`과 `operational_state`를 같은 뜻처럼 쓰지 않는다.

## 3. 상태
- 상태: `draft`
- 현재 목적:
  - semantics 층의 경계를 문서로 잠그기
- 현재 우선 기준:
  - official/raw-only/operator headline 경계는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)를 따른다.
- 아직 하지 않는 것:
  - runtime_rawonly_chain_common_v1.py 알고리즘 patch
  - current preview / precursor report wording patch

## 4. 세 층의 정의

### 4.1 Layer A. runtime event semantics
질문:
- 이 패널/사건을 시간축으로 보면 어떤 사건으로 해석되는가

대표 필드:
- `strict_trigger_date`
- `retrospective_onset`
- `fault_status`
- `event_type`
- `terminal_pattern`
- `has_final_fault`
- `has_critical_fault`

역할:
- 사건을 retrospective하게 정리
- precursor gap, event_type, terminal pattern 같은 시간 해석 생성

주의:
- 이 층은 current 운영표의 direct wording과 1:1로 동일하지 않다.

### 4.2 Layer B. operator-facing current semantics
질문:
- 지금 운영자가 이 패널을 어떤 상태로 읽어야 하는가

대표 필드:
- `operational_state`
- `problem_class` 축약
- `operational_category` 축약
- `maintenance_lane` 축약
- `confidence_level` 축약

역할:
- 공식 current / precursor report에서 직접 읽는 현재 상태
- raw-only fault signal report에서는 필요할 때만 제한된 operator-support summary로 참조되는 상태
- 운영 조치 우선순위 제공

주의:
- event_type/terminal_pattern은 필요할 때 보조로만 노출
- retrospective event 해석을 current state처럼 말하지 않는다

### 4.3 Layer C. analyst-facing explanation semantics
질문:
- 왜 그렇게 읽혔는가

대표 필드:
- `primary_evidence_path`
- `supporting_evidence`
- `candidate_ranked`
- `electrical_phenotype`
- `locus`
- `common_cause_flag`
- `abstain_reason`

역할:
- detailed report, raw-only fault signal report, analyst note의 설명층

주의:
- operator-facing보다 넓게 보여줄 수 있지만, semantics 계약 밖의 새 상태를 만들면 안 된다

## 5. layer별 주요 질문 차이
| layer | 핵심 질문 | 대표 산출물 |
| --- | --- | --- |
| runtime event semantics | 이 사건은 전조형인가 급작인가, 어디서 trigger가 걸렸는가 | runtime audit / event fields |
| operator-facing current semantics | 지금 운영자가 신경 써야 하는 상태는 무엇인가 | current / precursor / 제한된 operator-support summary |
| analyst-facing explanation semantics | 왜 그렇게 읽혔고 무엇이 비어 있는가 | detailed / raw-only / master guide |

## 6. 신호별 semantics 계약

### 6.1 `fault_like_day`
event semantics:
- trigger 보조 축으로 들어갈 수 있다
- retrospective onset 해석의 경계 신호가 될 수 있다

operator-facing:
- 단독으로 `고장 신호` direct label 금지
- 단독으로 `precursor candidate` direct 승격 금지
- 보조 설명 또는 `경계 신호` 수준으로만 허용

analyst-facing:
- boundary signal로 표시 가능
- 다만 hard evidence와 동일 tier로 말하지 않는다

### 6.2 `critical_fault`
event semantics:
- strong fault path의 시작점으로 쓸 수 있다
- strict trigger의 일부가 될 수 있다

operator-facing:
- `강한 고장 신호` 수준까지만 허용
- `최종 고장 신호`와 동급 표현 금지

analyst-facing:
- strong path의 중심 신호로 설명 가능
- `critical_confirmed`와 구분해서 보여준다

### 6.3 `critical_confirmed`
event semantics:
- confirm된 critical path
- final path 일부가 된다

operator-facing:
- `강한 고장 신호 확정` 허용
- 단, 같은 사건에서 `final_fault`가 있으면 보조 근거로 내린다

analyst-facing:
- final path와의 관계를 명시적으로 설명 가능

### 6.4 `final_fault`
event semantics:
- 사건 확정 경로의 최상위 상태

operator-facing:
- `최종 고장 신호` 허용
- 현재 confirm path 결과이지 미래 예언이 아님

analyst-facing:
- dead-like path인지 critical-confirmed path인지 분해해서 설명 가능

### 6.5 `event_type`
event semantics:
- 핵심 필드

operator-facing:
- current state 기본 필드가 아님
- direct field 노출 금지
- official current에서 이미 닫힌 사례를 설명하는 `softened secondary summary`의 입력으로만 제한적 사용

analyst-facing:
- event reconstruction에 적극 사용 가능

### 6.6 `terminal_pattern`
event semantics:
- 핵심 필드

operator-facing:
- direct field 노출 금지
- official current에서 이미 닫힌 사례를 설명하는 `softened secondary summary`의 입력으로만 제한적 허용
- current state와 같은 칼럼에 섞지 않는다

analyst-facing:
- event reconstruction에서 적극 사용 가능

## 7. `operational_state`와 `event_type/terminal_pattern`의 관계

### 7.1 서로 다른 축이다
- `operational_state`:
  지금 운영자가 읽는 현재 상태
- `event_type`:
  retrospective 사건유형
- `terminal_pattern`:
  사건 종결 해석

예:
- `operational_state = precursor candidate`
- `event_type = 미정`
- `terminal_pattern = 미정`

또는
- `operational_state = 고장 신호`
- `event_type = 전조형 고장`
- `terminal_pattern = 급격 종료`

이는 모순이 아니다.

### 7.2 금지되는 혼용
- `진행성 악화`를 현재 상태처럼 current 표 헤드라인에 올리기
- `전조형 고장`을 precursor candidate와 같은 말처럼 쓰기
- `급격 종료`를 final_fault와 동일 상태처럼 쓰기

## 8. canonical result object와의 매핑

### 8.1 event semantics -> canonical object
- `event_type` -> `temporal_axis.event_type`
- `terminal_pattern` -> `temporal_axis.terminal_pattern`
- `strict_trigger_date` -> `provenance/evidence metadata`
- `retrospective_onset` -> `temporal metadata`

### 8.2 operator semantics -> canonical object
- `operational_state` -> `state_axis.operational_state`
- `state_lane` -> `state_axis.state_lane`
- current direct wording -> `state_axis` + 축약된 `action_axis`

### 8.3 analyst semantics -> canonical object
- `primary_evidence_path` -> `evidence_axis.primary_evidence_path`
- `candidate_ranked` -> `cause_axis.candidate_ranked`
- `electrical_phenotype` -> `phenotype_axis.electrical_phenotype`
- `abstain_reason` -> `confidence_axis.abstain_reason`

## 9. artifact별 semantics 우선순위
| artifact | 우선 semantics | 보조 semantics | 금지되는 기본 해석 |
| --- | --- | --- | --- |
| `fault_panel_result_current_*` | operator-facing current semantics | 일부 explanation | event semantics direct headline |
| `fault_panel_result_precursor_report_v1.csv` | operator-facing current semantics | 일부 explanation | terminal pattern headline |
| `fault_panel_result_raw_only_fault_signal_report_v1.csv` | analyst-facing explanation semantics | operator-facing summary | event semantics를 current state와 동일시 |
| `fault_panel_result_detailed_report_v1.xlsx` | analyst-facing explanation semantics | event semantics | 없음 |
| `runtime audit / raw event fields` | event semantics | explanation | operator current wording으로 자동 번역 |
| `master_report` | 안내 semantics | artifact 차이 설명 | 새 상태 발명 |

## 10. precedence 규칙

### 10.1 상태 precedence
operator-facing current에서 우선 보는 것:
1. `operational_state`
2. `primary_evidence_path` 축약
3. `operational_category`
4. `maintenance_lane`

event semantics 필드는 보조로만 사용

### 10.2 사건 precedence
event reconstruction에서 우선 보는 것:
1. `event_type`
2. `terminal_pattern`
3. `strict_trigger_date`
4. `retrospective_onset`

### 10.3 conflict 해결
`event_type/terminal_pattern`이 현재 상태와 긴장관계에 있어 보이면:
- current artifact에서는 `operational_state`를 우선
- detailed/analyst artifact에서는 둘 다 보여주되 축이 다름을 명시

## 11. 보류/미확정 규칙
- event semantics는 닫혔어도 operator-facing current에선 `보류`가 될 수 있다
  - 예: common-cause unresolved
- operator-facing current가 `고장 신호`여도 cause_axis는 `원인 미확정`일 수 있다
- analyst-facing explanation은 이 둘의 차이를 노출할 수 있다

## 12. 현재 코드 기준으로 가장 위험한 혼용 포인트
- `fault_like_day`가 event trigger에 들어간다는 이유로 operator-facing에서 과하게 읽히는 것
- `critical_fault`와 `critical_confirmed`를 같은 강도로 current wording에 쓰는 것
- `event_type/terminal_pattern`을 precursor/current 표에서 현재 상태처럼 읽히게 하는 것
- `final_fault`를 미래 예언처럼 읽히게 하는 것

## 13. Decision Log에 바로 올릴 질문
- `fault_status=고장`을 operator-facing current semantics에 어느 정도 반영할 것인가
- official current의 `softened event summary` 조건부 노출 규칙은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 에서 잠겼다.
- `critical_fault`를 operator-facing current에서 언제 직접 보여줄지
- `fault_like_day`를 event semantics trigger에서 유지하되 current wording에선 완전히 숨길지
- `strict_trigger_date`를 current 설명에 어떤 이름으로만 허용할지

## 14. Gate 4A 체크리스트
- 같은 필드가 event semantics와 operator semantics에서 같은 뜻처럼 읽히지 않는가
- `operational_state`와 `event_type/terminal_pattern`이 분리되어 있는가
- `fault_like_day`가 operator-facing direct label로 새지 않는가
- current artifact가 event reconstruction 문서처럼 되지 않는가
- detailed artifact가 current summary를 대신하려 들지 않는가

## 15. 근거 source
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

## 16. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 4 hard evidence 경계:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- Gate 5 출력 정책:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 2B canonical multi-axis result model:
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1

## 1. 목적
Gate 2A는 `어떤 판단을 하려면 어떤 관측 축이 필요한가`를 잠갔다.
이제 Gate 2B는 `그 판단을 어떤 결과 객체로 담을 것인가`를 잠근다.

이 문서의 목적은 다음과 같다.
- Gate 3 precursor 규칙, Gate 4 hard evidence 경계, Gate 5 output policy, Gate 6B taxonomy/action policy가 공통으로 참조할 `canonical result object`를 정의한다.
- 결과를 단일 top1 family가 아니라 `다축 결과 모델`로 본다.
- operator-facing과 analyst-facing이 같은 underlying object를 서로 다른 projection으로 읽게 한다.

## 2. 사용 규칙
- 이 문서는 구현 스키마 강제 문서이기 전에, 상위 설계 계약 문서다.
- 어떤 artifact가 canonical result object의 전체를 다 보여줄 필요는 없다.
- 그러나 어떤 artifact도 canonical object에 없는 축을 임의로 발명해서 보여주면 안 된다.
- 어떤 축이 비어 있는 경우, `미확정`, `보류`, `추가 확인 필요`, `해당 없음` 중 하나로 내려야 한다.
- `원인`, `현상`, `범위`, `행동`, `안전`, `확신도`는 같은 축이 아니므로 한 칼럼에 접지 않는다.

## 3. 상태
- 상태: `draft`
- 현재 목적:
  - Gate 5 output policy와 Gate 6B policy lock의 공통 기반을 마련
- 아직 하지 않는 것:
  - csv/xlsx schema patch
  - runtime 코드 patch
  - top1/top2 ranking rule patch

## 4. 왜 canonical result model이 필요한가
현재까지 드러난 문제:
- 원인 축과 현상 축이 섞인다.
- maintenance lane과 safety/control lane이 섞인다.
- panel-local과 common-cause가 섞인다.
- event semantics 결과와 operator-facing 결과가 같은 row에서 겹친다.

이 문제를 줄이려면, 결과를 적어도 다음처럼 분리해야 한다.
- `지금 무슨 상태인가`
- `왜 그렇게 읽히는가`
- `어디 범위의 문제로 보이는가`
- `무엇을 해야 하는가`
- `얼마나 확실한가`

## 5. canonical result object의 최상위 구조

### 5.1 기본 원칙
한 row의 canonical result는 아래 축들의 조합이다.

1. `state_axis`
2. `evidence_axis`
3. `cause_axis`
4. `phenotype_axis`
5. `temporal_axis`
6. `scope_axis`
7. `action_axis`
8. `confidence_axis`
9. `provenance_axis`

### 5.2 축별 역할
| 축 | 질문 | 같은 것으로 접으면 안 되는 것 |
| --- | --- | --- |
| `state_axis` | 지금 운영 상태가 무엇인가 | 원인 후보 |
| `evidence_axis` | 어떤 신호/증거 경로로 그렇게 봤는가 | 현장 조치 |
| `cause_axis` | 원인에 가장 가까운 해석은 무엇인가 | 현상 축 |
| `phenotype_axis` | 전기적/시계열 현상은 무엇인가 | root cause |
| `temporal_axis` | 시간 전개는 무엇인가 | 현재 상태 |
| `scope_axis` | 문제 범위는 어디까지인가 | 행동 권고 |
| `action_axis` | 무엇을 해야 하는가 | 상태 자체 |
| `confidence_axis` | 얼마나 확실한가 | 근거 상세 |
| `provenance_axis` | 어떤 layer/artifact에서 왔는가 | 상태 등급 |

## 6. 축별 canonical field 정의

### 6.1 `state_axis`
필드:
- `operational_state`
- `state_lane`

의미:
- `operational_state`는 operator-facing에서 가장 먼저 읽는 상태
- `state_lane`은 maintenance / safety / analyst 보조처럼 이 상태가 속한 lane

허용 예:
- `정상`
- `전조 흔적`
- `precursor candidate`
- `고위험 관찰`
- `고장 신호`
- `확정`
- `보류`
- `원인 미확정`

금지:
- 원인명을 여기 직접 넣기
- `vdrop`, `critical_source`, `shape_only` 같은 내부 설명 신호를 상태로 승격하기

### 6.2 `evidence_axis`
필드:
- `evidence_tier`
- `primary_evidence_path`
- `supporting_evidence`
- `blocked_by_missing_evidence`

의미:
- 어떤 tier의 증거가 있는지
- 주 증거 경로가 무엇인지
- 보조 근거가 무엇인지
- 무엇이 없어서 더 강한 판정을 못 하는지

예:
- `evidence_tier`: `trace`, `candidate`, `boundary`, `strong`, `confirmed`, `final`
- `primary_evidence_path`: `warning_accumulation`, `critical_confirmed_path`, `final_fault_path`
- `supporting_evidence`: `vdrop explanation`, `degradation pattern`, `legacy source`
- `blocked_by_missing_evidence`: `scope unavailable`, `external sensor unavailable`

### 6.3 `cause_axis`
필드:
- `problem_class`
- `operational_category`
- `candidate_ranked`

의미:
- `problem_class`:
  최상위 문제 대분류
- `operational_category`:
  operator-facing 운영 분류
- `candidate_ranked`:
  analyst-facing top1/top2/top3 후보

예:
- `problem_class`: `electrical`, `shape`, `instability`, `common_cause`, `control`, `unknown`
- `operational_category`: `음영`, `오염`, `다이오드`, `접속`, `센서`, `MLPE 응답`, `외부 전원`, `원인 미확정`

금지:
- `problem_class`와 `operational_category`를 같은 칼럼에서 top1 경쟁시키기

### 6.4 `phenotype_axis`
필드:
- `electrical_phenotype`
- `signal_summary`

의미:
- 전기적/시계열 현상을 말하는 축

예:
- `전압강하형`
- `전류단절형`
- `출력붕괴형`
- `전압 유지 + 전류 저하형`
- `간헐 회복/재발형`
- `dead-like`
- `shape-only anomaly`

금지:
- phenotype를 root cause처럼 확정 표현하기

### 6.5 `temporal_axis`
필드:
- `event_type`
- `terminal_pattern`
- `stage`

의미:
- 사건유형, 최종고장양상, 그리고 현재 사건 단계

예:
- `event_type`: `전조형 고장`, `급작 고장`, `미정`
- `terminal_pattern`: `진행성 악화`, `급격 종료`, `급작 발생`, `미정`
- `stage`: `trace`, `candidate`, `pre-fault high risk`, `fault signal observed`, `confirmed`

주의:
- `stage`는 현재 시점 상태이고,
- `event_type`/`terminal_pattern`은 사건 해석이다.

### 6.6 `scope_axis`
필드:
- `locus`
- `common_cause_flag`
- `control_scope_candidate`

의미:
- 문제 범위
- 공통원인 여부
- 제어/차단이 필요하다면 어느 범위까지 검토해야 하는지

예:
- `locus`: `모듈`, `서브스트링`, `MLPE 장치`, `그룹`, `인버터/전력변환`, `외부`, `미정`
- `common_cause_flag`: `yes`, `no`, `unknown`
- `control_scope_candidate`: `모듈`, `스트링`, `접속반`, `사이트`, `해당 없음`

### 6.7 `action_axis`
필드:
- `maintenance_lane`
- `safety_lane`
- `next_check_items`

의미:
- maintenance action과 safety/control action을 분리

예:
- `maintenance_lane`:
  `monitor_only`, `singleton_review`, `common_cause_review`, `maintenance_candidate`, `세척 확인`, `배선 점검`, `MLPE 점검`
- `safety_lane`:
  `none`, `sensor_check`, `remote_shutdown_review`, `module_shutdown_candidate`, `string_shutdown_candidate`, `fire_safety_policy_review`
- `next_check_items`:
  현장 점검자/분석가에게 주는 구체 확인 목록

금지:
- maintenance와 safety/control을 같은 단일 `action` 칼럼으로 합치기

### 6.8 `confidence_axis`
필드:
- `confidence_level`
- `competition_state`
- `abstain_reason`

의미:
- 얼마나 확실한지
- 후보가 얼마나 경합 중인지
- 왜 더 강하게 못 말하는지

예:
- `confidence_level`: `low`, `medium`, `high`, `unknown`
- `competition_state`: `single dominant`, `top2 close`, `multi-way`, `not applicable`
- `abstain_reason`: `missing scope`, `missing event history`, `common-cause unresolved`, `sensor unavailable`

### 6.9 `provenance_axis`
필드:
- `source_layer`
- `artifact_class`
- `officiality`

의미:
- 이 결과가 어느 layer에서 온 것인지
- 어느 종류의 artifact에 투영되는지
- official / analyst / mixed 중 어디에 속하는지

예:
- `source_layer`: `live`, `raw-only`, `event-semantics`, `analyst-derived`
- `artifact_class`: `current`, `precursor_report`, `raw_only_fault_signal_report`, `detailed`, `master_guide`
- `officiality`: `official`, `analyst`, `narrative`

## 7. 최소 canonical object 예시

### 7.1 precursor candidate 예시
```text
state_axis:
  operational_state = precursor candidate
  state_lane = maintenance
evidence_axis:
  evidence_tier = candidate
  primary_evidence_path = warning_accumulation
  supporting_evidence = [prefault accumulation, relative output deviation]
  blocked_by_missing_evidence = []
cause_axis:
  problem_class = electrical
  operational_category = 접속
  candidate_ranked = [접속·부분개방형, 센서·피드백형, 원인미확정]
phenotype_axis:
  electrical_phenotype = 전압 유지 + 전류 저하형
  signal_summary = 정오대 출력비 저하가 반복됨
temporal_axis:
  event_type = 미정
  terminal_pattern = 미정
  stage = candidate
scope_axis:
  locus = 모듈
  common_cause_flag = no
  control_scope_candidate = 해당 없음
action_axis:
  maintenance_lane = singleton_review
  safety_lane = none
  next_check_items = [배선/커넥터 확인, MLPE 응답 기록 확인]
confidence_axis:
  confidence_level = medium
  competition_state = top2 close
  abstain_reason = none
provenance_axis:
  source_layer = raw-only
  artifact_class = precursor_report
  officiality = analyst
```

### 7.2 hard evidence 예시
```text
state_axis:
  operational_state = 고장 신호
  state_lane = maintenance
evidence_axis:
  evidence_tier = confirmed
  primary_evidence_path = critical_confirmed_path
  supporting_evidence = [vdrop explanation]
  blocked_by_missing_evidence = []
cause_axis:
  problem_class = electrical
  operational_category = 다이오드
  candidate_ranked = [다이오드·서브스트링형, 접속·부분개방형, 원인미확정]
phenotype_axis:
  electrical_phenotype = 전압강하형
  signal_summary = 전압 저하 기반 강한 전기 신호
temporal_axis:
  event_type = 전조형 고장
  terminal_pattern = 급격 종료
  stage = fault signal observed
scope_axis:
  locus = 모듈
  common_cause_flag = no
  control_scope_candidate = 모듈
action_axis:
  maintenance_lane = maintenance_candidate
  safety_lane = remote_shutdown_review
  next_check_items = [현장 점검, MLPE/모듈 이상 확인]
confidence_axis:
  confidence_level = high
  competition_state = single dominant
  abstain_reason = none
provenance_axis:
  source_layer = raw-only
  artifact_class = raw_only_fault_signal_report
  officiality = analyst
```

## 8. projection 규칙

### 8.1 operator-facing projection
operator-facing artifact는 아래 축만 직접 노출해도 된다.
- `state_axis.operational_state`
- `cause_axis.operational_category`
- `phenotype_axis.electrical_phenotype` 또는 완곡한 설명
- `action_axis.maintenance_lane`의 축약 버전
- `confidence_axis`의 축약 버전

원칙:
- `candidate_ranked` 전체를 다 보여주지 않는다.
- `abstain_reason`은 필요할 때 `추가 확인 필요`로 완곡화한다.
- `provenance_axis`는 기본 숨김이지만 artifact 이름/설명으로 간접 노출한다.

### 8.2 analyst-facing projection
analyst-facing artifact는 canonical object 대부분을 노출할 수 있다.

원칙:
- `problem_class`, `operational_category`, `candidate_ranked`, `electrical_phenotype`, `locus`, `common_cause_flag`, `blocked_by_missing_evidence`, `abstain_reason`를 함께 볼 수 있다.

### 8.3 narrative/master projection
master report는 결과 객체 자체를 모두 보여주지 않는다.

역할:
- 각 artifact가 canonical object의 어느 축을 보여주는지 설명하는 안내서

## 9. null / unknown / abstain 규칙

### 9.1 `unknown`
- 해당 축을 현재 판단할 정보가 없음

### 9.2 `not_applicable`
- 이 row/상태에 그 축이 적용되지 않음

### 9.3 `abstain`
- 판단할 수는 있으나, 증거 부족/충돌 때문에 direct label을 유보

규칙:
- `unknown`과 `abstain`은 다르다.
- `abstain`은 decision이며, `unknown`은 정보 상태다.

## 10. 꼭 남겨야 하는 분리
- `state_axis`와 `cause_axis`
- `phenotype_axis`와 `cause_axis`
- `maintenance_lane`과 `safety_lane`
- `locus`와 `common_cause_flag`
- `evidence_tier`와 `confidence_level`
- `event_type/terminal_pattern`과 `stage`
- `source_layer/officiality`와 `operational_state`

## 11. 현재 코드/문서 기준으로 이 모델이 해결하는 것
- Gate 5가 artifact별 audience만 잠그고 결과 객체는 비워 둔 문제를 메운다.
- Gate 6가 taxonomy inventory만 있고 최상위 결과 구조가 없던 문제를 메운다.
- Gate 3/4에서 event semantics와 operator-facing semantics가 섞이던 문제를 완화한다.
- maintenance action과 safety/control action을 같은 result field에 접지 않게 한다.

## 12. Decision Log에 바로 올릴 질문
- `operational_state`의 allowed enum을 얼마나 넓게 둘 것인가
- `problem_class`와 `operational_category`를 모두 operator-facing에 보여줄 것인가
- `control_scope_candidate`를 scope_axis에 둘지 action_axis에 둘지
- `event_type/terminal_pattern` direct field의 operator-facing 금지와 `softened secondary summary`의 조건부 허용 범위는 [DL-20260422-008](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md), [DL-20260422-009](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 로 잠겼다.
- 남은 질문은 이 softened summary를 canonical result object의 explicit field로 둘지, artifact projection 단계에서만 계산되는 secondary field로 둘지다.
- `confidence_level`과 `competition_state`를 separate field로 유지할지
- `provenance_axis`를 csv artifact에 explicit 칼럼으로 둘지, naming/guide로만 처리할지

## 13. Gate 2B 체크리스트
- 하나의 결과가 단일 top1 family로 과압축되지 않는가
- 원인, 현상, 범위, 행동, 안전, 확신도가 분리되어 있는가
- operator-facing projection과 analyst-facing projection이 같은 underlying object를 공유하는가
- output policy가 canonical object보다 먼저 의미를 발명하지 않는가
- Gate 6B taxonomy/action lock이 이 object 위에서 내려앉을 수 있는가

## 14. 근거 source
- [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)

## 15. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 2A observability / evidence availability matrix:
  - [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
- Gate 2C existing signal score map:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- Gate 4A event semantics / operator semantics contract:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- Gate 6 taxonomy/action survey:
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)

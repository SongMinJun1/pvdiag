<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1

## 1. 목적
Gate 6 survey에서 드러난 누락과 혼선을 출발점으로, Gate 0~6 전체 설계가 서로 어떤 숨은 가정을 공유하고 있는지 다시 감사한다.

이 문서의 목적은 다음 셋이다.
- `Gate 6의 허점`이 Gate 3~5 이전 단계의 허점인지, 아니면 Gate 6 자체의 누락인지 구분한다.
- 현재 로드맵이 너무 선형적으로 읽히는 지점을 찾아낸다.
- 이후 알고리즘 패치 전에 반드시 다시 잠가야 하는 설계 게이트를 정리한다.

## 2. 조사 계기
이번 감사는 아래 문제의식에서 시작됐다.
- Gate 6에서 누락된 축이 생각보다 많다.
- 그렇다면 Gate 3 precursor 규칙, Gate 4 hard evidence 경계, Gate 5 output policy도 그 누락된 축을 전제로 잘못 잠갔을 수 있다.
- 설계 단계의 허점을 늦게 발견하면, report/schema patch 이후에 알고리즘과 문서를 다시 크게 되돌릴 수 있다.

## 3. 조사 범위
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 문서:
  - [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- 코드/회의록 근거:
  - [panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
  - [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
  - [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
  - [3사 회의록.md](</Users/b9gc/Documents/1. 현장 시스템과 현재 구축 상태/3사 회의록.md>)

## 4. 핵심 결론
결론은 단순하다.

- Gate 6의 허점은 Gate 6만의 문제가 아니다.
- 현재 설계는 `선형 게이트`처럼 적혀 있지만, 실제로는 `다축 결과 모델`이 먼저 잠기지 않으면 Gate 3~5가 다시 흔들린다.
- 따라서 지금까지 쓴 Gate 1~5 문서는 폐기할 수준은 아니지만, `상호 의존성`과 `되돌림 규칙`을 더 강하게 반영해야 한다.

즉,
- `로직이 완전히 틀렸다`기보다는
- `게이트 간 전제 관계가 충분히 명시되지 않았다`
가 더 정확한 진단이다.

## 5. High-Severity 설계 허점

### 5.1 허점 A. Gate 순서가 실제보다 너무 선형적으로 적혀 있다
현재 상위 로드맵은 다음처럼 읽힌다.
- Gate 3 precursor 규칙
- Gate 4 hard evidence 경계
- Gate 5 output policy
- Gate 6 taxonomy/action

하지만 Gate 6 survey는 이미 다음을 보여준다.
- 원인 축과 현상 축이 섞여 있다.
- maintenance lane과 safety/control lane이 섞여 있다.
- panel-local과 common-cause가 섞여 있다.
- MLPE 특성 축이 단순 cause label에 흡수되고 있다.

이 네 가지는 모두 Gate 3~5의 전제를 흔든다.

예시:
- Gate 3에서 `precursor candidate`를 올릴 때, 공통원인과 panel-local을 분리하지 못하면 승격 규칙 자체가 흔들린다.
- Gate 4에서 `hard evidence`를 operator-facing으로 어떻게 부를지 정할 때, maintenance lane과 safety lane이 분리되지 않으면 상태 의미가 과장되거나 누락된다.
- Gate 5에서 어떤 artifact에 어떤 축을 노출할지 तय할 때, top-level result object가 단일 축인지 다축인지가 먼저 정해져야 한다.

판정:
- `Gate 6A survey`는 Gate 6 뒤 단계가 아니라, Gate 3~5를 재검토하게 만드는 교차 게이트 입력이다.

### 5.2 허점 B. 다축 결과 모델이 상위 계약으로 명시되지 않았다
Gate 6 survey는 최소 다음 축이 필요하다고 본다.
- Cause Axis
- Electrical Phenotype Axis
- Temporal Axis
- Scope / Locus Axis
- Safety / Control Axis
- Actionability Axis
- Confidence / Evidence Axis

그런데 Gate 3, 4, 5는 아직 암묵적으로 더 단순한 결과 모델을 전제한다.

문제:
- Gate 3은 주로 시간/경고/승격 축을 본다.
- Gate 4는 hard evidence tier를 본다.
- Gate 5는 artifact별 노출 정책을 본다.
- 하지만 셋 사이를 묶는 `canonical result object`는 아직 없다.

그래서 생기는 위험:
- 하나의 artifact에 `원인`, `현상`, `범위`, `행동`, `안전`이 어떤 형태로 같이 들어가야 하는지 기준이 없다.
- Gate 5 output policy가 사실상 Gate 6B 결과 모델을 먼저 요구한다.

판정:
- Gate 6B는 taxonomy lock이 아니라, 사실상 `multi-axis result model lock`이어야 한다.

### 5.3 허점 C. 관측 가능성/증거 가용성 게이트가 없다
회의록은 분명히 다음을 함께 보라고 말한다.
- 전압, 전류, 온도, 위치, 시계열 정보
- 외부 센서
- 자동 차단/수동 차단/원격 차단 맥락

하지만 현재 Gate 문서들에는 다음이 없다.
- 어떤 분류가 어떤 센서/신호 조합 없이는 말해지면 안 되는가
- 어떤 lane은 전기 데이터만으로 충분한가
- 어떤 lane은 외부 센서나 운영 이벤트 없이는 보류해야 하는가

이 허점은 크다.

예시:
- `설치 초기 불량 가능성`
- `외부 센서/외부 화재 감지 연계`
- `접속반/차단 범위 확장 필요`
- `작업일/운영 이벤트 영향`

이런 항목은 전기 패턴만으로는 직접 잠그기 어렵다.

판정:
- Gate 2와 Gate 6 사이에 `Observability / Evidence Availability Matrix`가 별도 필요하다.

### 5.4 허점 D. event semantics와 operator-facing semantics의 계약이 약하다
Gate 3과 Gate 4는 둘 다 `runtime event semantics`와 `operator-facing interpretation`을 분리하려고 한다.
하지만 아직 `공식 계약 문서` 수준으로 잠기진 않았다.

문제:
- event semantics에서 fault event를 닫는 기준
- operator-facing에서 지금 보여줄 상태를 정하는 기준
- raw-only 분석 우주에서 retrospective하게 붙는 상태

이 세 층의 관계가 여전히 독립 문서에 흩어져 있다.

위험:
- 같은 `fault_like_day`가
  - event semantics에선 trigger 보조 축,
  - operator-facing에선 설명 신호,
  - raw-only에선 경계 신호
  로 읽히는데, 이 차이가 상위 계약으로 고정돼 있지 않으면 다시 표면 wording 문제로 돌아간다.

판정:
- Gate 4 뒤에 `Event Semantics / Operator Semantics Contract`가 별도 필요하다.

### 5.5 허점 E. 차단 범위와 개입 범위가 taxonomy 바깥에 남아 있다
회의록은 차단 범위를 강하게 말한다.
- 모듈 차단
- 스트링/접속반 차단
- 발전 손실 최소화 vs 화재 안전 우선
- 외부 센서 연계

그런데 현재 Gate 6 survey에서는 이 축이 inventory로만 정리돼 있고, 아직 상위 policy로 승격되지 않았다.

이건 단순 액션 추천 문제가 아니다.

이유:
- `모니터링`
- `현장 점검`
- `모듈 차단 후보`
- `스트링/접속반 차단 후보`
- `화재안전 우선 정책 검토`

이들은 같은 종류의 결과가 아니다.
일부는 maintenance lane이고, 일부는 safety/control lane이다.

판정:
- Gate 6B는 `taxonomy/action lock`만으로 부족하고, `intervention scope / control policy`까지 다뤄야 한다.

### 5.6 허점 F. common-cause / locus 정책이 Gate 3~6 전체를 관통하는데 독립 게이트가 없다
회의록과 Gate 6 survey 모두 다음을 강조한다.
- 모듈 국소
- 서브스트링 국소
- MLPE 장치 국소
- 그룹/인버터
- 외부 계통
- 공통원인

현재는 이 축이 Gate 6 scope/locus axis에 들어가 있지만, 사실은 더 앞단에 영향을 준다.

예시:
- precursor 승격에서 common-cause를 직접 제외할지
- hard evidence에서 common-cause면 panel-local 고장 신호로 낮춰야 하는지
- official artifact에 panel-local처럼 내보내지 말아야 하는지

판정:
- `scope/locus/common-cause policy`는 Gate 3, 4, 5 모두의 선행 조건이다.

### 5.7 허점 G. 보류/미확정 정책이 상위 문서에는 있으나 Gate 규칙 안에 충분히 흡수되지 않았다
상위 로드맵에는 `보류/미확정 정책`이 있다.
하지만 Gate 3~6 본문에서는 아직 이 상태가 일급 상태처럼 쓰이지 않는다.

위험:
- 축이 늘어날수록 `확신도 낮음`, `원인미확정`, `공동상위후보`, `추가 센서 필요`, `작업일 영향 의심` 같은 상태가 늘어난다.
- 그런데 게이트 규칙이 binary하게 잠기면 다시 억지 승격이나 과도한 top1 표시로 돌아간다.

판정:
- `abstain / unknown / needs-more-evidence`는 Gate 6의 후처리가 아니라 Gate 3~6 전체를 통과하는 공통 상태여야 한다.

## 6. Medium-Severity 설계 허점

### 6.1 Gate 5 output policy가 다축 결과 모델보다 먼저 잠겨 있다
현재 Gate 5는 artifact audience, row universe, wording을 잘 정리했지만, 아직 결과 객체의 축 수가 완전히 잠기기 전이다.

그래서 Gate 5는 고정 정책이라기보다 `provisional display policy`에 가깝다.

### 6.2 Gate 6 survey는 inventory는 충분하지만 반례 기반 압박이 아직 약하다
누락 범주 목록은 좋다.
하지만 아직 다음이 필요하다.
- 이 범주가 실제로 기존 Gate 3/4 규칙을 깨는 사례
- 어떤 artifact에서 오해를 만드는지
- 어떤 slice에서 더 자주 발생하는지

### 6.3 Gate 1 glossary의 용어는 좋아졌지만 다축 축 이름이 아직 외부 표현으로 잠기지 않았다
`Cause Axis`, `Electrical Phenotype Axis`, `Scope / Locus Axis` 등 내부 설계 용어는 생겼다.
하지만 어떤 축이 operator-facing 표면까지 올라올지 아직 안 잠겼다.

## 7. 이번 감사로 드러난 핵심 되돌림 규칙

### 7.1 Gate 6A는 Gate 3~5를 재개방할 수 있다
다음이 발견되면 Gate 3~5는 다시 열려야 한다.
- 새로운 축 추가
- maintenance vs safety lane 충돌
- common-cause와 panel-local 혼동
- top-level result object 구조 변경
- observability requirement 변경

### 7.2 Gate 5는 Gate 6B 이후에도 정합성 갱신이 필요하다
Gate 6B 문서가 생겼다고 해서 Gate 5가 자동으로 잠기는 것은 아니다.

현재 상태:
- Gate 5는 Gate 2B, Gate 4A, Gate 6B를 반영한 `동기화 대상 working draft`다.

정합성 완료 조건:
- 결과 객체의 축 수와 우선순위가 정해짐
- maintenance/safety lane 분리 확정
- operator-facing에 몇 축까지 보여줄지 확정
- Gate 5 상태/용어/다음 단계가 Gate 6B 기준으로 갱신됨

### 7.3 Gate 3/4 규칙은 scope/locus 정책이 잠기기 전까지 provisional이다
특히 다음은 scope/locus 정책에 영향받는다.
- precursor 승격 제외 규칙
- hard evidence operator-facing 승격 규칙
- raw-only fault signal report row universe

## 8. 로드맵 수정 제안

### 8.1 수정된 메인 라인
1. Gate 0. 범위 고정
2. Gate 1. 용어/역할 고정
3. Gate 2. signal role matrix
4. Gate 2A. observability / evidence availability matrix
5. Gate 2B. canonical multi-axis result model
6. Gate 3. precursor promotion rule
7. Gate 4. hard evidence boundary
8. Gate 4A. event semantics vs operator semantics contract
9. Gate 5. output policy
10. Gate 6A. taxonomy/action/safety/control survey
11. Gate 6B. taxonomy/action/control policy lock
12. Gate 7. implementation order lock

### 8.2 Gate 간 피드백 규칙
- Gate 6A는 Gate 2B, 3, 4, 5를 재개방할 수 있다.
- Gate 2A observability 요구가 바뀌면 Gate 3과 Gate 6B를 다시 본다.
- Gate 4A semantics contract가 바뀌면 Gate 5 wording 정책을 다시 본다.
- Gate 6B가 top-level result object를 바꾸면 Gate 5 artifact schema를 다시 본다.

### 8.3 지금 당장 멈춰야 하는 것
아래는 더 잠그기 전에 멈추는 게 맞다.
- action recommendation을 더 세분화하는 코드 패치
- operator-facing taxonomy를 top1/top2로 굳히는 패치
- safety/control lane을 maintenance lane과 같은 report column에 고정하는 패치
- observability requirement 없이 새 분류군을 확정하는 패치

## 9. Decision Log에 바로 올릴 질문
- Gate 6A survey 결과를 보고, Gate 2A observability matrix를 별도 Gate로 만들 것인가
- top-level result object는 `문제 대분류 + 운영 분류 + 현상 축 + 범위 축 + action lane + confidence` 조합이 되는가
- `common-cause`는 cause family가 아니라 scope/locus axis로 강제 이동시킬 것인가
- safety/control lane은 maintenance lane과 완전히 다른 artifact lane으로 분리할 것인가
- `fault_like_day`는 어디까지 event semantics 전용으로 남기고 어디부터 operator-facing에서 금지할 것인가
- `원인미확정`과 `needs-more-evidence`를 같은 상태로 볼 것인가

## 10. 바로 해야 할 후속 작업
1. decision log 1호를 Gate 5 / Gate 6B / cross-gate gatekeeper 기준으로 사용
2. Gate 6A survey 결과를 [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md) 와 함께 사용
3. 알고리즘 패치 전, decision log 1호에 남은 `보류 질문`을 추가 decision으로 분리할지 결정
   - current/master overlap은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md) 로 잠겼다.
   - raw-only direct exposure / master direct link 범위는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md) 로 잠겼다.
   - detailed definitions operator guidance 범위는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md) 로 잠겼다.
   - operator-facing event semantics exposure 범위는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md) 로 잠겼다.
   - official current의 softened event summary 조건부 노출 규칙은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 로 잠겼다.
4. build/release/smoke sync 범위를 결정
5. release/final_delivery 문서군의 runtime 설명 동기화 범위는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1.md) 로 최소 범위 잠금됐다.
6. stable/runtime mapping note의 spec 승격은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md) 로 잠겼다.

## 11. 이번 감사의 판정
- Gate 1~5가 무효는 아니다.
- 하지만 `지금 그대로 알고리즘 패치로 직행하면 크게 돌아갈 가능성`은 충분히 있다.
- Gate 2A / 2B / 4A / 6B 문서는 이제 생겼다.
- `DL-20260422-002`로 stable/runtime contract boundary도 잠겼다.
- Gate 7 implementation order lock도 이제 생겼다.
- `DL-20260422-003`로 stable/handoff boundary note 최소 패치 범위도 잠겼고, stable 문서군에 최소 경계 문구가 반영됐다.
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md) 로 반례 세트 V1도 생겼다.
- 따라서 현재 단계의 최우선은 `새 Gate 문서 추가`가 아니라, `반례 세트 활용 + existing signal->score map 정리 -> build/release/smoke sync 범위 확정 -> MLPE ambiguous/common-cause 반례 seed 보강`이다.

## 12. 근거 source
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- [OPS_CRITICAL_ACTIONABILITY_V3.md](/Users/b9gc/pvdiag/docs/OPS_CRITICAL_ACTIONABILITY_V3.md)
- [3사 회의록.md](</Users/b9gc/Documents/1. 현장 시스템과 현재 구축 상태/3사 회의록.md>)

## 13. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- decision log 1호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- decision log 3호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md)
- Gate 6 survey:
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- Gate 7 implementation order lock:
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- Gate 2C existing signal score map:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)
- Gate 5 artifact/schema patch checklist:
  - [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- 브랜치/파킹 로트 템플릿:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1

## 1. 목적
- 본 문서는 `MLPE runtime redesign`에서 실제 패치를 어떤 순서로 넣어야 하는지 잠그는 구현 순서 문서다.
- 목적은 아래 다섯 가지다.
  - 문서 결정을 코드 패치 순서로 번역한다.
  - `docs-only 정합성 패치`, `artifact/schema 패치`, `알고리즘 패치`, `release 재생성`의 순서를 고정한다.
  - 아직 잠기지 않은 질문 때문에 섣불리 들어가면 안 되는 패치를 명확히 금지한다.
  - 여러 패치 묶음이 동시에 움직일 때 어느 문서/결정을 먼저 따라야 하는지 정한다.
  - Gate 5 projection policy를 실제 patch checklist로 내려앉힐 기준을 만든다.

## 2. 이 문서가 전제하는 상위 기준
- 상위 로드맵: [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- current/raw-only/operator semantics lock: [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- stable/runtime contract boundary lock: [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- signal role / observability / result model:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- semantics / output / taxonomy lock:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)

## 3. 상태
- 상태: `working draft`
- 의미:
  - 현재까지 잠긴 Gate/decision을 반영한 구현 순서 초안이다.
  - `Gate 5 checklist`, `stable boundary note 최소 패치 범위`, `반례 세트 V1`까지는 존재한다.
  - `MLPE ambiguous`, `common-cause risk`의 초기 승인 seed는 생겼지만, 운영 이벤트 연계/현장 확인 seed는 아직 부족하므로 algorithm gating 단계는 여전히 보수적으로 진행해야 한다.
- 현재 우선 기준:
  - DL-001, DL-002가 Gate 7보다 우선한다.
  - stable/handoff 문서는 별도 계약으로 읽고, runtime redesign 패치를 stable 문서군에 직접 확장하지 않는다.

## 4. 기본 원칙
### 4.1 문서 결정이 먼저, 코드 패치가 나중
- Gate / decision log로 잠기지 않은 규칙은 코드에서 먼저 구현하지 않는다.

### 4.2 한 번에 한 층만 바꾼다
- 같은 패치 묶음에서 아래를 동시에 바꾸지 않는다.
  - 용어/가이드
  - artifact row universe
  - algorithm threshold/rule
  - taxonomy/action semantics

### 4.3 official current와 raw-only는 끝까지 분리
- 어떤 구현 단계에서도 raw-only artifact를 official current 대체물로 승격시키지 않는다.

### 4.4 stable/handoff와 runtime redesign는 별도 레인
- Gate 7의 기본 구현 대상은 runtime redesign 레인이다.
- stable/handoff 문서군 패치는 `boundary note` 수준을 넘기면 별도 decision이 필요하다.

## 5. 구현 레인
### 5.1 Lane A. 문서 정합성 / 용어 정리
- 목적:
  - stale wording, old artifact naming, accepted decision mismatch 제거
- 대표 파일:
  - `docs/OPS_CONALOG_*`
- 허용:
  - definitions 보정
  - stale next-step 정리
  - accepted/proposed 상태 갱신
- 금지:
  - 문서만으로 아직 미결인 알고리즘 규칙을 확정하는 것

### 5.2 Lane B. artifact/schema projection 패치
- 목적:
  - Gate 5 projection policy를 실제 파일명/컬럼명/definitions/master report에 반영
- 대표 파일:
  - [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
  - [build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)
  - [smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)
- 허용:
  - 파일명/컬럼명/guide wording
  - definitions 시트 갱신
  - master report 읽는 순서 갱신
- 금지:
  - precursor rule 자체 변경
  - hard evidence boundary 자체 변경

### 5.3 Lane C. semantics enforcement 패치
- 목적:
  - operator headline에서 event semantics 금지
  - raw-only/offical current 공식성 구분 enforcement
- 대표 파일:
  - `run_full_algorithm_pack.py`
  - 필요 시 release README / QUICKSTART / KNOWN_LIMITS
- 허용:
  - current/precursor/master wording 정리
  - operator/analyst exposure gating
- 금지:
  - stable path direct output contract 재정의

### 5.4 Lane D. algorithm gating 패치
- 목적:
  - Gate 3 / Gate 4 규칙을 실제 코드에 반영
- 대표 파일:
  - [research/prognostics/runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
  - 필요 시 [pv_ae/panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
- 선행 조건:
  - Gate 3 precursor 승격 규칙의 미결 질문이 더 좁아져 있어야 한다.
  - Gate 4 hard evidence 경계의 미결 질문이 더 좁아져 있어야 한다.
- 금지:
  - 반례 세트 없이 threshold/rule을 바로 조정

### 5.5 Lane E. taxonomy / action patch
- 목적:
  - Gate 6B policy lock을 실제 출력 컬럼/문구/axis projection에 반영
- 대표 파일:
  - `run_full_algorithm_pack.py`
  - heuristic 관련 문서/설명문
- 선행 조건:
  - Gate 5 projection checklist가 먼저 있어야 한다.
  - safety/control lane direct exposure 질문이 정리돼 있어야 한다.

### 5.6 Lane F. build / release / smoke sync
- 목적:
  - source, smoke, release artifact를 같은 계약으로 맞춤
- 대표 파일:
  - `research/prognostics/build_*`
  - `research/prognostics/smoke_test_*`
  - `release/conalog_full_runtime_v1/*`
- 규칙:
  - source patch만 넣고 build/release/smoke를 뒤로 미루지 않는다.

## 6. 권장 패치 순서
### 6.1 Step 0. 문서/결정 정합성
- 내용:
  - Gate / decision / mapping note / glossary 정합성 정리
- 완료 기준:
  - accepted/proposed 상태가 실제와 맞는다.
  - artifact naming이 모두 현재 기준과 맞는다.

### 6.2 Step 1. Gate 5 patch checklist 작성
- 내용:
  - Gate 5 projection policy를 실제 파일/컬럼/artifact별 checklist로 내린다.
- 산출물:
  - [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- 완료 기준:
  - artifact별로 `무엇을 바꾸고 무엇을 건드리지 말아야 하는지`가 체크리스트로 존재한다.

### 6.3 Step 2. Lane B/C docs-first runtime patch
- 내용:
  - runtime pack 쪽 이름/컬럼/guide/master/detailed definitions patch
  - operator/current/raw-only/precursor wording patch
- 대표 대상:
  - `run_full_algorithm_pack.py`
  - smoke/build 문서성 체크
- 완료 기준:
  - Gate 5, DL-001, DL-002와 모순 없는 artifact surface가 된다.

### 6.4 Step 3. stable/handoff boundary note 최소 패치 여부 결정
- 내용:
  - stable 문서군에 최소 경계 문구를 넣을지 별도 decision으로 잠근다.
- 완료 기준:
  - stable 레인을 건드릴지 말지 결정이 존재한다.

### 6.5 Step 4. 반례 세트 1차 작성
- 내용:
  - precursor / hard evidence / MLPE 특수 케이스 / common-cause / raw-only vs official 사례 묶음 작성
- 완료 기준:
  - algorithm gating patch 전에 최소 반례 세트가 준비된다.
- 현재 산출물:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- 남은 조건:
  - `MLPE ambiguous`에서 `센서·피드백형` 외에 `장치 응답 이상형` top1 또는 회복/재발 사례를 더 확보해야 한다.
  - `common_cause_risk`에서 운영 이벤트/통신 흔들림 연계 사례와 `group_off_event` 직접 중첩 사례를 더 확보해야 한다.
  - `official current`와 direct overlap하는 common-cause 사례는 `2026-04-22` tri-site scan 기준 아직 미관측이라 별도 수집이 필요하다.
  - BR-029 기준으로 provisional shortlist는 curated counterexample seed로 승격될 수 있지만, 이는 `exact missing family closure`와는 별개다.

### 6.6 Step 4A. existing signal -> score axis map 정리
- 내용:
  - 현재 있는 warning / hard evidence / suppressor / explanation 신호를 다축 score axis에 연결한다.
- 완료 기준:
  - `single signal -> direct label`이 아니라 `signal -> score -> projection`으로 설명 가능하다.
- 현재 산출물:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)

### 6.7 Step 5. Lane D algorithm gating patch
- 내용:
  - 필요 시 precursor 승격 / hard evidence 경계 코드 조정
- 조건:
  - Step 4 반례 세트가 먼저 존재해야 한다.
  - Step 4A signal-to-score map이 먼저 존재해야 한다.
  - BR-029 이후에는 provisional seed promotion criteria가 먼저 잠겨 있어야 한다.
  - 그 다음 `score-to-projection decision log`가 먼저 잠겨 있어야 한다.
  - 관련 decision log가 추가로 잠겨 있어야 한다.
  - [DL-20260422-012](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_012_V1.md) 기준으로 `prefault_B_effective`는 eligibility/explanation additive evidence까지만 허용되고, `고위험 관찰` direct trigger 승격은 별도 decision 전까지 보류한다.

### 6.8 Step 6. Lane E taxonomy/action patch
- 내용:
  - operator-facing과 analyst-facing 축을 실제 출력에 반영
- 조건:
  - safety/control lane 직접 노출 범위가 더 좁아져 있어야 한다.

### 6.9 Step 7. build / release / smoke / run sync
- 내용:
  - source patch를 build/release/smoke/run 결과까지 연결
- 최소 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `python research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
  - conalog 1회 실행 또는 paper pack 재생성 확인

## 7. 지금 바로 허용되는 패치
- Gate 5 projection policy를 checklist로 바꾸는 문서 패치
- runtime pack surface wording / guide / definitions patch
- master report read order 정리
- artifact 설명문 정정
- stable/runtime boundary note 필요 범위를 정하는 decision log 추가

## 8. 지금 보류해야 하는 패치
- precursor 승격 threshold 조정
- hard evidence precedence 변경
- `fault_like_day` semantics 변경
- `prefault_B_effective_days`를 단독 `고위험 관찰` threshold로 올리는 패치
- safety/control lane 직접 추천 문구 확대
- stable/handoff contract를 redesign semantics에 맞춰 재작성
- final delivery / one-click 전체 wording 최종화

## 9. 체크리스트
### 9.1 패치 시작 전
- 이 패치가 어느 Lane인지 분류했는가
- 상위 Gate / decision log가 이미 잠겼는가
- stable 레인과 runtime redesign 레인을 혼합하지 않는가

### 9.2 패치 중
- row universe를 바꾸지 않으면서 wording만 바꾸는지
- wording을 바꾸지 않으면서 rule을 슬쩍 바꾸고 있지 않은지
- build/smoke/release sync 범위를 놓치지 않았는지

### 9.3 패치 완료 후
- docs/source/build/release 중 어느 층까지 영향을 줬는지 기록했는가
- 새로운 decision log가 필요한 변경이었는지 확인했는가

## 10. 선행/후행 관계 요약
| 단계 | 선행 필요 | 후행 영향 |
| --- | --- | --- |
| Step 1 Gate 5 checklist | DL-001, DL-002, Gate 5 | Step 2, Step 6 |
| Step 2 runtime surface patch | Step 1 | Step 7 |
| Step 3 stable boundary note decision | DL-002, DL-003, mapping note | stable docs patch 여부 |
| Step 4 반례 세트 | Gate 3/4/6 survey | Step 4A, Step 5 |
| Step 4A signal-to-score map | Gate 2/3/4/6 + 반례 세트 | Step 5, Step 6 |
| Step 5 algorithm gating patch | Step 4 + Step 4A + 추가 decision | Step 6, Step 7 |
| Step 6 taxonomy/action patch | Step 1, Step 5 일부 | Step 7 |
| Step 7 build/release/smoke sync | 모든 source patch | 배포/검증 |

## 11. 지금 기준 다음 우선순위
1. `score-to-projection decision log` 잠금
2. `MLPE ambiguous`의 장치 응답 이상형 top1 / 회복 재발 exact seed 추가
3. `common_cause_risk`의 운영 이벤트 / `group_off_event` 연계 exact seed 추가
4. 그 다음에야 algorithm gating patch 검토

## 12. 관련 문서
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)

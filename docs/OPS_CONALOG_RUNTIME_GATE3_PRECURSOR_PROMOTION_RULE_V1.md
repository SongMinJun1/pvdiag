# OPS Conalog Runtime Gate 3 Precursor Promotion Rule V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 3 산출물인 `precursor 승격 규칙 초안`이다.
- 목적은 아래 다섯 가지다.
  - `전조 흔적`, `precursor candidate`, `고위험 관찰`, `고장 신호`를 서로 다른 상태로 잠근다.
  - 현재 runtime baseline이 어디서 precursor를 잡는지 문서로 남긴다.
  - 앞으로의 알고리즘 패치가 무엇을 바꾸는 패치인지 추적 가능하게 만든다.
  - operator-facing precursor report와 event 해석용 retrospective precursor를 분리한다.
  - Gate 4 hard evidence boundary를 정하기 전, precursor 쪽에서 먼저 금지해야 할 승격을 잠근다.

## 2. 사용 규칙
- 이 문서는 `precursor로 올릴 수 있는 상태 전이`를 잠그는 문서다.
- 이 문서가 잠기기 전에는 다음 패치를 금지한다.
  - precursor 승격 threshold 조정
  - `fault_like_day`를 precursor 또는 hard evidence 어느 한쪽으로 코드에서 재배치
  - precursor report inclusion 규칙 변경
- 이 문서가 잠기기 전에도 허용되는 작업은 아래다.
  - wording patch
  - lineage 확인
  - 반례 수집
  - decision log 등록

## 3. 상태
- 현재 상태:
  - `working draft`
- 의미:
  - 현재 baseline을 기준으로 작성된 초안이며, Gate 4 이후 일부 경계 표현은 재조정될 수 있다.

## 4. 먼저 분리해야 하는 세 가지 질문
### 4.1 질문 A. 전조 흔적이 있는가
- 의미:
  - warning 계열이나 prefault 계열 신호가 관측되었는가
- 아직 답하지 않는 것:
  - 운영상 precursor candidate로 올릴 것인가
  - hard evidence가 있는가

### 4.2 질문 B. 나중에 고장이 난 사건을 retrospective하게 보면 precursor가 있었는가
- 의미:
  - strict trigger 이전에 onset을 잡을 수 있는가
- 용도:
  - 사건유형을 `전조형 고장`으로 볼지, `급작 고장`으로 볼지
- 주의:
  - retrospective precursor는 현재 시점 precursor candidate와 동일하지 않다

### 4.3 질문 C. 현재 운영표에 precursor candidate로 올릴 것인가
- 의미:
  - hard evidence는 아직 없지만, 운영자가 추적/모니터링할 가치가 있는가
- 용도:
  - `fault_panel_result_precursor_report_v1.csv`
- 주의:
  - event 해석용 retrospective onset만으로 현재 precursor candidate가 되면 안 된다

## 5. 상태 사다리
| 상태 | 의미 | operator-facing 허용 표현 | artifact 기본 위치 |
| --- | --- | --- | --- |
| `비고장` | 유의미한 precursor 신호도 hard evidence도 없음 | 노출 안 함 또는 정상 관찰 | current/detailed 내부 |
| `전조 흔적` | warning 계열 신호는 있으나 운영 추적 대상으로 승격되진 않음 | 직접 노출 비권장 | detailed 위주 |
| `precursor candidate` | hard evidence는 없고, 운영 추적 가치가 있는 다축 누적 이상 | `전조 후보` | precursor report |
| `고위험 관찰` | precursor candidate 중 강도가 높거나 gap/반복성이 강해 우선 추적이 필요한 상태 | `고위험 관찰` | precursor report / summary |
| `고장 신호` | hard evidence 또는 그에 준하는 confirm path가 이미 존재 | `고장 신호` | raw-only fault signal report / current 설명 |
| `확정` | 운영 등급상 고장으로 본 상태 | `확정` | current / raw-only fault signal report |

## 6. Current Baseline
### 6.1 현재 runtime에서 쓰는 warning 계열
- primary warning:
  - `ews_warning`
  - `pre_alarm`
- secondary warning:
  - `pre_ews`
  - `prefault_B`
  - `prefault_cond_mid`
  - `prefault_cond_ae`
  - `prefault_cond_dtw`
  - `prefault_cond_ews`
  - `prealarm_cond_ae_mid_or_hi`
  - `prealarm_cond_dtw_mid_or_hi`
  - `prealarm_cond_hs_mid_or_hi`

근거:
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)

### 6.2 현재 strict trigger baseline
- current runtime은 아래 중 가장 이른 날짜를 `strict_trigger`로 둔다.
  - `first_critical_fault`
  - `first_final_fault`
  - `first_fault_like`

주의:
- 여기서 `fault_like_day`가 이미 trigger 축에 들어가 있기 때문에, Gate 4와 함께 가장 먼저 다시 검토해야 하는 경계다.

### 6.3 현재 retrospective onset baseline
- current runtime은 아래 우선순위로 onset을 잡는다.
  1. primary warning이 strict trigger 이전이고 gap이 `<= 120일`
  2. secondary warning이 strict trigger 이전이고 gap이 `7일 이상 120일 이하`
  3. `anom_subtype:degradation`가 strict trigger 이전에 존재

### 6.4 현재 fault status baseline
- current runtime은 아래처럼 상태를 만든다.
  - `has_final or has_critical or has_fault_like` 이면 `고장`
  - 그렇지 않고 earliest warning이 있으면 `미확정`
  - 둘 다 아니면 `비고장`

### 6.5 현재 precursor flag baseline
- current runtime은 아래 조건이면 `precursor_flag=1`로 둔다.
  - `fault_status == 고장`
  - `retrospective_onset is not None`

의미:
- 현재 baseline의 precursor_flag는 `운영 precursor candidate`가 아니라 `고장 사건을 retrospective하게 봤을 때 precursor가 있었는가`에 더 가깝다.

## 7. Gate 3에서 잠그려는 핵심 원칙
### 7.1 precursor는 hard evidence 이전 상태여야 한다
- `critical_fault`
- `critical_confirmed`
- `final_fault`

위 신호가 row 기준 현재 시점에 있으면, 그 row는 precursor candidate가 아니다.

### 7.2 retrospective precursor와 operator precursor candidate를 분리한다
- retrospective precursor:
  - 나중에 fault로 닫힌 사건을 설명하기 위한 onset
- operator precursor candidate:
  - 아직 hard evidence는 없지만 지금 추적해야 하는 상태

이 둘은 같은 필드를 재활용할 수 있어도, 같은 개념으로 취급하면 안 된다.

### 7.3 warning 하나만으로 바로 precursor candidate로 올리지 않는다
- `전조 흔적`과 `precursor candidate` 사이에 최소한 한 단계의 검토가 필요하다.
- 특히 secondary-only 신호는 sustain 또는 다축 누적 조건 없이 단독 승격하면 안 된다.

### 7.4 `fault_like_day`는 자동 승격 신호가 아니다
- `fault_like_day`는 경계 신호다.
- Gate 3 문맥에서는 아래를 잠근다.
  - `fault_like_day`만으로 operator precursor candidate를 올리지 않는다.
  - `fault_like_day`가 있었다는 이유만으로 retrospective precursor를 hard evidence와 동일시하지 않는다.

### 7.5 degradation fallback은 explanatory fallback이지 primary promotion path가 아니다
- `anom_subtype:degradation`는 useful하다.
- 하지만 degradation alone으로 operator precursor candidate를 대량 승격하면 안 된다.
- degradation은 아래 두 용도에 더 가깝다.
  - retrospective onset 설명
  - terminal pattern이 `진행성 악화`로 읽히는 이유 설명

### 7.6 common-cause / group-off는 직접 precursor 승격에서 제외한다
- group-off, site event, 공통원인성 패턴은 panel-local precursor 승격에서 직접 제외 또는 보류 처리한다.

## 8. Draft Promotion Logic
### 8.1 Step 0. Hard evidence exclusion
아래 중 하나라도 있으면 operator precursor candidate 승격을 중단한다.
- `critical_fault`
- `critical_confirmed`
- `final_fault`

결과:
- precursor report가 아니라 fault signal 쪽 검토 대상으로 보낸다.

### 8.2 Step 1. Warning trace detection
아래 중 하나라도 있으면 `전조 흔적` 상태로 둔다.
- primary warning 관측
- secondary warning 관측
- prefault 계열 관측

결과:
- 아직 precursor candidate는 아니다.

### 8.3 Step 2. Candidate promotion
`전조 흔적`을 `precursor candidate`로 승격하려면 아래 중 하나가 필요하다.
- primary warning이 존재하고, 공통원인/운영 이벤트가 아님
- 서로 다른 secondary warning family가 둘 이상 존재
- 같은 secondary family라도 sustain 또는 반복성이 확인됨
- `pre_alarm` 또는 `ews_warning`와 prefault 계열이 함께 존재

주의:
- exact sustain 일수는 이 문서에서 아직 잠그지 않는다.
- 다만 `secondary one-shot`은 candidate로 바로 올리지 않는다는 방향만 먼저 잠근다.

### 8.4 Step 3. High-risk upgrade
`precursor candidate`를 `고위험 관찰`로 올리려면 아래 요소를 본다.
- primary warning이 이미 존재
- gap이 충분히 길다
- 반복 이상이 누적된다
- degradation 또는 반복 전압 이탈 같은 설명 신호가 동반된다
- common-cause가 아니다

주의:
- `고위험 관찰`도 hard evidence는 아니다.
- `현장 점검 권고`보다 먼저 `모니터링 권고 강화`로 해석하는 것이 기본이다.

### 8.5 Step 4. Retrospective precursor for fault events
이미 fault event가 닫힌 패널에 대해서는 아래를 별도로 계산한다.
- strict trigger 이전 onset이 존재하는가
- onset source가 primary인지 secondary인지 degradation fallback인지
- gap이 어느 정도인가

결과:
- `전조형 고장` vs `급작 고장`
- `onset_confidence`
- `onset_method`

이 단계는 operator precursor candidate와 분리된 event semantics 단계다.

## 9. 승격 금지 규칙
- `critical_fault`가 있는 row를 precursor report에 넣지 않는다.
- `final_fault`가 있는 row를 precursor report에 넣지 않는다.
- `critical_confirmed`가 있는 row를 precursor report에 넣지 않는다.
- `fault_like_day` 단독으로 precursor candidate를 만들지 않는다.
- `event_A`를 precursor 승격 근거로 직접 노출하지 않는다.
- `v_drop` 단독으로 precursor candidate를 만들지 않는다.
- `anom_subtype:degradation` 단독으로 operator precursor candidate를 대량 승격하지 않는다.
- group-off/common-cause를 panel-local precursor로 번역하지 않는다.

## 10. 꼭 남겨야 하는 구분
### 10.1 `전조 흔적` vs `precursor candidate`
- 전조 흔적:
  - 신호는 있었지만 아직 운영 추적 대상으로 승격되진 않음
- precursor candidate:
  - hard evidence는 없고, 운영 추적 가치가 있음

### 10.2 `precursor candidate` vs `고위험 관찰`
- precursor candidate:
  - 추적 필요
- 고위험 관찰:
  - 같은 precursor 후보군 안에서도 우선순위가 높음

### 10.3 `고위험 관찰` vs `고장 신호`
- 고위험 관찰:
  - 여전히 hard evidence 이전 상태
- 고장 신호:
  - 이미 hard evidence가 존재

## 11. 현재 코드와 이후 코드 패치가 갈라지는 지점
### 11.1 현재 baseline
- `fault_like_day`가 trigger 축에 들어간다
- `고장`/`미확정`/`비고장`은 event semantics 관점에서 만들어진다
- precursor_flag는 event-level retrospective precursor에 가깝다

### 11.2 이후 패치에서 바꿔야 할 가능성이 높은 지점
- operator precursor candidate 산정용 별도 state 추가
- `fault_like_day`의 역할 재배치
- secondary-only promotion sustain 조건 추가
- `고위험 관찰` 등급을 report schema에 명시
- group-off/common-cause 보류 상태 추가

## 12. Decision Log에 바로 올릴 질문
- `fault_like_day`는 Gate 3 쪽인가, Gate 4 쪽인가
- `pre_alarm`은 primary warning으로 유지할 것인가
- secondary-only promotion에 필요한 최소 sustain 기준은 무엇인가
- `고위험 관찰`을 precursor report 안의 값으로 둘지, 별도 artifact로 뺄지
- degradation fallback을 event semantics 전용으로 고정할지
- `v_drop`가 precursor candidate 승격에 기여할 수 있다면 어떤 보조 조건이 필요한가

## 13. Gate 3 체크리스트
- precursor report row가 hard evidence current row와 섞이지 않는가
- operator precursor candidate와 retrospective precursor를 혼동하지 않는가
- secondary one-shot을 바로 precursor candidate로 올리지 않는가
- common-cause/group-off를 panel precursor로 잘못 읽지 않는가
- `고위험 관찰`이 hard evidence처럼 읽히지 않는가

## 14. 근거 source
- [runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
- [panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

## 15. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- Gate 1 용어 사전:
  - [OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE1_GLOSSARY_V1.md)
- Gate 2 signal role matrix:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
- Gate 4 hard evidence 경계 초안:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-009 | accepted | Gate 4A / Gate 5 / Gate 7 | official current softened event summary exposure condition | official current의 `사건 종결 요약`은 상시 노출이 아니라 `확정/고장` row에서만 채우는 조건부 secondary summary로 유지 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-009] official current softened event summary conditional exposure lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 4A / Gate 5 / Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- official current의 `사건 종결 요약` 같은 softened event summary를 모든 row에 항상 보여줄 것인가, 아니면 이미 닫힌 row에서만 조건부로 보여줄 것인가.

### 배경
- [DL-20260422-008](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)은 direct `event_type/terminal_pattern` 노출을 금지하고, official current에서만 완곡한 secondary summary를 제한적으로 허용했다.
- 현재 코드 [event_display_fields()](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py:637)는 이미 아래 조건으로 움직인다.
  - `운영 판정 == 확정`
  - 또는 `패널고장여부_ko == 고장`
- 즉 현재 구현은 `사건 종결 요약`을 모든 row에 상시 채우지 않고, 이미 닫힌 current row에만 채운다.

### 선택지
1. 선택지 A. official current 모든 row에 `사건 종결 요약`을 항상 노출한다
   - 장점:
     - 표면상 설명량이 늘어난다.
   - 단점:
     - watch/관찰/보류 row에도 retrospective event semantics가 새어 들어간다.
     - `operational_state`와 `event reconstruction`의 경계가 다시 흐려진다.
2. 선택지 B. official current에서 `사건 종결 요약`은 확정/고장 row에만 조건부로 채운다
   - 장점:
     - current semantics 중심을 유지한다.
     - 이미 닫힌 row에는 보조 설명력을 제공한다.
     - precursor/watch row에 event semantics가 과하게 새지 않는다.
   - 단점:
     - current 표만 훑을 때 일부 row는 summary가 비어 보일 수 있다.
3. 선택지 C. summary를 아예 제거한다
   - 장점:
     - 가장 보수적이다.
   - 단점:
     - 이미 닫힌 current row의 사건 해석 요약이 너무 약해진다.
     - [DL-20260422-008](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)의 제한적 허용 취지를 되돌린다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. `사건 종결 요약`은 official current에서 `secondary summary`로만 유지한다.
  2. 이 summary는 `운영 판정 == 확정` 또는 `패널고장여부_ko == 고장`인 row에서만 채운다.
  3. watch/관찰/보류 row, precursor-only row, 아직 닫히지 않은 row에는 기본 공란을 유지한다.
  4. `급락 종결 관측`, `점진 저하 누적` 같은 관측 축은 유지할 수 있지만, 그것만으로 `사건 종결 요약`을 강제로 채우지 않는다.
  5. precursor report와 master report의 operator 기본 읽기 흐름에는 본 summary를 확장 적용하지 않는다.

### 이유
- current semantics 보호:
  - operator-facing official current는 현재 상태를 우선 보여줘야 한다.
- retrospective leakage 억제:
  - 관측 플래그만으로 event summary를 상시 채우면 현재 상태와 사건 해석이 섞인다.
- 기존 코드와 정합:
  - 현재 구현이 이미 조건부 노출 방식이라, 이번 결정은 새로운 알고리즘 변경이 아니라 기준 잠금이다.

### 허용 패치
- current preview/current report에서 `사건 종결 요약은 확정 row에서만 채워진다`는 설명을 더 명확히 하는 패치
- code path가 본 조건을 더 명시적으로 드러내도록 주석/가드 문구를 보강하는 패치
- Gate 4A/5/7과 상위 로드맵 문서에서 본 결정을 반영하는 패치

### 금지 패치
- 관측 플래그만 있으면 모든 current row에 `사건 종결 요약`을 채우는 패치
- `사건 종결 요약`을 current headline/primary sorting field로 올리는 패치
- precursor/master의 operator 기본 읽기 흐름에 동일 요약을 상시 주입하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- 필수 아님.
- 현재 [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py:637) 는 이미 본 결정을 따른다.
- 이후 current preview summary 생성 규칙을 바꿀 때는 본 decision을 우선 기준으로 본다.

### 검증 계획
- 문서 검증:
  - Gate 4A/5/7과 상위 로드맵에서 본 결정을 모순 없이 참조하는지 확인
- 코드 검증:
  - `event_display_fields()`가 여전히 `확정/고장 row` 조건을 요구하는지 확인
- artifact 검증:
  - current preview의 `사건 종결 요약`이 모든 row에 상시 채워지지 않는지 확인
  - precursor report에는 동일 summary가 기본 노출되지 않는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - conalog 1회 실행 후 current/master/precursor/raw-only artifact 확인

### 롤백 트리거
- current preview에서 summary 공란이 과도해져 이미 닫힌 row조차 설명력이 떨어진다고 반복 보고되는 경우
- 조건부 노출 때문에 operator가 오히려 판단 흐름을 잃는다는 실사용 피드백이 누적되는 경우

### 남겨둔 보류 질문
- 없음
- 다음 residual question은 `softened event summary` 자체가 아니라, `release/final_delivery` 문서군에서 이 조건부 노출 기준을 어디까지 동기화할지다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

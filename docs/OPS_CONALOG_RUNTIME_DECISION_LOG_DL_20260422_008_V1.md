<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-008 | accepted | Gate 4A / Gate 5 / Gate 6B | operator-facing event semantics exposure | operator-facing artifact에서 direct `event_type/terminal_pattern`는 금지하고, official current에 한해 완곡한 secondary event summary만 제한적으로 허용 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-008] operator-facing artifact event semantics exposure range lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 4A / Gate 5 / Gate 6B
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- runtime redesign의 operator-facing artifact에서 `event_type` / `terminal_pattern`을 어디까지 허용할 것인가.

### 배경
- DL-001은 operator-facing headline에서 `event_type/terminal_pattern`을 금지했다.
- 하지만 current preview에는 이미 완곡화된 `사건 종결 요약` 컬럼이 존재하고, 이는 direct event field는 아니지만 event semantics를 요약한 secondary field다.
- 따라서 지금 필요한 결정은 아래 둘을 분리하는 것이다.
  1. direct event field(`사건유형`, `최종고장양상`, `event_type`, `terminal_pattern`)를 operator-facing에 허용할지
  2. 완곡화된 event summary를 official current의 보조 설명으로 제한적으로 허용할지

### 선택지
1. 선택지 A. operator-facing에서 event semantics를 완전히 숨긴다
   - 장점:
     - 가장 보수적이다.
     - current state와 retrospective interpretation이 절대 섞이지 않는다.
   - 단점:
     - 이미 닫힌 current 사례의 시간 해석 정보를 current preview에서 전혀 못 보게 된다.
     - `current_preview`의 `사건 종결 요약` 같은 완곡 요약도 금지되어 설명력이 과도하게 낮아진다.
2. 선택지 B. direct event field는 금지하되, official current에서만 완곡화된 secondary summary를 제한적으로 허용한다
   - 장점:
     - headline은 current semantics를 유지한다.
     - 이미 닫힌 current 사례에 대해 `전조 후 급격 종료` 같은 요약을 보조 정보로 유지할 수 있다.
     - precursor/operator watchlist에는 event semantics가 새지 않는다.
   - 단점:
     - 어디까지가 “완곡한 secondary summary”인지 추가 문서화가 필요하다.
3. 선택지 C. operator-facing에서도 direct event field를 제한적으로 허용한다
   - 장점:
     - 설명력이 높다.
   - 단점:
     - DL-001과 충돌한다.
     - stable/handoff direct fields와 runtime redesign operator-facing semantics가 다시 섞인다.
     - `전조형 고장`, `급격 종료`가 현재 상태처럼 읽힐 위험이 커진다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. runtime redesign의 operator-facing artifact에서 direct `event_type`, `terminal_pattern`, `사건유형`, `최종고장양상` 노출은 금지한다.
  2. `fault_panel_result_current_preview_v1.csv`와 그를 설명하는 `current_report`에서는 이미 닫힌 official current row에 한해 완곡화된 secondary summary(`사건 종결 요약`)를 제한적으로 허용한다.
  3. 이 summary는 headline이 아니라 보조 열이다.
  4. precursor report에서는 event summary도 기본 숨김으로 둔다.
  5. master report는 artifact guide 문서이므로, row-level event summary를 직접 전면 표로 다시 펼치지 않는다.
  6. analyst-facing artifact(`raw_only_fault_signal_report`, `detailed report`)에서는 direct event fields를 계속 허용한다.

### 이유
- current semantics 유지:
  - operator-facing headline은 `operational_state` 중심이어야 한다.
- 설명력 확보:
  - official current에 한해 `전조 후 급격 종료` 같은 요약은 보조 정보로 의미가 있다.
- artifact 분리 유지:
  - precursor report와 raw-only artifact는 다른 row universe와 역할을 가진다.
- stable/runtime 경계 보호:
  - stable direct fields와 runtime redesign operator-facing policy를 다시 섞지 않는다.

### 허용 패치
- current preview/current report에서 `사건 종결 요약` 같은 완곡한 secondary summary를 유지·정리하는 패치
- precursor report에서 direct/summary event semantics 노출을 더 줄이는 패치
- Gate 4A/5/6B 문서에 `direct field 금지 + softened summary 한정 허용`을 반영하는 패치

### 금지 패치
- current/precursor/master headline에 `사건유형`, `최종고장양상`, `event_type`, `terminal_pattern`을 직접 넣는 패치
- `사건 종결 요약`을 current headline이나 primary sorting field로 승격하는 패치
- precursor report에 `전조형 고장`, `급격 종료`, `진행성 악화`를 row 기본 열로 추가하는 패치
- master report 본문에 raw-only/current event tables를 operator 기본 읽기 흐름처럼 전개하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)

### 필요한 코드 업데이트
- 현재 runtime surface는 이미 대체로 본 결정을 따른다.
- 별도 즉시 코드 패치는 필수 아님.
- 다만 이후 `current_preview/current_report` 구조를 바꿀 때는 본 결정을 우선 기준으로 본다.

### 검증 계획
- 문서 검증:
  - Gate 4A/5/6B/2B가 본 결정과 모순 없이 갱신되었는지 확인
- artifact 검증:
  - `fault_panel_result_current_preview_v1.csv`에 direct event field가 없는지 확인
  - `fault_panel_result_precursor_report_v1.csv`에 direct/summary event semantics headline이 없는지 확인
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`와 detailed report에서는 direct event fields가 여전히 analyst-facing으로 남는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - conalog 1회 실행 후 current/precursor/raw-only artifact 확인

### 롤백 트리거
- current preview에서 softened event summary조차 운영자 혼동을 크게 유발한다고 확인되는 경우
- current report/current preview가 event summary 없이 설명력이 지나치게 떨어진다고 반복 보고되는 경우

### 남겨둔 보류 질문
- 본 보류 질문은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 에서 `확정/고장 row에만 채우는 조건부 secondary summary`로 후속 잠금됐다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)

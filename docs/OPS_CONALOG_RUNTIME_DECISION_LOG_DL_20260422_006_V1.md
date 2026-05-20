<!-- markdownlint-disable MD013 -->

# OPS Conalog Runtime Decision Log DL-20260422-006 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-006 | accepted | Gate 5 (+7) | raw-only direct exposure / master report link boundary | raw-only artifact는 master report에 남기되 operator 기본 읽기 흐름과 inline preview에서는 제외하고 analyst/support 섹션으로 내린다 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-006] raw-only direct exposure / master report link boundary
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 (primary), Gate 7 (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `raw-only fault signal report`와 `raw-only current` 계열을 운영자에게 어디까지 직접 노출하고, master report에서 어느 수준까지 직접 링크/preview로 보여줄 것인가.

### 배경
- [DL-20260422-001](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)은 `raw-only`를 analyst/support artifact로 잠갔고, [DL-20260422-004](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)는 auto-open 기본 경로에서 raw-only를 뺐다.
- [DL-20260422-005](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md)는 current report와 master report 역할을 분리해, master report를 안내/fallback 문서로 고정했다.
- 그런데 master report 내부에는 여전히 `raw-only preview 표`, `raw-only 고장 신호 표`, raw-only artifact direct bullet이 operator 기본 읽기 순서와 같은 화면층에 남아 있었다.
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)의 `RAW-001 ~ RAW-006`은 raw-only artifact가 공식 current 대체물이나 operator headline artifact처럼 읽히면 안 되는 대표 반례다.

### 선택지
1. 선택지 A. 현재처럼 master report 본문에 raw-only preview/fault signal 표를 직접 유지한다
   - 장점:
     - master report 하나만 읽어도 raw-only 근거를 바로 본다.
   - 단점:
     - operator 기본 동선에서 raw-only가 너무 앞단에 노출된다.
     - analyst/support artifact라는 경계가 다시 흐려진다.
2. 선택지 B. raw-only artifact 링크는 유지하되, operator 기본 읽기 순서와 inline preview에서는 빼고 master report의 analyst/support 섹션으로 내린다
   - 장점:
     - raw-only artifact 접근 경로는 남기면서도 공식 current 흐름과 분리된다.
     - master report가 안내 문서라는 성격과 잘 맞는다.
     - counterexample set의 `raw_only_only` 사례를 operator headline 흐름에 섞지 않는다.
   - 단점:
     - analyst/support 사용자는 한 단계 더 내려가 읽어야 한다.
3. 선택지 C. raw-only artifact를 master report에서 아예 감춘다
   - 장점:
     - operator 혼동이 최소화된다.
   - 단점:
     - analyst/support 접근성이 과도하게 떨어진다.
     - master report의 cross-artifact 안내 역할이 약해진다.

### 최종 결정
- `선택지 B`를 채택한다.
- 규칙은 아래와 같다.
  1. raw-only artifact는 master report에 남길 수 있지만 `operator 기본 읽기 흐름`의 bullet과 inline preview/table에서는 제외한다.
  2. master report 안에서는 raw-only artifact를 `analyst/support 추가 자료` 섹션으로 분리한다.
  3. `fault_panel_result_raw_only_fault_signal_report_v1.csv`와 `fault_panel_result_raw_only_current_*`는 path/link는 유지할 수 있으나, operator가 current/precursor 다음으로 바로 읽어야 하는 표처럼 배치하지 않는다.
  4. master report 본문에 raw-only preview table이나 raw-only fault signal table을 직접 전개하지 않는다.
  5. operator 기본 흐름은 `current_* -> precursor_report -> (필요 시) master report analyst/support 섹션`으로 읽는다.

### 이유
- DL-001 정합성:
  - raw-only는 공식 current 대체물이 아니라 analyst/support artifact다.
- DL-005 정합성:
  - master report는 공식 current 설명 문서가 아니라 안내/fallback 문서다.
- 반례 세트 정합성:
  - `RAW-001 ~ RAW-006`은 raw-only를 전면 노출할수록 operator가 current semantics와 혼동할 위험이 크다.
- 접근성 균형:
  - raw-only artifact를 숨기지 않고도 operator 기본 동선에서는 내릴 수 있다.

### 허용 패치
- master report의 `먼저 보는 법`에서 raw-only bullet 제거
- master report에 `analyst/support 추가 자료` 섹션 신설
- raw-only artifact를 주요 산출물 top block에서 analyst/support block으로 이동
- Gate 5 / Gate 7 / 상위 로드맵의 보류 질문 정리

### 금지 패치
- raw-only artifact를 current preview/current report와 같은 수준의 operator 기본 문서처럼 배치하는 패치
- 별도 decision 없이 raw-only artifact를 auto-open fallback에 다시 넣는 패치
- raw-only artifact를 master report에서 완전히 숨겨 analyst/support 접근까지 막는 패치
- raw-only artifact row universe나 알고리즘 규칙을 함께 바꾸는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

### 검증 계획
- 문서 검증:
  - Gate 5 / Gate 7 / 상위 로드맵이 raw-only direct exposure 질문을 닫았는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py`
  - conalog 1회 실행 후 master report에서 raw-only table inline preview가 제거됐는지 확인
- 반례 검증:
  - `RAW-001 ~ RAW-006`을 기준으로 master report가 raw-only를 operator default lane으로 밀어 올리지 않는지 확인

### 롤백 트리거
- analyst/support 사용자가 master report만으로 raw-only 핵심 row를 전혀 찾지 못한다는 반복 피드백이 쌓이는 경우
- operator current report가 자주 비어 master report analyst/support 섹션이 사실상 주 current 흐름처럼 쓰이는 경우

### 후속 결정
- auto-open fallback 정책은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)를 따른다.
- current report와 master report 역할 분리는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md)를 따른다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

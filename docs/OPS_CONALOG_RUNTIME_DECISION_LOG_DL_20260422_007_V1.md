<!-- markdownlint-disable MD013 -->

# OPS Conalog Runtime Decision Log DL-20260422-007 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-007 | accepted | Gate 5 (+7) | detailed definitions operator guidance boundary | detailed definitions 시트는 artifact 역할/컬럼 의미/공식성 차이까지만 설명하는 analyst/support glossary로 유지하고, operator 읽기 순서와 auto-open 정책은 current/master report에만 둔다 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-007] detailed definitions operator guidance boundary
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 (primary), Gate 7 (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- detailed report의 `definitions` 시트에 operator-facing guidance를 어디까지 넣고, 어디부터는 current/master report와 decision 문서에 남겨둘 것인가.

### 배경
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)는 detailed report를 lineage 문서로 정의하고 있다.
- 실제 `definitions` 시트는 artifact 역할과 컬럼 뜻을 짧게 설명하는 데 유용하지만, operator가 무엇을 먼저 열어야 하는지까지 담기 시작하면 current/master report와 정책 문서가 중복된다.
- [DL-20260422-004](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md), [DL-20260422-005](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md), [DL-20260422-006](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md)가 이미 auto-open, current/master 역할, raw-only direct exposure를 따로 잠갔다.

### 선택지
1. 선택지 A. definitions 시트에 operator 읽기 순서와 fallback 정책까지 적극적으로 넣는다
   - 장점:
     - xlsx 하나만 열어도 운영 가이드를 어느 정도 본다.
   - 단점:
     - current/master report와 결정 문서의 역할이 다시 겹친다.
     - stale wording이 생기면 정합성 관리가 어려워진다.
2. 선택지 B. definitions 시트는 artifact 역할, 공식성 차이, 주요 컬럼 뜻까지만 설명하는 glossary로 유지한다
   - 장점:
     - detailed report 성격과 잘 맞는다.
     - operator 정책은 current/master report에 남겨 일관성 있게 관리할 수 있다.
     - build/release 동기화가 단순해진다.
   - 단점:
     - definitions 시트만 열면 운영 읽기 순서는 충분히 알기 어렵다.
3. 선택지 C. definitions 시트를 순수 컬럼 사전으로 축소하고 artifact 역할 설명도 뺀다
   - 장점:
     - scope가 가장 작다.
   - 단점:
     - official/raw-only/precursor artifact 차이를 xlsx 안에서 전혀 설명하지 못한다.

### 최종 결정
- `선택지 B`를 채택한다.
- 규칙은 아래와 같다.
  1. definitions 시트는 `artifact 역할`, `공식성 차이`, `주요 컬럼 의미`, `짧은 caution`까지만 설명한다.
  2. definitions 시트는 analyst/support glossary로 유지한다.
  3. definitions 시트에 `무엇을 먼저 열지`, `auto-open fallback`, `operator 기본 읽기 순서`는 넣지 않는다.
  4. current/master report를 대체하지 않는다는 짧은 경계 문구는 허용한다.
  5. event semantics/operator headline 정책의 상세 설명은 definitions 시트가 아니라 Gate/decision 문서에 남긴다.

### 이유
- 역할 일관성:
  - detailed report는 lineage 문서고, current/master report는 operator 읽기 흐름을 담당한다.
- 정합성 비용:
  - 읽기 순서나 fallback 정책까지 xlsx에 넣으면 stale wording이 쌓이기 쉽다.
- 접근성 균형:
  - artifact 차이와 컬럼 의미는 xlsx 안에서 볼 수 있어야 하지만, 정책 레벨 가이드는 별도 문서가 더 적합하다.

### 허용 패치
- definitions 시트에 `definitions 시트 역할`, `detailed report 역할`, `official current vs raw_only`, `precursor vs fault_signal` 같은 짧은 glossary 행 추가
- raw-only/current/precursor 정의 문구를 `analyst/support glossary` 기준으로 정리
- Gate 5 / Gate 7 / 상위 로드맵의 open question 정리

### 금지 패치
- definitions 시트에 auto-open 순서, current -> precursor 기본 동선, master fallback 규칙을 직접 넣는 패치
- definitions 시트만 보고 operator가 공식 읽기 흐름을 다 따라가야 한다고 가정하는 패치
- event semantics headline 금지 규칙을 definitions 시트에서 장황한 정책 문단으로 다시 설명하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

### 검증 계획
- 문서 검증:
  - Gate 5 open question에서 definitions operator guidance 질문이 제거됐는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py`
  - conalog 1회 실행 후 detailed report `definitions` 시트에 glossary 행이 반영됐는지 확인
- 정합성 검증:
  - definitions 시트에 읽기 순서/auto-open 문구가 직접 들어가지 않았는지 확인

### 롤백 트리거
- 현장 사용자가 xlsx만 보고도 기본 읽기 순서를 알아야 한다는 강한 요구가 반복될 경우
- current/master report 접근성이 낮아 definitions 시트가 사실상 운영 메인 가이드로만 쓰이는 경우

### 관련 근거
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

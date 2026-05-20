# OPS Conalog Runtime Decision Log DL-20260422-005 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-005 | accepted | Gate 5 (+7) | current_report vs master_report role split | `current_report`는 official current 설명/요약 문서로, `master_report`는 artifact 안내/비교/fallback 문서로 분리한다 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-005] current_report vs master_report role split
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 (primary), Gate 7 (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `fault_panel_result_current_report_v1.md`와 `fault_panel_result_master_report_v1.md`의 역할 겹침을 어디까지 줄이고, 각 문서를 무엇으로 읽게 할 것인가.

### 배경
- DL-001은 `official current`와 `raw-only`를 분리했고, DL-004는 operator auto-open 순서를 `current_preview -> current_report -> master_report -> result`로 잠갔다.
- 그런데 current report와 master report가 둘 다 설명 문서를 맡고 있어서, operator가 “둘 중 무엇이 공식 current 설명 문서인가”를 헷갈릴 여지가 남아 있었다.
- 실제 runtime output에서는 site/chain 조합에 따라 current preview/current report가 비거나 생략될 수 있고, 이때 master report가 fallback처럼 열리더라도 공식 current 설명 문서와 동일한 의미를 가져서는 안 된다.

### 선택지
1. 선택지 A. current_report와 master_report의 역할 겹침을 유지한다
   - 장점:
     - 별도 문구 조정이 적다.
     - master report 하나만 읽어도 어느 정도 이해가 된다.
   - 단점:
     - current_report를 왜 여는지 약해진다.
     - master report가 안내 문서인지 공식 current 설명 문서인지 흐려진다.
2. 선택지 B. current_report는 official current 설명/요약 문서로, master_report는 artifact 안내/비교/fallback 문서로 분리한다
   - 장점:
     - DL-004 auto-open 순서와 잘 맞는다.
     - operator가 `공식 current 의미`와 `artifact 내비게이션`을 분리해 읽을 수 있다.
     - master report를 fallback으로 써도 공식 current semantics를 덮어쓰지 않는다.
   - 단점:
     - master report의 wording을 더 조심해서 써야 한다.
     - current_report가 없는 slice에서는 master report가 fallback 안내 문서라는 점을 더 명시해야 한다.
3. 선택지 C. current_report를 없애고 master_report 하나로 통합한다
   - 장점:
     - 문서 수가 줄어든다.
   - 단점:
     - current 설명과 cross-artifact 안내가 다시 섞인다.
     - Gate 5 projection policy와 DL-004 auto-open 정책을 다시 열어야 한다.

### 최종 결정
- `선택지 B`를 채택한다.
- 규칙은 아래와 같다.
  1. `fault_panel_result_current_report_v1.md`는 `official current`의 설명/요약 문서다.
  2. `fault_panel_result_master_report_v1.md`는 artifact 안내, cross-artifact 비교, fallback orientation 문서다.
  3. master report는 current/precursor/raw-only/detailed 차이를 설명할 수 있지만, 공식 current semantics의 주 설명 문서를 대체하지 않는다.
  4. current report가 존재하면 operator는 current preview와 current report를 먼저 읽는다.
  5. current report가 비어 있거나 없을 때 master report가 자동 오픈 fallback이 될 수는 있지만, 그 경우에도 master report는 `안내/fallback 문서`로 읽고 공식 current report로 승격하지 않는다.

### 이유
- 정의 일관성:
  - Gate 5는 이미 current artifact와 master artifact를 다른 projection으로 정의했다.
- operator 해석 가능성:
  - 공식 current 설명과 artifact 안내를 나눠야 operator가 무엇을 먼저 봐야 할지 분명해진다.
- fallback 안전성:
  - current report가 비어 있는 slice에서도 master report가 “공식 current semantics”를 대신한다고 오해되지 않아야 한다.
- downstream 영향:
  - `run_full_algorithm_pack.py` wording, Gate 5 output policy, DL-001/DL-004 parked questions, Gate 7 구현 순서를 같은 기준으로 맞출 수 있다.

### 허용 패치
- `build_live_report_markdown(...)`의 목적/읽는 법 wording 정리
- `build_master_report_markdown(...)`의 목적/먼저 보는 법/해석 가이드 wording 정리
- Gate 5 output policy와 Gate 7 implementation order 문서에 역할 분리 반영
- DL-001, DL-004의 parked question 정리

### 금지 패치
- current report를 삭제하거나 master report에 흡수하는 패치
- master report를 `공식 current 설명 문서`로 승격하는 패치
- 별도 decision 없이 current/master row universe를 바꾸는 패치
- current report 부재만을 이유로 raw-only current report를 operator-facing 공식 설명 문서처럼 승격하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

### 필요한 코드 업데이트
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

### 검증 계획
- 문서 검증:
  - Gate 5/7, DL-001, DL-004가 current/master 역할 분리를 같은 기준으로 참조하는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py`
  - conalog 1회 실행 후 master/current report wording 확인
- slice 검증:
  - current report 존재 slice
  - current report 미존재 slice에서 master fallback wording 확인

### 롤백 트리거
- current report가 실제 운영에서 거의 생성되지 않아 master report가 사실상 주 current 설명 문서로만 쓰인다는 근거가 쌓이는 경우
- master report를 더 얇게 유지할 수 없어 artifact 안내와 current 설명을 분리하는 비용이 과도하다고 판단되는 경우

### 후속 결정
- auto-open 순서는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)를 따른다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

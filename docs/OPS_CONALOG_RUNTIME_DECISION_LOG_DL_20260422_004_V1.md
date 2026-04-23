# OPS Conalog Runtime Decision Log DL-20260422-004 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-004 | accepted | Gate 5 (+7) | operator auto-open fallback policy | operator-oriented wrapper의 기본 자동 오픈은 official current/current guide 레인 안에서만 순환하고 raw-only preview는 자동 오픈 fallback에서 제외 | Codex + 사용자 | 2026-04-22 |

## [DL-20260422-004] operator auto-open fallback policy lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 (primary), Gate 7 (dependent)
- `owner`: Codex + 사용자
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- operator-oriented runtime wrapper가 실행 완료 후 어떤 artifact를 어떤 순서로 자동 오픈해야 하는가.

### 배경
- DL-001은 `official current`와 `raw-only`의 공식성을 분리했고, `raw-only`를 operator-facing 공식 current 대체물로 쓰지 않도록 잠갔다.
- 하지만 현재 runtime package wrapper는 대체로 아래 순서를 사용해 왔다.
  1. `fault_panel_result_current_preview_v1.csv`
  2. `fault_panel_result_raw_only_current_preview_v1.csv`
  3. `fault_panel_result_current_report_v1.md`
  4. `fault_panel_result_master_report_v1.md`
- 이 순서는 official current preview가 비었을 때 operator가 raw-only preview를 먼저 보게 만들 수 있다.
- Gate 5 output policy와 DL-001 기준으로 보면, 이는 `공식 current 부재`와 `raw-only 보조표 직접 전면 배치`를 혼동하게 만들 위험이 있다.

### 선택지
1. 선택지 A. 현 baseline 유지
   - 순서:
     - `current_preview -> raw_only_current_preview -> current_report -> master_report -> result`
   - 장점:
     - current preview가 비었을 때도 바로 표 하나를 열어준다.
     - 현재 package batch 동작을 거의 안 건드려도 된다.
   - 단점:
     - raw-only preview가 operator-facing 공식 fallback처럼 읽힌다.
     - DL-001의 official/raw-only 경계를 다시 흐린다.
2. 선택지 B. operator 기본 자동 오픈은 official/current-guide 레인 안에서만 순환
   - 순서:
     - `current_preview -> current_report -> master_report -> result`
   - 장점:
     - operator 기본 진입점이 끝까지 official/guide artifact 안에 머문다.
     - raw-only preview는 결과 폴더나 master report 안내를 통해 analyst/support가 선택적으로 본다.
     - DL-001과 Gate 5 정책에 가장 잘 맞는다.
   - 단점:
     - official current preview가 없을 때 raw-only preview를 자동으로 보지 못한다.
     - 일부 support 사용자는 한 번 더 result/master를 거쳐야 한다.
3. 선택지 C. 무조건 master report만 자동 오픈
   - 장점:
     - 안내 문서 하나만 보면 된다.
     - official/raw-only 공식성 혼동이 더 줄어든다.
   - 단점:
     - operator가 바로 current preview를 보는 빠른 흐름이 사라진다.
     - existing runtime wrapper UX와 너무 멀어진다.

### 최종 결정
- `선택지 B`를 채택한다.
- 규칙은 아래와 같다.
  1. operator-oriented runtime wrapper의 기본 자동 오픈 순서는 `fault_panel_result_current_preview_v1.csv -> fault_panel_result_current_report_v1.md -> fault_panel_result_master_report_v1.md -> result 폴더`다.
  2. `fault_panel_result_raw_only_current_preview_v1.csv`는 operator 기본 자동 오픈 fallback에서 제외한다.
  3. raw-only preview/current report는 analyst/support artifact로서 result 폴더 또는 master report 안내를 통해 수동 접근한다.
  4. 이 결정은 runtime redesign / hybrid artifact 레인에만 적용하며, stable/handoff contract 자체를 재정의하지 않는다.

### 이유
- 정의 일관성:
  - DL-001은 `official current != raw-only`를 이미 잠갔다.
- operator 해석 가능성:
  - current preview가 없다고 해서 raw-only preview를 공식 fallback처럼 띄우면 혼동이 커진다.
- analyst/support 접근성:
  - raw-only artifact는 숨기지 않되, operator 기본 진입점에서만 뺀다.
- downstream 영향:
  - batch wrapper, README, Gate 5 output policy, smoke test가 한 기준으로 맞춰질 수 있다.

### 허용 패치
- runtime package operator-oriented wrapper의 자동 오픈 순서 수정
- release runtime README의 실행 후 자동 오픈 설명 수정
- Gate 5 output policy / Gate 7 implementation order / 상위 로드맵의 parked question 정리
- smoke test에서 operator wrapper의 auto-open order를 검증하는 패치

### 금지 패치
- 별도 decision 없이 raw-only preview를 operator 기본 auto-open fallback으로 유지하거나 승격하는 패치
- raw-only preview/current report를 삭제하거나 비공개로 만드는 패치
- stable/handoff wrapper까지 같은 기준으로 자동 확장하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [release/conalog_full_runtime_v1/README.md](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/README.md)

### 필요한 코드 업데이트
- [release/conalog_full_runtime_v1/package/bin/daily_run.bat](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/bin/daily_run.bat)
- [release/conalog_full_runtime_v1/package/bin/incremental_run.bat](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/bin/incremental_run.bat)
- [release/conalog_full_runtime_v1/package/bin/run_real.bat](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/bin/run_real.bat)
- [release/conalog_full_runtime_v1/package/bin/run_imported_real.bat](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/bin/run_imported_real.bat)
- [research/prognostics/build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)
- [research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)

### 검증 계획
- 문서 검증:
  - Gate 5, Gate 7, 상위 로드맵의 parked question과 open policy가 본 결정을 따르는지 확인
- script/smoke 검증:
  - operator-oriented wrapper에서 `raw_only_current_preview`가 auto-open fallback으로 남아 있지 않은지 확인
- 최소 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `python research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
  - conalog 1회 실행 후 result artifact 생성 확인

### 롤백 트리거
- official current preview가 비는 실제 운영 slice에서 operator workflow가 과도하게 막힌다는 근거가 반복적으로 나오는 경우
- result/master를 거쳐 raw-only preview를 여는 흐름이 현장 운영에 명백한 병목이 된다는 근거가 쌓이는 경우
- 별도 analyst/support wrapper를 만드는 편이 더 낫다는 합의가 생기는 경우

### 남겨둔 보류 질문
- operator-oriented wrapper가 아닌 analyst/support 전용 wrapper를 별도로 둘 것인가
- raw-only artifact를 result 폴더 대신 master report에서 더 직접 링크/안내할 것인가

### 후속 결정
- current report와 master report의 역할 분리는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md) 에서 별도로 잠근다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [release/conalog_full_runtime_v1/README.md](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/README.md)
- [research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)

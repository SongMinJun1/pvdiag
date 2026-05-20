<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_010_V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-010 | accepted | Gate 5 / Gate 7 | release/final_delivery runtime explanation sync scope | final_delivery 문서군에는 stable 우선 + runtime redesign 별도 계약이라는 boundary note만 최소 반영하고, runtime artifact semantics 상세는 runtime pack README/decision set에 남긴다 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-010] release/final_delivery runtime explanation sync scope lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 / Gate 7
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `release/final_delivery_v1/*` 문서군에 runtime redesign 설명을 어디까지 동기화할 것인가.

### 배경
- [DL-20260422-002](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md) 로 stable/handoff contract와 runtime redesign contract는 별도 계약으로 잠겼다.
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)는 두 문서군을 같은 층으로 덮어쓰지 말고 boundary/mapping note로 읽어야 한다고 정리한다.
- final delivery pack은 stable direct CLI / stable integrated schema 중심이고, runtime redesign pack은 `official current / precursor / raw-only / master / detailed` artifact를 나눠서 다룬다.

### 선택지
1. 선택지 A. final_delivery 문서군을 runtime redesign README 수준으로 상세 동기화한다
   - 장점:
     - runtime pack만 읽은 사람에게는 친숙하다.
   - 단점:
     - stable pack 문서가 runtime artifact semantics를 과도하게 끌어오게 된다.
     - stable/handoff direct fields와 runtime redesign operator semantics가 다시 섞일 위험이 크다.
2. 선택지 B. final_delivery 문서군에는 boundary note만 최소 반영하고, runtime artifact semantics 상세는 runtime pack README/decision set에 남긴다
   - 장점:
     - stable 문서의 역할을 유지한다.
     - stable/runtime 경계가 분명해진다.
     - 중복 설명을 줄이고 drift 위험을 낮춘다.
   - 단점:
     - runtime 상세를 보려면 별도 문서를 따라가야 한다.
3. 선택지 C. final_delivery 문서군에는 runtime redesign을 전혀 언급하지 않는다
   - 장점:
     - 가장 간단하다.
   - 단점:
     - 사용자가 sibling runtime pack과 final_delivery pack을 같은 층으로 오해할 여지가 남는다.

### 최종 결정
- 선택지 B를 채택한다.
- 규칙은 아래와 같다.
  1. `release/final_delivery_v1/README.md`, `QUICKSTART.md`, `KNOWN_LIMITS.md`에는 stable pack이 우선이라는 점과 runtime redesign artifact는 별도 계약/별도 pack이라는 boundary note만 최소 반영한다.
  2. `fault_panel_result_current_*`, `precursor_report`, `raw_only_fault_signal_report`, `master_report`, `detailed_report`의 세부 semantics, current/master/read-order, direct event field 금지 규칙은 final_delivery 문서에 재기술하지 않는다.
  3. 그 상세는 [release/conalog_full_runtime_v1/README.md](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/README.md) 와 runtime decision/gate 문서군을 canonical source로 둔다.
  4. final_delivery 문서군은 stable direct CLI와 stable integrated schema 설명을 우선 유지한다.

### 이유
- contract separation 유지:
  - stable/handoff contract와 runtime redesign contract는 이미 별도 계약으로 잠겨 있다.
- drift 감소:
  - runtime artifact semantics를 final_delivery에도 복제하면 중복 설명이 빠르게 어긋난다.
- operator confusion 완화:
  - final_delivery 사용자는 stable pack을 먼저 읽고, runtime redesign은 별도 참고 pack으로 인지하면 된다.

### 허용 패치
- final_delivery 문서군에 stable/runtime 경계 문구를 짧게 추가하는 패치
- runtime pack README 또는 mapping note를 참조하도록 안내 문구를 넣는 패치
- Gate 7 / 상위 로드맵 / cross-gate audit에 본 결정 반영

### 금지 패치
- final_delivery 문서군에 runtime redesign artifact 세부 semantics를 대량 복제하는 패치
- final_delivery 문서군에서 `fault_panel_result_current_*`, `precursor_report`, `raw_only_fault_signal_report`를 primary reading flow처럼 설명하는 패치
- stable integrated schema 설명을 runtime redesign operator semantics로 덮어쓰는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [release/final_delivery_v1/README.md](/Users/b9gc/pvdiag/release/final_delivery_v1/README.md)
- [release/final_delivery_v1/QUICKSTART.md](/Users/b9gc/pvdiag/release/final_delivery_v1/QUICKSTART.md)
- [release/final_delivery_v1/KNOWN_LIMITS.md](/Users/b9gc/pvdiag/release/final_delivery_v1/KNOWN_LIMITS.md)

### 필요한 코드 업데이트
- 없음
- 본 결정은 문서 boundary/sync scope에 관한 것이며 알고리즘/entrypoint 코드를 바꾸지 않는다.

### 검증 계획
- 문서 검증:
  - final_delivery 문서군에 boundary note가 들어가되 runtime semantics 상세가 과복제되지 않았는지 확인
- 경계 검증:
  - final_delivery 문서군이 stable CLI / schema 우선 설명을 유지하는지 확인
  - runtime pack README가 runtime artifact semantics의 canonical source로 남는지 확인
- 실행 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - conalog 1회 실행 후 runtime artifact 경로가 계속 정상인지 확인

### 롤백 트리거
- final_delivery 문서 사용자가 boundary note만으로 sibling runtime pack과의 관계를 이해하기 어렵다고 반복 보고되는 경우
- runtime 설명을 최소만 넣었더니 stable pack 사용 흐름이 오히려 더 혼란스러워지는 경우

### 남겨둔 보류 질문
- 없음
- 본 후속 질문은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_011_V1.md) 에서 후속 잠금됐다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- [release/conalog_full_runtime_v1/README.md](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/README.md)

# OPS Conalog Runtime Decision Log DL-20260422-001 V1

## 빠른 요약
| decision_id | status | related_gate | topic | decision | owner | date_decided |
| --- | --- | --- | --- | --- | --- | --- |
| DL-20260422-001 | accepted | Gate 5 (+4A/6B) | official/raw-only/operator semantics | official current와 raw-only의 공식성 분리, operator headline 축 제한, event semantics headline 금지 | Codex + 사용자 합의 | 2026-04-22 |

## [DL-20260422-001] official current / raw-only / operator headline semantics lock
- `status`: accepted
- `date_first_raised`: 2026-04-22
- `date_decided`: 2026-04-22
- `related_gate`: Gate 5 (primary), Gate 4A / Gate 6B (dependent)
- `owner`: Codex + 사용자 합의
- `related_branch_ids`: []
- `related_parking_ids`: []

### 질문
- `official current`, `raw-only`, `operator-facing headline`, `event semantics`의 경계를 지금 시점에 어디까지 고정할 것인가.

### 배경
- 기존 논의에서 `raw-only` 보조표가 공식 current처럼 읽히거나, `event_type`/`terminal_pattern` 같은 사건 해석 축이 현재 상태 headline처럼 읽히는 흔들림이 반복됐다.
- Gate 2B는 canonical result object를 정의했고, Gate 4A는 event semantics와 operator semantics를 분리했으며, Gate 6B는 operator-facing 노출 축을 줄였다.
- 하지만 이 세 문서만으로는 실제 코드 패치 전에 “무엇을 해도 되는가/안 되는가”가 충분히 잠기지 않았다.
- 특히 아래 artifact에 직접 영향이 있다.
  - `fault_panel_result_current_*`
  - `fault_panel_result_precursor_report_v1.csv`
  - `fault_panel_result_raw_only_fault_signal_report_v1.csv`
  - `fault_panel_result_master_report_v1.md`
  - `fault_panel_result_detailed_report_v1.xlsx`

### 선택지
1. 선택지 A. official current와 raw-only를 상황에 따라 유동적으로 해석한다
   - 장점:
     - 구현 자유도가 높다.
     - official current가 비는 경우 raw-only를 쉽게 전면 배치할 수 있다.
   - 단점:
     - 운영자 혼동이 반복된다.
     - release/논문/발표 방어가 어려워진다.
     - 같은 row가 artifact마다 다른 공식성으로 읽힐 수 있다.
2. 선택지 B. official current와 raw-only를 분리하되, operator headline에는 사건 해석 축을 일부 허용한다
   - 장점:
     - 설명력이 조금 늘 수 있다.
     - 현재 이벤트의 “끝 모양”을 더 풍부하게 전달할 수 있다.
   - 단점:
     - `operational_state`와 `event_type/terminal_pattern`이 다시 섞인다.
     - precursor/current 표에서 미래 예언처럼 읽힐 위험이 남는다.
3. 선택지 C. official current와 raw-only의 공식성을 고정하고, operator headline은 current semantics만 허용하며, event semantics는 analyst/event layer에 한정한다
   - 장점:
     - 정의 일관성이 가장 좋다.
     - MLPE 환경에서 사건 해석과 현재 상태를 구분하기 쉽다.
     - downstream artifact/schema 패치 기준이 명확해진다.
   - 단점:
     - operator-facing 표면 설명은 더 단순해진다.
     - raw-only를 운영 fallback으로 쓰고 싶은 유혹을 제어해야 한다.

### 최종 결정
- 선택지 C를 채택한다.
- 규칙은 아래와 같다.
  1. `official current`는 live chain이 만든 공식 운영 결과만 뜻한다.
  2. `raw-only` artifact는 analyst-facing 또는 운영 보조표일 뿐, 공식 current를 대체하지 않는다.
  3. operator-facing headline은 `operational_state` 중심 current semantics만 허용한다.
  4. `event_type`, `terminal_pattern`, `fault_like_day`, raw `critical/final` naming은 current/precursor headline에서 금지한다.
  5. `raw-only fault signal report`는 `공식 hard-fault ledger`가 아니라 `raw-only 후보 우주에서 고장 신호가 관측된 analyst/support artifact`로 유지한다.

### 이유
- 정의 일관성:
  - Gate 4A 계약상 `operational_state`와 `event semantics`는 같은 층이 아니다.
- MLPE 해석 적합성:
  - MLPE 환경에서는 current pattern과 retrospective event interpretation이 쉽게 섞여 오해를 만든다.
- 운영자 해석 가능성:
  - operator-facing headline은 현재 무엇을 해야 하는지를 알려야지, 사건 종결 해석을 전면에 두면 안 된다.
- false positive / false negative 비용:
  - raw-only를 공식 결과처럼 올리면 false positive 비용이 불필요하게 커진다.
  - 반대로 official current를 유지하면 운영 경보의 비용 통제가 쉬워진다.
- downstream artifact 영향:
  - Gate 5 projection policy, Gate 6B policy lock, 실제 CSV/XLSX schema 패치가 같은 기준을 보게 된다.

### 허용 패치
- Gate 5 projection policy를 artifact/schema patch checklist로 변환하는 패치
- current/precursor/master/detailed의 wording을 본 결정에 맞게 정리하는 패치
- `raw_only`와 `official current`를 이름/가이드/오픈 정책에서 더 명확히 드러내는 패치
- operator-facing에서 `event semantics headline 금지`를 enforcement하는 패치
- smoke/build/release 문서에 official/raw-only 구분을 추가하는 패치

### 금지 패치
- 별도 decision 없이 `raw-only current`나 `raw-only fault signal report`를 공식 current처럼 승격하는 패치
- current preview/current report/precursor report headline에 `event_type`/`terminal_pattern`을 넣는 패치
- `fault_like_day`를 operator-facing direct state label로 번역하는 패치
- maintenance lane과 safety/control lane을 같은 단일 top1 action label로 접는 패치
- official current가 비었다는 이유만으로 raw-only preview를 같은 공식성으로 노출하는 패치

### 필요한 문서 업데이트
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- release README/QUICKSTART/KNOWN_LIMITS 계열 문서

### 필요한 코드 업데이트
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
- [build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)
- [smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)
- 필요 시 current/master auto-open policy를 다루는 batch/release 문서

### 검증 계획
- 문서 검증:
  - Gate 5/4A/메인 로드맵이 본 결정을 모순 없이 참조하는지 확인
- artifact 검증:
  - `official current`와 `raw-only` 파일명이 공식성/출처를 숨기지 않는지 확인
  - current/precursor headline에 `event_type/terminal_pattern`이 없는지 확인
- smoke 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `python research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
- 실행 검증:
  - conalog 1회 실행 후 current/master/raw-only artifact read order와 wording 확인
- slice 검증:
  - official current empty / raw-only populated 사례
  - precursor vs hard-evidence 경계 사례

### 롤백 트리거
- official current가 비는 상황에서 raw-only fallback 정책 때문에 운영 workflow가 지속적으로 막히는 경우
- current/precursor headline에서 event semantics를 완전히 감출 수 없어 operational confusion이 커지는 경우
- Gate 7 구현 순서 잠금 이후, artifact projection이 본 결정을 유지할 수 없다고 드러나는 경우

### 남겨둔 보류 질문
- 본 결정의 기본 경계는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md) 에서 후속 잠금됐다.
- official current의 `softened event summary` 조건부 노출 규칙은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 에서 후속 잠금됐다.
- 현재 본 결정에 남아 있는 별도 보류 질문은 없다.

### 후속 결정
- auto-open fallback 정책은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md) 에서 별도로 잠근다.
- current report와 master report의 역할 분리는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_005_V1.md) 에서 별도로 잠근다.
- raw-only direct exposure / master report link boundary는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md) 에서 별도로 잠근다.

### 관련 근거
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

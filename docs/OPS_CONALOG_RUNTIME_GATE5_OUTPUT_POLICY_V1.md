# OPS Conalog Runtime Gate 5 Output Policy V1

## 1. 목적
- 본 문서는 `OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md`의 Gate 5 산출물인 `출력 정책` 초안이다.
- 목적은 아래 일곱 가지다.
  - 각 artifact가 `누구를 위한 표인지` 잠근다.
  - 각 artifact가 `어떤 row universe`를 담는지 잠근다.
  - `official current`와 `raw-only 보조표`의 공식성 수준을 분명히 한다.
  - operator-facing wording과 analyst-facing wording의 경계를 문서로 남긴다.
  - 각 artifact가 canonical result object의 어떤 축을 투영하는지 잠근다.
  - master report가 어떤 순서로 artifact를 안내해야 하는지 고정한다.
  - 이후 schema/파일명/가이드 패치가 생겨도, 무엇이 정책 위반인지 바로 판별할 수 있게 만든다.

## 2. 사용 규칙
- 이 문서는 `artifact 정책`을 잠그는 문서다.
- 동시에 `projection 정책` 문서다.
- 즉 artifact는 canonical result object와 semantics contract를 각기 다른 방식으로 투영한 결과여야 한다.
- 이 문서가 잠기기 전에는 아래 패치를 금지한다.
  - official artifact와 raw-only artifact의 이름/역할을 뒤섞는 patch
  - operator-facing 표에 analyst-only artifact를 같은 수준으로 배치하는 patch
  - artifact별 audience, 공식성, row universe를 바꾸는 patch
  - canonical result object에 없는 새 상태/축을 artifact에서 먼저 발명하는 patch
- 이 문서가 잠기기 전에도 허용되는 작업은 아래다.
  - wording patch
  - 가이드 문구 보강
  - read order 정리
  - decision log 등록

## 3. 상태
- 현재 상태:
  - `working draft`
- 의미:
  - 현재 코드와 문서 흐름을 기준으로 한 projection 정책 초안이다.
  - Gate 2B canonical result model, Gate 4A semantics contract, Gate 6B policy lock을 반영한 `동기화 대상 draft`다.
  - official/raw-only/operator headline 경계는 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)를 현재 우선 기준으로 따른다.
  - operator-oriented wrapper의 auto-open fallback은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_004_V1.md)를 따른다.
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md) 에 구현 순서가 잠겨 있으나, 실제 artifact/schema patch 전이라 일부 노출 범위와 오픈 정책은 조정될 수 있다.

## 4. 출력 정책 원칙
### 4.1 one artifact, one universe
- 한 artifact는 하나의 row universe만 대표해야 한다.
- precursor candidate, hard evidence, official current를 한 표에 섞지 않는다.

### 4.2 공식성과 분석용을 섞지 않는다
- `official current`는 운영 공식 기준이다.
- `raw-only`는 분석/보조 판단 우주다.
- raw-only artifact는 이름만 보고도 raw-only임을 알 수 있어야 한다.

### 4.3 operator-facing과 analyst-facing을 구분한다
- operator-facing:
  - 바로 행동할 수 있어야 한다.
  - internal shorthand가 없어야 한다.
- analyst-facing:
  - lineage와 internal field를 더 많이 허용한다.

### 4.4 master report는 안내 문서다
- master report는 새 판정을 만드는 문서가 아니다.
- 각 artifact를 어떤 순서로 읽어야 하는지 설명하는 문서다.

### 4.5 detailed report는 lineage 문서다
- detailed report는 단순 요약표가 아니다.
- 서로 다른 층의 신호와 lineage를 함께 보는 analyst-facing 문서다.

### 4.6 output policy는 projection policy다
- artifact는 `canonical result object`의 projection이다.
- 따라서 같은 row라도 artifact마다 보여주는 축이 달라질 수 있다.
- 하지만 어떤 artifact도 canonical object에 없는 의미를 먼저 만들면 안 된다.

### 4.7 semantics contract를 어기면 안 된다
- `event_type`, `terminal_pattern`은 사건 해석 축이다.
- `operational_state`는 현재 운영 상태 축이다.
- Gate 4A 계약상, current/precursor artifact는 `operational_state`를 우선하고 `event_type/terminal_pattern`은 보조로만 다룬다.

### 4.8 maintenance lane과 safety lane을 같은 projection으로 접지 않는다
- operator-facing에서 `무엇을 해야 하는가`는 maintenance action과 safety/control action으로 나뉜다.
- Gate 6B 기준으로, 같은 artifact에 있더라도 같은 칼럼/등급표로 접지 않는다.

## 5. Artifact Policy Matrix
| artifact | audience | source layer | row universe | 공식성 | operator-facing 허용 여부 | allowed wording | 금지 wording | 핵심 질문 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `fault_panel_result_current_v1.csv` | 운영자, 분석가 | live chain | 공식 current fault row | 공식 | 가능 | `운영 공식 결과`, `확정`, `상위 해석 후보` | `raw-only candidate`, `임시 후보` | 지금 운영 공식 결과에서 어떤 패널이 fault인가 |
| `fault_panel_result_current_preview_v1.csv` | 운영자 | live chain | 공식 current preview row | 공식 | 가능 | `운영 공식 preview`, `운영 판정` | `분석용 후보` | 지금 운영자가 먼저 훑어볼 공식 요약은 무엇인가 |
| `fault_panel_result_current_report_v1.md` | 운영자, 분석가 | live chain | 공식 current 요약 | 공식 | 가능 | `공식 current 설명` | `raw-only만 보면 된다` | 공식 current 결과를 어떻게 읽어야 하나 |
| `fault_panel_result_raw_only_current_v1.csv` | 분석가 | raw-only candidate layer | raw-only strict current subset | 보조 | 제한적 | `raw-only current`, `분석용 strict subset` | `운영 공식 current` | raw-only 우주에서 strict current subset은 무엇인가 |
| `fault_panel_result_raw_only_current_preview_v1.csv` | 분석가 | raw-only candidate layer | raw-only strict current preview | 보조 | 제한적 | `raw-only preview`, `분석용 preview` | `공식 preview` | raw-only current subset을 빠르게 훑을 수 있는가 |
| `fault_panel_result_raw_only_current_report_v1.md` | 분석가 | raw-only candidate layer | raw-only current 설명 | 보조 | 제한적 | `raw-only current 설명` | `운영 공식 설명` | raw-only current subset을 어떻게 읽어야 하나 |
| `fault_panel_result_precursor_report_v1.csv` | 운영자, 분석가 | precursor gate + report layer | hard evidence 없는 precursor candidate | 보조 | 가능 | `전조 후보`, `고위험 관찰`, `모니터링 권고` | `확정`, `critical/final`, `직접 고장 신호` | 아직 고장 신호는 없지만 추적할 가치가 있는 패널은 무엇인가 |
| `fault_panel_result_raw_only_fault_signal_report_v1.csv` | 분석가, 운영 보조 | raw-only candidate + hard evidence layer | raw-only 후보 우주에서 고장 신호가 관측된 row | 보조 | 제한적 | `raw-only 고장 신호`, `확정 경로`, `현장 점검 권고` | `공식 hard-fault ledger`, `운영 공식 결과` | raw-only 우주에서 이미 강한 고장 신호가 보이는 패널은 무엇인가 |
| `fault_panel_result_detailed_report_v1.xlsx` | 분석가 | combined lineage | 여러 층의 evidence와 lineage | 분석용 | 제한적 | `lineage`, `상세 근거`, `timeline`, `definitions` | `가장 먼저 보는 운영표` | 왜 그렇게 판정됐는가, 어떤 층의 신호가 있었는가 |
| `fault_panel_result_master_report_v1.md` | 운영자, 분석가 | combined navigation | artifact 안내와 요약 | 안내용 | 가능 | `읽는 순서`, `artifact 역할`, `의미 차이` | `새 판정`, `새 점수` | 어떤 표를 어떤 순서로 읽어야 하나 |

## 6. Projection Policy Matrix
| artifact | primary semantics | projection type | 직접 노출 가능한 canonical 축 | 기본 숨김 축 | 비고 |
| --- | --- | --- | --- | --- | --- |
| `fault_panel_result_current_*` | operator-facing current semantics | operator summary projection | `state_axis`, 축약된 `cause_axis.operational_category`, 축약된 `action_axis.maintenance_lane`, 축약된 `confidence_axis` | `candidate_ranked`, `event_type`, `terminal_pattern`, `blocked_by_missing_evidence` | official artifact |
| `fault_panel_result_precursor_report_v1.csv` | operator-facing current semantics | operator watchlist projection | `state_axis.operational_state`, 완곡한 `phenotype_axis`, 축약된 `maintenance_lane`, 완곡한 confidence | `hard evidence tier`, `event_type/terminal_pattern` headline, ranked causes | precursor candidate 전용 |
| `fault_panel_result_raw_only_fault_signal_report_v1.csv` | analyst-facing explanation semantics + 일부 operator summary | analyst diagnostic projection | `state_axis`, `evidence_axis`, `cause_axis.candidate_ranked`, `phenotype_axis`, `scope_axis`, `confidence_axis` | official current 의미 | raw-only임을 명시 |
| `fault_panel_result_raw_only_current_*` | analyst-facing explanation semantics | analyst strict-subset projection | `state_axis`, `cause_axis`, 일부 `temporal_axis`, 일부 `scope_axis` | officiality | raw-only current subset |
| `fault_panel_result_detailed_report_v1.xlsx` | analyst-facing explanation semantics + event semantics | lineage projection | canonical object 대부분 + lineage metadata | 없음 | analyst primary |
| `fault_panel_result_master_report_v1.md` | narrative/master semantics | navigation projection | artifact role, 읽는 순서, 축 설명 | 개별 row 판정 | 안내 문서 |

원칙:
- current 계열은 `operational_state`를 우선한다.
- detailed 계열만 `event_type/terminal_pattern`을 적극적으로 쓸 수 있다.
- master report는 canonical object의 축을 직접 row마다 다 보여주지 않는다.

## 7. 읽는 순서 정책
### 7.1 운영자 기본 순서
1. `fault_panel_result_current_preview_v1.csv`
2. `fault_panel_result_current_report_v1.md`
3. 필요 시 `fault_panel_result_precursor_report_v1.csv`
4. 필요 시 `fault_panel_result_master_report_v1.md`

원칙:
- 운영자는 raw-only artifact를 기본 진입점으로 보지 않는다.

### 7.2 분석가 기본 순서
1. `fault_panel_result_master_report_v1.md`
2. `fault_panel_result_current_v1.csv`
3. `fault_panel_result_precursor_report_v1.csv`
4. `fault_panel_result_raw_only_fault_signal_report_v1.csv`
5. `fault_panel_result_raw_only_current_v1.csv`
6. `fault_panel_result_detailed_report_v1.xlsx`

원칙:
- 분석가는 official과 raw-only를 비교하되, 둘을 같은 공식성으로 취급하지 않는다.

## 8. 기본 오픈 정책
### 8.1 현재 pack/build baseline
- operator-oriented runtime wrapper의 기본 자동 오픈 순서는 아래 preference를 따른다.
  - `fault_panel_result_current_preview_v1.csv`
  - 없으면 `fault_panel_result_current_report_v1.md`
  - 없으면 `fault_panel_result_master_report_v1.md`
  - 없으면 `result` 폴더

### 8.2 권장 정책
- 기본 자동 오픈은 공식 current preview를 우선한다.
- raw-only preview는 analyst/support artifact로서 result 폴더 또는 master report 안내를 통해 수동 접근한다.
- master report는 자동 오픈 fallback이 될 수 있지만, current preview를 대체하는 1순위 표는 아니다.

## 9. Row Universe 규칙
### 9.1 official current
- live chain이 만든 공식 current row만 포함한다.
- raw-only candidate 전용 row를 혼입하지 않는다.

### 9.2 precursor report
- hard evidence가 없는 precursor candidate만 포함한다.
- `final_fault`, `critical_fault`, `critical_confirmed` 동반 row는 제외한다.

### 9.3 raw-only fault signal report
- raw-only 후보 우주에서 hard evidence 또는 그에 준하는 강신호가 관측된 row를 포함한다.
- official current와 일부 row가 겹칠 수 있지만, 공식 current와 동일한 의미로 읽지 않는다.

### 9.4 detailed report
- 서로 다른 row universe를 한 파일 안에 담을 수 있다.
- 대신 시트/섹션마다 source layer와 역할이 드러나야 한다.

## 10. Semantics Priority by Artifact
### 10.1 current 계열
- `operational_state` 우선
- `primary_evidence_path`는 축약 보조
- `event_type/terminal_pattern`은 headline 금지

### 10.2 precursor report
- current semantics 우선
- `전조 후보`, `고위험 관찰`, `추가 확인 필요` 같은 현재 상태 표현 사용
- `진행성 악화`, `급격 종료` 같은 사건 종결 해석은 headline 금지

### 10.3 raw-only fault signal report
- analyst explanation semantics 우선
- `확정 경로`, `고장 신호 요약`, `상세 후보`, `공통원인 여부`, `범위` 같은 설명 허용
- official current와 같은 강도의 공식 wording 금지

### 10.4 detailed report
- explanation semantics + event semantics 적극 허용
- 단, operator current summary를 대신하지 않는다
- definitions 시트는 artifact 역할/주요 컬럼 뜻을 짧게 설명하는 glossary로 유지하고, 읽기 순서/auto-open 정책은 current/master report에 남긴다

## 11. Wording Policy
### 11.1 official artifact에서 허용하는 표현
- `운영 공식 결과`
- `운영 판정`
- `확정`
- `상위 해석 후보`
- `모니터링 권고`

### 11.2 raw-only artifact에서 허용하는 표현
- `raw-only`
- `분석용`
- `보조표`
- `확정 경로`
- `현장 점검 권고`

### 11.3 precursor artifact에서 금지하는 표현
- `critical/final`
- `hard evidence`
- `최종 고장 신호`
- `강한 고장 신호 확정`

### 11.4 current artifact에서 기본 금지하는 표현
- `전조형 고장` headline
- `급격 종료` headline
- `진행성 악화` headline
- `fault-like 경계 신호`

### 11.5 master report에서 반드시 설명해야 하는 것
- official current와 raw-only의 차이
- precursor report와 fault signal report의 차이
- detailed report는 lineage 문서라는 점
- 어떤 순서로 읽어야 하는지

## 12. Naming Lock
### 12.1 이름만 보고 알아야 하는 것
- `raw_only`가 들어가면 raw-only 우주다.
- `current`가 들어가면 current subset/공식 current 계열이다.
- `precursor_report`는 precursor candidate 전용이다.
- `fault_signal_report`는 hard evidence 관측 사례 쪽이다.
- `master_report`는 안내 문서다.
- `detailed_report`는 lineage 문서다.

### 12.2 이름에 담지 말아야 하는 것
- 확정 원인
- truth
- evaluator 전용 jargon

## 13. Publication Policy
### 13.1 운영 전달 기본 묶음
- `fault_panel_result_current_preview_v1.csv`
- `fault_panel_result_current_report_v1.md`
- 필요 시 `fault_panel_result_precursor_report_v1.csv`
- 필요 시 `fault_panel_result_master_report_v1.md`

### 13.2 분석 전달 기본 묶음
- 운영 전달 기본 묶음 전체
- `fault_panel_result_raw_only_fault_signal_report_v1.csv`
- `fault_panel_result_raw_only_current_v1.csv`
- `fault_panel_result_detailed_report_v1.xlsx`

### 13.4 master report에서 raw-only를 다루는 방식
- master report는 raw-only artifact를 숨기지 않는다.
- 다만 raw-only artifact는 `operator 기본 읽기 순서`가 아니라 `analyst/support 추가 자료`로 묶어 다룬다.
- master report 본문에 raw-only preview/fault signal table을 직접 전개하지 않는다.
- raw-only artifact는 경로/이름/역할을 안내하되, current/precursor와 같은 headline 흐름으로 배치하지 않는다.

### 13.3 release 문서와 source 문서 관계
- source repo의 Gate 문서가 상위 정의다.
- release README/QUICKSTART/KNOWN_LIMITS는 이 정책을 전달용으로 축약한 하위 문서다.

## 14. 꼭 남겨야 하는 구분
### 14.1 official current vs raw-only current
- official current:
  - 운영 공식 결과
- raw-only current:
  - 분석용 strict subset

### 14.2 precursor report vs raw-only fault signal report
- precursor report:
  - hard evidence 없음
- raw-only fault signal report:
  - raw-only 우주에서 고장 신호 관측

### 14.3 master report vs detailed report
- master report:
  - 읽는 순서와 역할 안내
- detailed report:
  - lineage와 상세 근거

### 14.4 current report vs master report
- current report:
  - `official current`의 설명/요약 문서
  - current preview와 함께 operator가 먼저 읽는 공식 current semantics 문서
- master report:
  - artifact 안내, cross-artifact 비교, fallback orientation 문서
  - current report가 있을 때 이를 대체하지 않으며, current report가 없을 때도 안내/fallback 의미만 가진다.

### 14.5 current state vs event interpretation
- current 계열:
  - 현재 운영 상태 중심
- event 계열:
  - retrospective 사건 해석 중심

### 14.6 maintenance lane vs safety/control lane
- maintenance lane:
  - 점검/세척/구성 확인 중심
- safety/control lane:
  - 센서/차단/정책 검토 중심

## 15. 남아 있는 잠정 영역
- operator-facing에 `problem_class`를 직접 보여줄지 여부
- safety/control lane을 operator-facing artifact 어디까지 직접 노출할지
- detailed report에 event semantics summary를 어느 수준까지 전면 배치할지

## 16. 이후 코드 패치에서 바뀔 가능성이 높은 지점
- 자동 오픈 우선순위
- master report 안내 문구
- detailed report 시트 구성
- raw-only fault signal report의 audience 표현
- precursor report의 `고위험 관찰` 컬럼 구조
- artifact projection 칼럼 구성

## 17. Decision Log에 바로 올릴 질문
- operator-facing official current의 `softened event summary` 조건부 노출 규칙은 [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md) 에서 잠겼다.

## 18. Gate 5 체크리스트
- artifact 이름만 보고 공식성/출처/대상을 유추할 수 있는가
- official current와 raw-only 보조표를 혼동하게 만드는 문구가 없는가
- precursor report와 hard evidence 보조표가 row universe를 섞지 않는가
- master report가 새 판정을 만들지 않고 안내 역할만 하는가
- detailed report가 lineage 문서라는 점이 유지되는가
- artifact별 projection이 canonical result object와 semantics contract를 어기지 않는가

## 19. 근거 source
- [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
- [build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)
- [smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)

## 20. 다음 연결 문서
- 상위 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- decision log 1호:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- Gate 2B canonical multi-axis result model:
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- Gate 4A event semantics / operator semantics contract:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
- Gate 6B taxonomy/action policy lock:
  - [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- Gate 4 hard evidence 경계 초안:
  - [OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4_HARD_EVIDENCE_BOUNDARY_V1.md)
- Gate 6 taxonomy/action survey:
  - [OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6_TAXONOMY_ACTION_SURVEY_V1.md)
- 결정 로그 템플릿:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_TEMPLATE_V1.md)
- 브랜치/파킹 로트 템플릿:
  - [OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_PARKING_LOT_TEMPLATE_V1.md)

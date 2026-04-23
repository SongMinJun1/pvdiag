<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1

## 1. 목적
- 본 문서는 [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md) 를 실제 패치 가능한 체크리스트로 내린 문서다.
- 목적은 아래 네 가지다.
  - runtime pack surface patch에서 어떤 파일을 건드려야 하는지 고정
  - artifact별로 허용되는 수정과 금지되는 수정을 구분
  - smoke/build/release sync 범위를 빠뜨리지 않게 함
  - 다음 실제 코드 패치 turn에서 `무엇부터 적용할지` 바로 체크할 수 있게 함

## 2. 상위 기준
- Gate 5 projection policy:
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- Gate 7 implementation order lock:
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- DL-001:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- DL-002:
  - [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)

## 3. 범위
### 3.1 이번 체크리스트에 포함
- runtime redesign 레인의 artifact 이름/컬럼명/guide wording
- master report read order / artifact 역할 설명
- detailed report `definitions` 시트 표현
- smoke/build에서 artifact 이름과 핵심 컬럼을 검증하는 부분
- release runtime README/summary 중 runtime artifact 설명 축

### 3.2 이번 체크리스트에서 제외
- precursor 승격 threshold
- hard evidence precedence
- `fault_like_day` 의미 변경
- safety/control lane 직접 추천 확대
- stable/handoff contract 자체 재정의

## 4. 패치 대상 파일
### 4.1 source of truth
- [release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)

### 4.2 build / sync
- [research/prognostics/build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)

### 4.3 smoke / regression
- [research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)

### 4.4 release 전달 문서
- [release/conalog_full_runtime_v1/README.md](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/README.md)
- 필요 시:
  - `release/final_delivery_v1/README.md`
  - `release/final_delivery_v1/QUICKSTART.md`
  - `release/final_delivery_v1/KNOWN_LIMITS.md`

## 5. artifact별 체크리스트
### 5.1 `fault_panel_result_current_*`
- [ ] `official current`라는 공식성 문구가 유지되는가
- [ ] `raw-only candidate`, `임시 후보` 같은 표현이 current headline에 섞이지 않는가
- [ ] `event_type/terminal_pattern`을 current headline으로 노출하지 않는가
- [ ] current preview/current report/master report 사이 역할 설명이 충돌하지 않는가

### 5.2 `fault_panel_result_precursor_report_v1.csv`
- [ ] `전조 후보`, `고위험 관찰`, `모니터링 권고` 중심 wording을 유지하는가
- [ ] `critical/final`, `직접 고장 신호`, `최종 고장 신호` 같은 wording이 headline/핵심 컬럼에 섞이지 않는가
- [ ] hard evidence row universe와 겹치지 않는다는 설명이 유지되는가

### 5.3 `fault_panel_result_raw_only_current_*`
- [ ] artifact 이름만 보고 raw-only임을 알 수 있는가
- [ ] `운영 공식 current`처럼 읽히는 표현이 없는가
- [ ] strict subset / analyst-facing 의미가 유지되는가

### 5.4 `fault_panel_result_raw_only_fault_signal_report_v1.csv`
- [ ] 이름에 `raw_only`가 유지되는가
- [ ] `공식 hard-fault ledger`, `운영 공식 결과` 같은 금지 wording이 없는가
- [ ] `raw-only 고장 신호`, `확정 경로`, `현장 점검 권고` 중심 설명이 유지되는가
- [ ] analyst/support artifact라는 설명이 master/detailed/definitions에서 일관되는가

### 5.5 `fault_panel_result_master_report_v1.md`
- [ ] master report가 새 판정을 만드는 문서처럼 쓰이지 않는가
- [ ] 운영자 기본 읽기 순서와 분석가 기본 읽기 순서가 Gate 5 정책과 일치하는가
- [ ] official current / precursor / raw-only fault signal / detailed의 차이를 분명히 설명하는가

### 5.6 `fault_panel_result_detailed_report_v1.xlsx`
- [ ] `definitions` 시트가 current semantics / event semantics / raw-only 공식성 구분을 보존하는가
- [ ] detailed가 lineage 문서라는 설명이 유지되는가
- [ ] raw-only fault signal report 정의가 analyst/support artifact 기준으로 적혀 있는가

## 6. 코드 touchpoint 체크리스트
### 6.1 상수 / 파일명
- [ ] `ROOT_*_NAME` 계열이 Gate 5 naming lock과 일치하는가
- [ ] deprecated artifact 이름이 남아 있지 않은가

### 6.2 report builder
- [ ] live current preview / raw-only current preview / precursor report / raw-only fault signal report builder가 row universe를 섞지 않는가
- [ ] guide wording helper가 artifact audience를 섞지 않는가
- [ ] master report summary text가 official/raw-only를 같은 공식성으로 말하지 않는가

### 6.3 definitions / detailed export
- [ ] `definitions_df`의 설명 문구가 Gate 5 matrix와 맞는가
- [ ] detailed frame 시트명과 역할 설명이 artifact policy와 맞는가

### 6.4 publish / summary
- [ ] published output summary에서 artifact 이름과 역할이 혼동되지 않는가
- [ ] `pack_summary_v1.json` 계열에서 stale naming이 남아 있지 않은가

## 7. smoke / build 체크리스트
### 7.1 smoke test
- [ ] root output artifact 이름이 현재 naming과 일치하는가
- [ ] precursor report required columns가 현재 schema와 맞는가
- [ ] raw-only fault signal report required columns가 현재 schema와 맞는가
- [ ] precursor report와 raw-only fault signal report non-overlap 검증이 유지되는가
- [ ] preview/current/master/detailed 존재 검증이 현재 read order와 어긋나지 않는가

### 7.2 build sync
- [ ] package 복사본으로 내려가는 파일과 source 파일이 같은 계약을 반영하는가
- [ ] build script 안의 artifact inventory가 현재 Gate 5 naming과 맞는가

### 7.3 release 전달 문서
- [ ] README/QUICKSTART가 official current와 raw-only를 혼동하게 만들지 않는가
- [ ] stable/handoff contract와 runtime redesign contract를 같은 층처럼 적지 않는가

## 8. 패치 순서
1. `run_full_algorithm_pack.py` wording / definitions / master report 수정
2. smoke test 기대치 및 schema 체크 수정
3. build script / pack summary naming 정리
4. release README/summary 보정
5. conalog 1회 실행 + smoke 재검증

## 9. 이번 체크리스트로 바로 허용되는 패치
- artifact 이름/컬럼명/guide wording 정리
- definitions 시트 설명 정리
- master report read order / 안내 문구 정리
- smoke/build/release 문서 동기화

## 10. 이번 체크리스트로도 아직 금지되는 패치
- precursor 승격 threshold 조정
- hard evidence 판정 규칙 변경
- `fault_like_day` 해석 변경
- safety/control lane direct recommendation 확대
- stable/handoff direct contract 재정의

## 11. 완료 기준
- Gate 5 matrix의 각 artifact가 실제 코드/문서/smoke에서 같은 의미로 읽힌다.
- current / precursor / raw-only current / raw-only fault signal / master / detailed의 공식성과 audience가 충돌하지 않는다.
- smoke/build/release까지 같은 artifact naming과 역할을 사용한다.

## 12. 다음 단계
- 이 체크리스트 기준으로 `runtime pack surface wording / guide / definitions patch` 수행
- 그 다음 `stable/handoff boundary note 최소 패치 범위` decision 검토
- 그 다음 `반례 세트`와 `algorithm gating patch` 여부 판단

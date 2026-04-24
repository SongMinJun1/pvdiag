<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1

## 1. 목적
- 본 문서는 `MLPE runtime redesign`에서 실제 패치를 어떤 순서로 넣어야 하는지 잠그는 구현 순서 문서다.
- 목적은 아래 다섯 가지다.
  - 문서 결정을 코드 패치 순서로 번역한다.
  - `docs-only 정합성 패치`, `artifact/schema 패치`, `알고리즘 패치`, `release 재생성`의 순서를 고정한다.
  - 아직 잠기지 않은 질문 때문에 섣불리 들어가면 안 되는 패치를 명확히 금지한다.
  - 여러 패치 묶음이 동시에 움직일 때 어느 문서/결정을 먼저 따라야 하는지 정한다.
  - Gate 5 projection policy를 실제 patch checklist로 내려앉힐 기준을 만든다.

## 2. 이 문서가 전제하는 상위 기준
- 상위 로드맵: [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- current/raw-only/operator semantics lock: [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- stable/runtime contract boundary lock: [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- signal role / observability / result model:
  - [OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2_SIGNAL_ROLE_MATRIX_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2A_OBSERVABILITY_EVIDENCE_MATRIX_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2B_CANONICAL_MULTIAXIS_RESULT_MODEL_V1.md)
- semantics / output / taxonomy lock:
  - [OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE4A_EVENT_OPERATOR_SEMANTICS_CONTRACT_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)

## 3. 상태
- 상태: `working draft`
- 의미:
  - 현재까지 잠긴 Gate/decision을 반영한 구현 순서 초안이다.
  - `Gate 5 checklist`, `stable boundary note 최소 패치 범위`, `반례 세트 V1`까지는 존재한다.
  - `MLPE ambiguous`, `common-cause risk`의 초기 승인 seed는 생겼지만, BR-031 이후 `exact same-day`와 `±7일 near-window backlog`의 해석 분리가 아직 남아 있으므로 algorithm gating 단계는 여전히 보수적으로 진행해야 한다.
- 현재 우선 기준:
  - DL-001, DL-002가 Gate 7보다 우선한다.
  - stable/handoff 문서는 별도 계약으로 읽고, runtime redesign 패치를 stable 문서군에 직접 확장하지 않는다.
  - BR-036 judgment rubric이 exact/supportive/reservoir/backlog/blocker 해석 우선권을 가진다.
  - DL-020 기준으로 patch 방향 자체는 `docs/evidence-first -> blocker-target-first -> algorithm-last` 순서를 따른다.

## 4. 기본 원칙
### 4.1 문서 결정이 먼저, 코드 패치가 나중
- Gate / decision log로 잠기지 않은 규칙은 코드에서 먼저 구현하지 않는다.

### 4.2 한 번에 한 층만 바꾼다
- 같은 패치 묶음에서 아래를 동시에 바꾸지 않는다.
  - 용어/가이드
  - artifact row universe
  - algorithm threshold/rule
  - taxonomy/action semantics

### 4.3 official current와 raw-only는 끝까지 분리
- 어떤 구현 단계에서도 raw-only artifact를 official current 대체물로 승격시키지 않는다.

### 4.4 stable/handoff와 runtime redesign는 별도 레인
- Gate 7의 기본 구현 대상은 runtime redesign 레인이다.
- stable/handoff 문서군 패치는 `boundary note` 수준을 넘기면 별도 decision이 필요하다.

## 5. 구현 레인
### 5.1 Lane A. 문서 정합성 / 용어 정리
- 목적:
  - stale wording, old artifact naming, accepted decision mismatch 제거
- 대표 파일:
  - `docs/OPS_CONALOG_*`
- 허용:
  - definitions 보정
  - stale next-step 정리
  - accepted/proposed 상태 갱신
- 금지:
  - 문서만으로 아직 미결인 알고리즘 규칙을 확정하는 것

### 5.2 Lane B. artifact/schema projection 패치
- 목적:
  - Gate 5 projection policy를 실제 파일명/컬럼명/definitions/master report에 반영
- 대표 파일:
  - [run_full_algorithm_pack.py](/Users/b9gc/pvdiag/release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py)
  - [build_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/build_conalog_full_runtime_pack_v1.py)
  - [smoke_test_conalog_full_runtime_pack_v1.py](/Users/b9gc/pvdiag/research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py)
- 허용:
  - 파일명/컬럼명/guide wording
  - definitions 시트 갱신
  - master report 읽는 순서 갱신
- 금지:
  - precursor rule 자체 변경
  - hard evidence boundary 자체 변경

### 5.3 Lane C. semantics enforcement 패치
- 목적:
  - operator headline에서 event semantics 금지
  - raw-only/offical current 공식성 구분 enforcement
- 대표 파일:
  - `run_full_algorithm_pack.py`
  - 필요 시 release README / QUICKSTART / KNOWN_LIMITS
- 허용:
  - current/precursor/master wording 정리
  - operator/analyst exposure gating
- 금지:
  - stable path direct output contract 재정의

### 5.4 Lane D. algorithm gating 패치
- 목적:
  - Gate 3 / Gate 4 규칙을 실제 코드에 반영
- 대표 파일:
  - [research/prognostics/runtime_rawonly_chain_common_v1.py](/Users/b9gc/pvdiag/research/prognostics/runtime_rawonly_chain_common_v1.py)
  - 필요 시 [pv_ae/panel_day_engine.py](/Users/b9gc/pvdiag/pv_ae/panel_day_engine.py)
- 선행 조건:
  - Gate 3 precursor 승격 규칙의 미결 질문이 더 좁아져 있어야 한다.
  - Gate 4 hard evidence 경계의 미결 질문이 더 좁아져 있어야 한다.
- 금지:
  - 반례 세트 없이 threshold/rule을 바로 조정

### 5.5 Lane E. taxonomy / action patch
- 목적:
  - Gate 6B policy lock을 실제 출력 컬럼/문구/axis projection에 반영
- 대표 파일:
  - `run_full_algorithm_pack.py`
  - heuristic 관련 문서/설명문
- 선행 조건:
  - Gate 5 projection checklist가 먼저 있어야 한다.
  - safety/control lane direct exposure 질문이 정리돼 있어야 한다.

### 5.6 Lane F. build / release / smoke sync
- 목적:
  - source, smoke, release artifact를 같은 계약으로 맞춤
- 대표 파일:
  - `research/prognostics/build_*`
  - `research/prognostics/smoke_test_*`
  - `release/conalog_full_runtime_v1/*`
- 규칙:
  - source patch만 넣고 build/release/smoke를 뒤로 미루지 않는다.

## 6. 권장 패치 순서
### 6.1 Step 0. 문서/결정 정합성
- 내용:
  - Gate / decision / mapping note / glossary 정합성 정리
- 완료 기준:
  - accepted/proposed 상태가 실제와 맞는다.
  - artifact naming이 모두 현재 기준과 맞는다.

### 6.2 Step 1. Gate 5 patch checklist 작성
- 내용:
  - Gate 5 projection policy를 실제 파일/컬럼/artifact별 checklist로 내린다.
- 산출물:
  - [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- 완료 기준:
  - artifact별로 `무엇을 바꾸고 무엇을 건드리지 말아야 하는지`가 체크리스트로 존재한다.

### 6.3 Step 2. Lane B/C docs-first runtime patch
- 내용:
  - runtime pack 쪽 이름/컬럼/guide/master/detailed definitions patch
  - operator/current/raw-only/precursor wording patch
- 대표 대상:
  - `run_full_algorithm_pack.py`
  - smoke/build 문서성 체크
- 완료 기준:
  - Gate 5, DL-001, DL-002와 모순 없는 artifact surface가 된다.

### 6.4 Step 3. stable/handoff boundary note 최소 패치 여부 결정
- 내용:
  - stable 문서군에 최소 경계 문구를 넣을지 별도 decision으로 잠근다.
- 완료 기준:
  - stable 레인을 건드릴지 말지 결정이 존재한다.

### 6.5 Step 4. 반례 세트 1차 작성
- 내용:
  - precursor / hard evidence / MLPE 특수 케이스 / common-cause / raw-only vs official 사례 묶음 작성
- 완료 기준:
  - algorithm gating patch 전에 최소 반례 세트가 준비된다.
- 현재 산출물:
  - [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- 남은 조건:
  - `MLPE ambiguous`에서 `센서·피드백형` 외에 `장치 응답 이상형` top1 또는 회복/재발 사례를 더 확보해야 한다.
  - `common_cause_risk`에서 운영 이벤트/통신 흔들림 연계 사례와 `group_off_event` 직접 중첩 사례를 더 확보해야 한다.
  - `official current`와 direct overlap하는 common-cause 사례는 `2026-04-22` tri-site scan 기준 아직 미관측이라 별도 수집이 필요하다.
  - BR-029 기준으로 provisional shortlist는 curated counterexample seed로 승격될 수 있지만, 이는 `exact missing family closure`와는 별개다.
  - BR-031 기준 widened `±7일 near-window overlap backlog`는 실제 backlog 로 존재하지만, `same-day exact family`와 분리된 채로 먼저 분류돼야 한다.

### 6.6 Step 4A. existing signal -> score axis map 정리
- 내용:
  - 현재 있는 warning / hard evidence / suppressor / explanation 신호를 다축 score axis에 연결한다.
- 완료 기준:
  - `single signal -> direct label`이 아니라 `signal -> score -> projection`으로 설명 가능하다.
- 현재 산출물:
  - [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)

### 6.6A Step 4B. evidence-axis sidecar expansion
- 내용:
  - 기존 raw/audit fields만으로 새 evidence-only sidecar axis를 만든다.
- 목적:
  - exact family를 억지 closure하지 않고 blocker / hold / review 설명력을 올린다.
- 우선순위:
  1. `report_entry_friction_axis`
  2. `recovery_recurrence_axis`
  3. `common_cause_synchrony_axis`
- 조건:
  - new top-level fault label을 직접 만들지 않는다.
  - operator headline으로 직접 승격하지 않는다.
  - first use는 explanation / blocker split / hold-review support로 제한한다.
- 진행 상태:
  - BR-040 기준 `report_entry_friction_axis`는 builder + smoke까지 구현 완료
  - BR-041 기준 `recovery_recurrence_axis`도 builder + smoke까지 구현 완료
- BR-043 기준 `evidence manifest / consolidated pack root`도 builder + smoke까지 구현 완료
- next 순서는 `common_cause_synchrony_axis`
- 단, BR-049 기준 practical execution lane에는 confusion-reduction prelude가 추가됐고 세 step 모두 구현 완료됐다:
  - `mixed_scope_disentangle` -> `repo_role_boundary_manifest_v1`
  - `source_vs_packaged_mirror_boundary` -> `repo_mirror_boundary_manifest_v1`
  - `active_builder_entrypoint_registry` -> `repo_active_builder_entrypoint_registry_v1`

### 6.6B Step 4C. evidence manifest / consolidated pack root
- 내용:
  - 현재 흩어진 evidence artifact를 하나의 index/manifest로 묶는다.
- 목적:
  - 지금 하고 있는 sidecar/evidence work를 잊지 않고 이어가기
  - current sidecar와 temp scan, base result artifact의 연결을 한 번에 읽기
- 최소 필드:
  - `evidence_family`
  - `judgment_role`
  - `artifact_path`
  - `artifact_kind`
  - `canonical_or_temp`
  - `owner_branch`
  - `latest_decision_log`
  - `repro_command`
- 완료 기준:
  - BR-040, BR-041, 기존 temp scan artifact가 하나의 manifest에서 연결된다.
  - BR-043 기준 완료됨:
    - `panel_day_engine_evidence_manifest_v1.csv`
    - `panel_day_engine_evidence_manifest_summary_v1.csv`
    - `panel_day_engine_evidence_pack_manifest_v1.json`
    - `evidence_pack_root/`
- 이후 exact-family 재탐색과 cross-axis review는 이 pack root를 default entry point로 사용한다.
- BR-049 기준 이 runtime order 자체는 유지하되, `repo_role_boundary_manifest_v1`, `repo_mirror_boundary_manifest_v1`, `repo_active_builder_entrypoint_registry_v1`를 먼저 읽어 current worktree/read-path 혼선을 줄인다.
- BR-050 기준 `common_cause_synchrony_axis` sidecar까지 구현됐으므로, 다음은 세 evidence axis를 함께 읽는 cross-axis review다.
- BR-051 기준 cross-axis review와 manifest sync가 완료됐으므로, 다음은 `local_signal_morphology_review` pool에서 exact-family missing seed를 다시 찾는 단계다.
- BR-052 기준 cleaner local morphology pool에서도 exact target top1은 `0`이므로, 다음은 `no_report_heuristic_match` attachment gap을 먼저 분해한다.
- BR-053 기준 direct `panel_day_engine.py` 변경 전 safety gate가 먼저 고정됐으므로, `no_report_heuristic_match` 분해 이후 엔진 패치가 필요해져도 safety gate packet을 먼저 통과해야 한다.
- BR-054 기준 safety gate는 이제 source/package pair, byte-identical content, deleted evidence exclusion, related-evidence check까지 포함한다.
- BR-055 기준 `no_report_heuristic_match=8`은 engine bug가 아니라 `미확정` status-gated heuristic absence로 분해됐다.
- BR-056 기준 BR-055의 near-anchor 3건은 non-fault morphology observation sidecar로만 보존되며, operator promotion과 engine patch candidate는 모두 `0`이다.
- BR-057 기준 post-BR-056 local morphology pool은 target exact closure `0`을 유지하지만, non-target hard same-day fault-family seed 5건과 sensor-feedback pressure seed 6건을 회귀/반례 재료로 분리했다.
- BR-058 기준 이 11건은 regression/counterexample packet으로 고정됐으며, target exact closure / operator promotion / engine patch candidate는 모두 `0`이다.
- BR-059 기준 BR-058 packet은 12개 required prepatch gate를 통과했으며, 이후 panel-engine algorithm patch 검토 전 이 gate를 먼저 실행해야 한다.
- BR-060 기준 panel-engine safety gate와 fault-family regression prepatch gate를 하나의 combined runbook으로 묶었으며, direct engine patch 검토 전 이 runbook을 먼저 통과해야 한다.
- BR-061 기준 result delta scorecard를 먼저 만들어 core result change와 candidate-context change를 분리하며, truth-label 평가 전에는 성능 향상 claim을 금지한다.
- BR-062 기준 baseline/post scorecard compare를 실행해 changed metric count와 core changed flag를 먼저 확인한 뒤 result-change claim을 검토한다.
- BR-063 기준 direct engine patch rehearsal은 `critical_fault_mask` cleanup으로 통과했다: source/package mirror, safety review, BR-060 runbook, BR-061 scorecard, BR-062 compare가 모두 green이다.
- BR-064 기준 fault-family judgment candidate packet은 threshold 후보를 먼저 family/axis별 review bucket으로 분리한다: common-cause block/hold `176`, regression pressure `11`, local morphology family-shape review `10`, weak hold `12`, promotion/engine patch `0`.
- BR-065 기준 BR-064 local morphology 10건 중 8건은 recovery-only hold로 남고, 2건만 voltage-dominant hard-signal review로 좁혀졌다. 둘 다 promotion/engine patch는 `0`이다.
- BR-066 기준 evidence line은 `handoff_ready_with_index`다. 새 작업자는 BR-066 handoff index에서 시작하고, BR-064/065 재현이 막히면 새 rule이 아니라 handoff/repro layer를 먼저 고친다.
- BR-067 기준 2건의 voltage-dominant hard-signal row는 broad peer/reference artifact보다는 physical-leaning voltage-axis review로 읽힌다. 단, confirmed fault family나 threshold patch가 아니라 physical confirmation 대기 상태다.
- BR-068 기준 2건 모두 raw timestamp peer comparison에서 low-voltage/current-preserved morphology가 재확인됐다. 단, raw waveform support는 independent physical confirmation과 다르므로 threshold patch 승인으로 읽지 않는다.
- BR-069 기준 2건 모두 independent physical-confirmation layer는 아직 미충족이다. 정확한 패널 ID에 붙은 direct physical measurement와 maintenance/inspection evidence가 없으므로 threshold patch는 계속 보류한다.
- BR-070 기준 그 미충족 상태는 2건의 high-priority exact-panel evidence request로 전환됐다. 다음 행동은 evidence acquisition이며, rule tuning이 아니다.
- BR-071 기준 BR-064 strong common-cause hold 50건은 panel-local promotion blocker/regression seed로 고정됐다. common-cause spatiality를 panel-local fault-family threshold positive로 읽지 않는다.
- BR-072 기준 common-cause exact closure는 여전히 `0`이지만, `49` panels / `101` raw same-day direct rows는 `candidate_reservoir + structural_blocker`로 보존된다. 보수성은 정지가 아니라 report-lane/date-alignment 병목을 정확히 좁히는 장치다.
- BR-073 기준 그 `49` structural blockers는 no-report `13`, precursor-carryover `19`, rawonly-displaced `15`, manual-trace target `2`로 분해된다. manual target도 production patch가 아니라 trace review queue다.
- BR-074 기준 manual-trace target `2`건은 더 좁아졌다. `gangui`는 raw-only near-anchor trace-only, `ktc_ess`는 post-current 71-day mismatch이므로 official/current bridge, semantic patch, promotion/engine/threshold sums는 모두 `0`이다.
- BR-075 기준 이 common-cause evidence boundary는 실행 가능한 prepatch gate가 됐다. required gate `12/12` 통과, warning `1`은 raw-only near-anchor context-only 경고이며 approval이 아니다.
- BR-076 기준 combined algorithm prepatch runbook은 이제 3-gate contract다. direct panel-engine algorithm review 전 panel-engine safety, fault-family regression, common-cause semantic gate를 모두 통과해야 한다.

### 6.7 Step 5. Lane D algorithm gating patch
- 내용:
  - 필요 시 precursor 승격 / hard evidence 경계 코드 조정
- 조건:
  - Step 4C evidence manifest / consolidated pack root가 먼저 있어야 한다.
  - Step 4 반례 세트가 먼저 존재해야 한다.
  - Step 4A signal-to-score map이 먼저 존재해야 한다.
  - BR-029 이후에는 provisional seed promotion criteria가 먼저 잠겨 있어야 한다.
  - 그 다음 `score-to-projection decision log`가 먼저 잠겨 있어야 한다.
  - BR-036 기준으로 새 evidence가 `judgment role`로 먼저 분류돼 있어야 한다.
  - 관련 decision log가 추가로 잠겨 있어야 한다.
  - [DL-20260422-012](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_012_V1.md) 기준으로 `prefault_B_effective`는 eligibility/explanation additive evidence까지만 허용되고, `고위험 관찰` direct trigger 승격은 별도 decision 전까지 보류한다.
  - [DL-20260424-014](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_014_V1.md) 기준으로 projection은 `highest score wins`가 아니라 `eligible evidence lane -> hold/reroute cap -> actionability ceiling` 순서를 따라야 한다.
  - BR-031 backlog 를 common-cause overlap family 로 다시 쓸 거면, `same-day exact`와 분리된 provisional family인지 먼저 문서에서 잠가야 한다.

### 6.8 Step 6. Lane E taxonomy/action patch
- 내용:
  - operator-facing과 analyst-facing 축을 실제 출력에 반영
- 조건:
  - safety/control lane 직접 노출 범위가 더 좁아져 있어야 한다.

### 6.9 Step 7. build / release / smoke / run sync
- 내용:
  - source patch를 build/release/smoke/run 결과까지 연결
- 최소 검증:
  - `python -m py_compile pv_ae/panel_day_engine.py`
  - `python research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py`
  - conalog 1회 실행 또는 paper pack 재생성 확인
  - direct `pv_ae/panel_day_engine.py` patch 검토 전:
    - `python3 research/prognostics/check_panel_day_engine_patch_safety_gate_v1.py --output-dir /private/tmp/panel_engine_patch_safety_gate_check`
  - direct `pv_ae/panel_day_engine.py` algorithm patch 검토 전:
    - `python3 research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --common-cause-strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv --common-cause-exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --common-cause-structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --common-cause-trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv --output-dir /private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check`
  - direct `pv_ae/panel_day_engine.py` algorithm patch의 결과 변화 주장 전:
    - `python3 research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py --runtime-root /private/tmp/pvdiag_postmerge_j_conalog_smoke_result_delta_scorecard --prepatch-runbook-summary /private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv --output-dir /private/tmp/panel_engine_result_delta_scorecard_check`
  - direct `pv_ae/panel_day_engine.py` algorithm patch의 before/after 결과 비교:
    - `python3 research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py --baseline-scorecard-summary /private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_summary_v1.csv --post-scorecard-summary /private/tmp/panel_engine_result_delta_scorecard_post_compare_check/panel_day_engine_result_delta_scorecard_summary_v1.csv --output-dir /private/tmp/panel_engine_result_delta_scorecard_compare_check`
  - BR-063 critical bool-mask cleanup safety review:
    - `python3 research/prognostics/build_panel_day_engine_critical_bool_mask_safety_review_v1.py --output-dir /private/tmp/panel_engine_critical_bool_mask_safety_review_check`
  - BR-064 fault-family judgment candidate packet:
    - `python3 research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py --cross-axis-input /private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv --pressure-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --threshold-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv --subtype-input docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv --output-dir /private/tmp/fault_family_judgment_candidate_packet_check`
  - BR-065 local morphology family-shape review:
    - `python3 research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py --packet-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/local_morphology_family_shape_review_check`
  - BR-066 evidence handoff index:
    - `python3 -m py_compile pv_ae/panel_day_engine.py`
  - BR-067 voltage-dominant physical-vs-artifact review:
    - `python3 research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py --shape-input /private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/voltage_dominant_physical_vs_artifact_review_check`
  - BR-068 raw waveform physical-support review:
    - `python3 research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py --review-input /private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/raw_waveform_physical_support_review_check`
  - BR-069 physical confirmation requirements review:
    - `python3 research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py --raw-review-input /private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv --manual-evidence-input docs/internal/manual_field_evidence_latest.csv --output-dir /private/tmp/physical_confirmation_requirements_review_check`
  - BR-070 physical evidence request packet:
    - `python3 research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py --confirmation-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv --checklist-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_checklist_v1.csv --output-dir /private/tmp/physical_evidence_request_packet_check`
  - BR-071 strong common-cause blocker regression packet:
    - `python3 research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py --judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --output-dir /private/tmp/strong_common_cause_blocker_regression_packet_check`
  - BR-072 common-cause exact seed search:
    - `python3 research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py --judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --synchrony-input /private/tmp/common_cause_synchrony_axis_sidecar_check/panel_day_engine_common_cause_synchrony_axis_v1.csv --current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv --precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv --rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/common_cause_exact_seed_search_check`
  - BR-073 common-cause structural blocker review:
    - `python3 research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py --exact-seed-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --output-dir /private/tmp/common_cause_structural_blocker_review_check`
  - BR-074 common-cause manual trace review:
    - `python3 research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py --blocker-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv --precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv --rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/common_cause_manual_trace_review_check`
  - BR-075 common-cause semantic prepatch gate:
    - `python3 research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py --strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv --exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv --output-dir /private/tmp/common_cause_semantic_prepatch_gate_check`
  - BR-076 combined panel-engine algorithm prepatch runbook:
    - `python3 research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --packet-input /private/tmp/fault_family_regression_pressure_packet_check/panel_day_engine_fault_family_regression_pressure_packet_v1.csv --common-cause-strong-blocker-input /private/tmp/strong_common_cause_blocker_regression_packet_check/panel_day_engine_strong_common_cause_blocker_regression_packet_v1.csv --common-cause-exact-search-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --common-cause-structural-input /private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv --common-cause-trace-input /private/tmp/common_cause_manual_trace_review_check/panel_day_engine_common_cause_manual_trace_review_v1.csv --output-dir /private/tmp/panel_engine_algorithm_prepatch_runbook_br076_check`

## 7. 지금 바로 허용되는 패치
- Gate 5 projection policy를 checklist로 바꾸는 문서 패치
- runtime pack surface wording / guide / definitions patch
- master report read order 정리
- artifact 설명문 정정
- stable/runtime boundary note 필요 범위를 정하는 decision log 추가

## 8. 지금 보류해야 하는 패치
- precursor 승격 threshold 조정
- hard evidence precedence 변경
- `fault_like_day` semantics 변경
- `prefault_B_effective_days`를 단독 `고위험 관찰` threshold로 올리는 패치
- safety/control lane 직접 추천 문구 확대
- stable/handoff contract를 redesign semantics에 맞춰 재작성
- final delivery / one-click 전체 wording 최종화

## 9. 체크리스트
### 9.1 패치 시작 전
- 이 패치가 어느 Lane인지 분류했는가
- 상위 Gate / decision log가 이미 잠겼는가
- stable 레인과 runtime redesign 레인을 혼합하지 않는가

### 9.2 패치 중
- row universe를 바꾸지 않으면서 wording만 바꾸는지
- wording을 바꾸지 않으면서 rule을 슬쩍 바꾸고 있지 않은지
- build/smoke/release sync 범위를 놓치지 않았는지

### 9.3 패치 완료 후
- docs/source/build/release 중 어느 층까지 영향을 줬는지 기록했는가
- 새로운 decision log가 필요한 변경이었는지 확인했는가

## 10. 선행/후행 관계 요약
| 단계 | 선행 필요 | 후행 영향 |
| --- | --- | --- |
| Step 1 Gate 5 checklist | DL-001, DL-002, Gate 5 | Step 2, Step 6 |
| Step 2 runtime surface patch | Step 1 | Step 7 |
| Step 3 stable boundary note decision | DL-002, DL-003, mapping note | stable docs patch 여부 |
| Step 4 반례 세트 | Gate 3/4/6 survey | Step 4A, Step 5 |
| Step 4A signal-to-score map | Gate 2/3/4/6 + 반례 세트 | Step 5, Step 6 |
| Step 5 algorithm gating patch | Step 4 + Step 4A + 추가 decision | Step 6, Step 7 |
| Step 6 taxonomy/action patch | Step 1, Step 5 일부 | Step 7 |
| Step 7 build/release/smoke sync | 모든 source patch | 배포/검증 |

## 11. 지금 기준 다음 우선순위
1. `repo_role_boundary_manifest_v1`를 먼저 읽어 현재 dirty/read-path를 role 기준으로 분류한다.
2. `repo_mirror_boundary_manifest_v1`를 읽어 source mirror, package-only surface, generated artifact를 분리한다.
3. `repo_active_builder_entrypoint_registry_v1`를 읽어 현재 진입점과 archive/helper review queue를 구분한다.
4. `common_cause_synchrony_axis`를 evidence-only sidecar로 만든다.
5. `report_entry_friction_axis`, `recovery_recurrence_axis`, `common_cause_synchrony_axis`를 cross-axis review로 함께 비교한다.
6. `local_signal_morphology_review` pool에서 `MLPE ambiguous`의 장치 응답 이상형 top1 / 회복 재발 `exact same-day` seed를 다시 찾는다.
7. direct `panel_day_engine.py` patch 전에 `panel_day_engine_patch_safety_gate_v1`을 필수 관문으로 둔다.
8. safety gate는 BR-054의 pair/hash/deletion/relevance checks 기준으로 읽는다.
9. `no_report_heuristic_match` rows는 BR-055 기준 engine patch 대상이 아니며, BR-056 기준 near-anchor 3건도 non-fault observation sidecar로만 보존한다.
10. BR-058 packet은 future algorithm patch의 pre-check 재료로 사용하되, target exact closure나 direct operator promotion으로 읽지 않는다.
11. BR-059 prepatch gate를 실행해 BR-058 packet이 축소되거나 promotion/closure/engine-patch 후보로 변질되지 않았는지 확인한다.
12. BR-060 combined runbook을 실행해 panel-engine safety gate와 fault-family regression gate가 동시에 통과하는지 확인한다.
13. BR-061 result delta scorecard로 현재 result-change baseline을 고정한다.
14. BR-062 result delta scorecard compare로 future post-patch 변화량을 비교한다.
15. BR-063 direct engine cleanup rehearsal처럼 source/package mirror와 scorecard compare까지 green인 경우만 accept한다.
16. BR-064 packet에서 `local_morphology_family_candidate_review` 10건을 먼저 family-shape review 대상으로 본다.
17. BR-065 기준 2건의 `voltage_dominant_hard_signal_review`만 partial-open vs measurement/reference artifact로 재검토한다.
18. BR-066 handoff index에서 status/order/artifact/candidate/shape docs를 먼저 확인한다.
19. BR-067 기준 2건은 physical-leaning으로 좁혀졌지만, waveform/IV/maintenance/reproducible voltage-axis evidence 전에는 threshold patch로 가지 않는다.
20. BR-068 기준 raw waveform support가 생겼지만, independent physical confirmation checklist 전에는 threshold patch로 가지 않는다.
21. BR-069 기준 current evidence는 `raw_supported_confirmation_gap_hold`이므로, exact-panel physical/inspection evidence 없이는 voltage-axis threshold patch를 열지 않는다.
22. BR-070 기준 next action은 exact-panel evidence acquisition이고, evidence가 붙으면 BR-069/070을 다시 실행한다.
23. BR-071 기준 `strong_common_cause_hold_review` rows는 promotion seed가 아니라 blocker/regression pressure로만 사용한다.
24. `common_cause_risk`의 운영 이벤트 / `group_off_event` / official current 연계 `exact same-day` seed를 계속 추가하되, 새 사례는 먼저 BR-036 `judgment role`로 분류한다.
25. raw-daily same-day direct row는 `candidate reservoir`, row-universe/date-alignment mismatch는 `structural_blocker`로 먼저 읽는다.
26. BR-072 기준 현재 exact closure는 `0`이므로, 다음 common-cause 진전은 raw reservoir 추가 수집보다 report-lane/date-alignment blocker 해소 여부를 먼저 본다.
27. BR-073 기준 manual trace target은 `2` rows뿐이며, 이 둘이 data/reporting alignment issue인지 먼저 판정한다.
28. BR-074 기준 그 `2` rows도 official/current closure가 아니다. raw-only near-anchor trace와 post-current 71-day mismatch는 regression/hold evidence로 보존한다.
29. BR-075 기준 common-cause semantic patch 검토 전에는 BR-071~074 prepatch gate를 먼저 통과해야 한다. 통과는 safety precondition이지 patch approval이 아니다.
30. BR-076 기준 direct `panel_day_engine.py` algorithm patch 검토 전에는 3-gate combined runbook을 먼저 통과해야 한다.
31. BR-077 기준 현재 상태는 project-completion/navigation checkpoint에서 먼저 읽는다. 안전장치 자체는 강화됐지만, 최신 evidence/handoff manifest는 BR-076까지 따라오지 못했으므로 manifest refresh가 다음 안전한 작업이다.
32. BR-078 기준 BR-064~077 최신 evidence/handoff manifest가 생성됐다. 이후 새 scan이나 algorithm proposal은 먼저 이 manifest에 붙는지 확인한다.
33. BR-079 기준 현재 `panel_day_engine.py`는 10개 algorithm/evidence layer, 7개 evidence gap, 6개 ordered action으로 먼저 읽는다.
34. BR-080 기준 17개 subtype hypothesis는 truth backlog로 고정됐고, current exact truth support는 `0`이다.
35. BR-081 기준 episode truth map은 완료됐고, 다음은 episode truth review packet이다.
36. semantic algorithm gating patch는 episode truth review packet과 subtype-conditioned threshold replay가 끝난 뒤에만 검토한다.

## 11A. 왜 이 순서로 가는가
- exact family가 아직 비어 있는 상태에서 rule patch를 넣으면, current evidence보다 stronger semantics를 추정으로 주입하게 된다.
- 현재 evidence의 대부분은 아래 급에 있다.
  - `supportive_hint`
  - `candidate_reservoir`
  - `non_closing_backlog`
  - `structural_blocker`
- therefore:
  - 지금 단계의 우선순위는 “규칙 바꾸기”보다 “근거 급과 blocker subtype을 명확히 하는 것”이다.
- 이 문서의 순서는 보수적이라서 느린 것이 아니라, evidence grade에 맞는 순서라는 점을 DL-020에서 잠갔다.

## 11B. BR-077 현재 체크포인트
- 현재 기준점:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_077_PROJECT_COMPLETION_CHECKPOINT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_077_PROJECT_COMPLETION_CHECKPOINT_V1.md)
- 짧은 판정:
  - core safety/evidence lanes are covered enough to avoid blind algorithm patching.
  - current weakness is navigation: BR-066 handoff and BR-043/051 manifest lineage are stale relative to BR-067 through BR-076.
- 다음 안전 순서:
  1. refresh latest evidence/handoff manifest for BR-064 through BR-076.
  2. keep voltage physical evidence requests, common-cause closure, result-delta claims, and stable/final delivery sync as separate lanes.
  3. run the BR-076 3-gate algorithm prepatch runbook before any direct `panel_day_engine.py` algorithm review.
- 금지:
  - BR-077 alone does not approve a threshold change, common-cause semantic loosening, raw-only promotion, performance claim, or dirty worktree merge.

## 11C. BR-078 최신 handoff manifest
- 현재 기준점:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_078_LATEST_EVIDENCE_HANDOFF_MANIFEST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_078_LATEST_EVIDENCE_HANDOFF_MANIFEST_V1.md)
- 실행 산출물:
  - `/private/tmp/latest_evidence_handoff_manifest_br078_check/panel_day_engine_latest_evidence_handoff_manifest_v1.csv`
  - `/private/tmp/latest_evidence_handoff_manifest_br078_check/panel_day_engine_latest_evidence_handoff_manifest_summary_v1.csv`
  - `/private/tmp/latest_evidence_handoff_manifest_br078_check/panel_day_engine_latest_evidence_handoff_manifest_note_v1.md`
- 판정:
  - BR-064 through BR-077 are now indexed from one latest manifest.
  - temp artifacts are allowed to be missing later, but the manifest row's `repro_command` becomes mandatory before detailed review.
  - operator promotion, engine patch, threshold patch, stable contract change, and release regeneration authorization sums remain `0`.
- 다음 안전 순서:
  1. use BR-078 manifest before opening scattered temp roots.
  2. attach exact-panel physical evidence and rerun BR-069/070 if physical evidence exists.
  3. require official/current bridge evidence before common-cause closure work.
  4. run BR-076 3-gate runbook before direct `panel_day_engine.py` algorithm review.

## 11D. BR-079 알고리즘 진화 지도
- 현재 기준점:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_079_ALGORITHM_EVOLUTION_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_079_ALGORITHM_EVOLUTION_MAP_V1.md)
- 실행 산출물:
  - `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_layer_map_v1.csv`
  - `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_gap_audit_v1.csv`
  - `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_action_queue_v1.csv`
- 판정:
  - current algorithm is a conservative diagnostic plus evidence-gated candidate engine.
  - mapped layers `10`, gaps `7`, P0 gaps `4`, ordered next actions `6`.
  - operator promotion, engine patch, and threshold patch authorization sums remain `0`.
- 다음 안전 순서:
  1. build `panel_day_engine_subtype_truth_expansion_backlog_v1`.
  2. build `panel_day_engine_episode_truth_map_v1`.
  3. run subtype-conditioned threshold replay only after those two truth/evidence layers exist.
  4. run BR-076 3-gate runbook before any direct `panel_day_engine.py` algorithm review.
- 금지:
  - BR-079 does not approve threshold tuning, AE root-cause claims, voltage-axis loosening, common-cause semantic loosening, or monolithic refactor mixed with behavior.

## 11E. BR-080 subtype truth expansion backlog
- 현재 기준점:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_080_SUBTYPE_TRUTH_EXPANSION_BACKLOG_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_080_SUBTYPE_TRUTH_EXPANSION_BACKLOG_V1.md)
- 실행 산출물:
  - `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_v1.csv`
  - `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_summary_v1.csv`
  - `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_action_queue_v1.csv`
- 판정:
  - subtype backlog rows `17`, family summaries `6`, P0 subtype rows `12`.
  - current exact truth support sum is `0`; current candidate/shadow counts are context only.
  - operator promotion, engine patch, and threshold patch authorization sums remain `0`.
- 다음 안전 순서:
  1. build `panel_day_engine_episode_truth_map_v1`.
  2. use it to split durable precursor, one-day episode, long-gap backdating, true sudden fault, common-cause displacement, and measurement displacement.
  3. only after subtype/episode truth rows exist, open subtype-conditioned threshold replay.
- 금지:
  - BR-080 does not approve operator-facing subtype labels, threshold updates, AE root-cause claims, voltage-axis loosening, common-cause semantic loosening, or direct `panel_day_engine.py` edits.

## 11F. BR-081 episode truth map
- 현재 기준점:
  - [OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_081_EPISODE_TRUTH_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_081_EPISODE_TRUTH_MAP_V1.md)
- 실행 산출물:
  - `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_v1.csv`
  - `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_summary_v1.csv`
  - `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_action_queue_v1.csv`
- 판정:
  - episode truth map rows `244`, summary rows `10`, action rows `5`.
  - all rows are `truth_pending`.
  - bucket counts: `common_cause_or_group_episode_hold=205`, `recovery_recurrence_observation=12`, `long_gap_backdating_hold=12`, `durable_precursor_candidate_review=7`, `episode_truth_requirement=5`, `strict_anchor_sudden_review=3`.
  - operator promotion, engine patch, and threshold patch authorization sums remain `0`.
- 다음 안전 순서:
  1. build `panel_day_engine_episode_truth_review_packet_v1`.
  2. review long-gap/backdating and strict-sudden rows first.
  3. review durable precursor candidates only after common-cause and recovery-only holds are separated.
  4. open subtype-conditioned threshold replay only after reviewed episode truth exists.
- 금지:
  - BR-081 does not approve threshold tuning, semantic loosening, operator-facing precursor promotion, or direct `panel_day_engine.py` edits.

## 12. 관련 문서
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_001_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_002_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_003_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_006_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_007_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_ARTIFACT_SCHEMA_PATCH_CHECKLIST_V1.md)
- [OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE6B_TAXONOMY_ACTION_POLICY_LOCK_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)

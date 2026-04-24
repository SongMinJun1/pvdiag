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
9. `no_report_heuristic_match` rows는 BR-055 기준 engine patch 대상이 아니므로, near-anchor 3건은 별도 non-fault observation sidecar 여부만 검토한다.
10. `strong_common_cause_hold_review` rows는 promotion seed가 아니라 blocker/regression pressure로만 사용한다.
11. `common_cause_risk`의 운영 이벤트 / `group_off_event` / official current 연계 `exact same-day` seed를 계속 추가하되, 새 사례는 먼저 BR-036 `judgment role`로 분류한다.
12. raw-daily same-day direct row는 `candidate reservoir`, row-universe/date-alignment mismatch는 `structural_blocker`로 먼저 읽는다.
13. 그 다음에야 algorithm gating patch 검토

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

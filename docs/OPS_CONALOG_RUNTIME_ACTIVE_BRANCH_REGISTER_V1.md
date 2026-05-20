<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## 1. 목적
- 본 문서는 `runtime redesign` 메인 라인과 현재 열려 있는 branch / parking lot을 한 곳에서 보게 만드는 운영 레지스터다.
- 목적은 아래 셋이다.
  - 메인 라인과 옆가지가 섞여 기억되는 일을 막는다.
  - branch가 열린 이유, 복귀 조건, 금지 작업을 빠르게 다시 확인하게 한다.
  - 이후 decision log / Gate 문서 / 패치 묶음이 어느 레인을 따라야 하는지 즉시 알 수 있게 한다.

## 2. 메인 라인 현재 위치
- 기준 로드맵:
  - [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
  - [OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE7_IMPLEMENTATION_ORDER_LOCK_V1.md)
- 현재 메인 라인 상태 요약:
  - `Lane A/B/C`: 문서 정합성, operator/current/raw-only 분리, artifact/schema surface 정리는 많이 진행됨
  - `Step 4 / 4A`: 반례 세트 V1, signal-to-score map, common-cause / MLPE ambiguous 초기 seed 확보됨
  - `Lane D`: direct gating/onset 변경 전 단계이며, shadow evidence / audit / explanation 정리 중심으로 진행 중
- 지금 메인 라인에서 이미 잠긴 것:
  - `official current`와 `raw-only`의 공식성 분리
  - `prefault_B_effective`는 eligibility / explanation additive evidence까지만 사용
  - `broad history / proximal / strict / warning` common-cause 축 분리
  - raw-only fault signal 표면의 `group root / subgroup base / subgroup cluster` 분리
- 지금 메인 라인에서 아직 잠그지 않은 것:
  - `subgroup common-cause`를 direct gating에 올릴지
  - `degradation onset fallback`에 persistence / common-cause guard를 넣을지
  - `warning_proximal_common_cause_flag`를 operator-facing surface로 올릴지

## 3. 운영 규칙
- 메인 라인을 흔드는 질문이 생기면 먼저 이 문서에 `BR-...` 항목을 연다.
- branch에서 바로 rule patch로 점프하지 않고, 허용 작업 / 금지 작업 / 복귀 조건을 먼저 적는다.
- branch가 바로 풀리지 않으면 `PL-...`로 내리고 review 조건을 남긴다.
- 패치 묶음은 가능하면 아래 셋 중 하나로 분류해 기록한다.
  - `mainline`
  - `branch work`
  - `parking safety action`
- branch가 `3개` 이상 동시에 `open/analyzing`이면 메인 라인 진행을 잠시 멈추고 Gate 7 / cross-gate audit을 다시 본다.

## 4. 빠른 요약 표

### 4.1 메인 라인
| lane | status | summary |
| --- | --- | --- |
| Lane A/B/C | active | wording / surface / schema / report split 정리 진행 중 |
| Step 4 / 4A | active | 반례 세트와 signal-to-score map 확보, 계속 보강 중 |
| Lane D | shadow-only | direct gating/onset 변경 전 단계, audit/evidence 정리 위주 |

### 4.2 열린 브랜치
| branch_id | status | type | current_gate | return_gate | title |
| --- | --- | --- | --- | --- | --- |
| BR-20260423-001 | analyzing | B | Gate 3 | Gate 7 | subgroup common-cause direct gating |
| BR-20260423-002 | shadow-audit | B | Gate 3 | Gate 7 | degradation onset fallback guard |
| BR-20260423-003 | analyzing | E | Gate 5 | Gate 7 | raw-only cluster/operator exposure boundary |
| BR-20260423-004 | shadow_audit_implemented | B | Gate 3 | Gate 7 | secondary warning window selection |

### 4.3 파킹 로트
| parking_id | status | related_gate | title | risk | review_after |
| --- | --- | --- | --- | --- | --- |
| PL-20260423-001 | parked | Gate 5 | warning_proximal_common_cause operator exposure | medium | strict-trigger surface 안정화 후 |
| PL-20260423-002 | parked | Gate 7 | final_delivery/stable 문서군 최종 wording sync | low | runtime semantics 추가 변동 종료 후 |

## 5. 열린 브랜치 상세

## [BR-20260423-001] subgroup common-cause direct gating
- `status`: shadow_audit_implemented
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

### 이슈 요약
- `site_event/group_off`는 어느 정도 잡히지만, `subgroup/base-level breadth` 흔들림을 direct gating에 올릴지 여부는 아직 열려 있다.

### 왜 브랜치인가
- 이걸 바로 메인 라인 rule로 넣으면 `precursor gating`과 `common-cause 해석`이 한 번에 바뀌어 결과 해석이 크게 흔들릴 수 있다.

### 허용 작업
- shadow flag 추가
- audit/evidence 비교
- tri-site A/B 표 생성
- broad history / proximal / strict / warning 분리 검토

### 금지 작업
- direct `prefault_B_effective` 억제 확장
- official current 승격/강등 규칙 변경
- onset fallback 직접 수정

### 필요한 추가 근거
- tri-site 기준 subgroup flag가 실제 false positive를 얼마나 줄이는지
- official current / precursor와 subgroup common-cause direct overlap 사례
- site-wide common-cause와 subgroup common-cause의 구분 안정성

### 잠정 판단
- subgroup common-cause는 shadow / audit / explanation 축으로는 유효하다.
- direct gating으로 올리기엔 아직 한 단계 더 근거가 필요하다.
- 2026-04-23 tri-site 가정 비교표 기준:
  - `prefault_B_effective` row `37` 감소
  - `local_precursor_any` row `9` 감소
  - future final-fault coverage 손실 `0`
  - official current 근접 overlap `0 / 6`
- 즉 “당장 큰 손실은 안 보인다”는 신호는 있지만, direct gating 승격 결론을 잠글 만큼은 아직 아니다.

### 복귀 조건
- subgroup shadow flag와 broad/proximal 분리 결과를 표로 정리
- direct gating 전후 A/B 차이를 최소 한 번 검토
- 필요 시 decision log 초안 작성

### 관련 문서/결정
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_001_SUBGROUP_COMMON_CAUSE_DIRECT_GATING_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_001_SUBGROUP_COMMON_CAUSE_DIRECT_GATING_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE2C_EXISTING_SIGNAL_SCORE_MAP_V1.md)

## [BR-20260423-002] degradation onset fallback guard
- `status`: shadow-audit
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

### 이슈 요약
- 현재 `retrospective_onset` fallback은 첫 `degradation` row 하나만 있어도 onset을 당길 수 있어 backdating 과민 위험이 있다.

### 왜 브랜치인가
- onset fallback을 바꾸면 `전조날짜`, `사건유형`, `전조형 고장` 해석까지 넓게 흔들릴 수 있다.

### 허용 작업
- 사례 deep dive
- onset vs strict-trigger 간격 분석
- persistence/common-cause guard 후보 비교

### 금지 작업
- fallback 규칙 즉시 변경
- panel_day_engine core threshold 조정
- current surface semantics 변경

### 필요한 추가 근거
- `degradation_strong -> fault_like_strong`로 이어지는 대표 사례
- false backdating처럼 보이는 사례
- common-cause 겹침과 onset backdating의 상관

### 잠정 판단
- guard 필요성은 높아 보이지만, 지금은 evidence 보강 단계다.
- 2026-04-23 tri-site gap/persistence 표 기준:
  - `gangui`: fallback `10`, median gap `1d`, persistent span>=2 `5`
  - `ktc_ess`: fallback `10`, median gap `270d`, one-day span `9`
- 현재 숫자만 보면 `pure persistence guard`는 `gangui`도 과하게 건드릴 수 있고, `long-gap 계열 guard`가 더 유망하다.
- 2026-04-23 A/B 후보 정제 기준:
  - `G1_extreme_longgap_one_day`: `7 panels`, 전부 `ktc_ess`
  - `G2b_longgap_and_subgroup_one_day`: `6 panels`, 전부 `ktc_ess`
  - `G2_longgap_or_subgroup_one_day`는 `gangui gap 0d subgroup-only` `3건`까지 잡아 제외
- 2026-04-23에는 `G1`을 shadow audit flag로만 추가한다.
- 실제 onset fallback / 사건유형 판정은 바꾸지 않고, fresh tri-site rerun에서 flag 분포와 기존 판정 불변성을 확인한다.

### 복귀 조건
- `G1` shadow audit flag fresh tri-site rerun 완료
- flag 적용 후보와 기존 사건유형 불변성 확인

### 관련 문서/결정
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md)
- [OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_COUNTEREXAMPLE_SET_V1.md)
- [OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_CROSS_GATE_DESIGN_GAP_AUDIT_V1.md)

## [BR-20260423-003] raw-only cluster/operator exposure boundary
- `status`: analyzing
- `branch_type`: E
- `current_gate`: Gate 5
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

### 이슈 요약
- raw-only fault signal 표면은 `row`, `group root`, `subgroup base`, `subgroup cluster`가 함께 보이지만, 이 중 어디까지를 operator-facing으로 설명할지 아직 완전히 잠기지 않았다.

### 왜 브랜치인가
- cluster는 해석력은 좋지만, operator-facing까지 올리면 사건 수처럼 과대 해석될 수 있다.

### 허용 작업
- surface naming 정리
- master report / definitions wording 보강
- cluster count와 row count의 관계 설명

### 금지 작업
- raw-only artifact를 official current처럼 승격
- cluster를 incident 확정 count처럼 표기

### 필요한 추가 근거
- cluster 휴리스틱이 실제 analyst reading에 얼마나 도움이 되는지
- operator 문서에서 cluster까지 보여줘야 하는지 여부

### 잠정 판단
- `group root / subgroup base / subgroup cluster` 분리는 유효하다.
- 현재는 analyst/support 보조값으로 두는 편이 안전하다.

### 복귀 조건
- cluster 표면의 역할이 `analyst only`인지 `master report 보조`인지 결정
- 필요하면 별도 decision log 생성

### 관련 문서/결정
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_003_RAWONLY_CLUSTER_OPERATOR_EXPOSURE_BOUNDARY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_003_RAWONLY_CLUSTER_OPERATOR_EXPOSURE_BOUNDARY_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_008_V1.md)
- [OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260422_009_V1.md)

## [BR-20260423-004] secondary warning window selection
- `status`: analyzing
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

### 이슈 요약
- 현재 onset 로직은 secondary warning 중 가장 이른 날짜 하나가 너무 이르면, 이후 허용 window 안의 secondary warning을 다시 보지 않고 degradation fallback 또는 trigger-only로 내려갈 수 있다.

### 왜 브랜치인가
- 이 후보는 `retrospective_onset_date`, `onset_method`, `전조흔적_flag`, `사건유형`을 바꿀 수 있고, 특히 `gangui` 급작/전조 분포를 크게 움직일 수 있다.

### 허용 작업
- first-secondary-only counterfactual 분석
- later qualified secondary warning 후보 표 생성
- gangui/ktc_ess 후보별 common-cause 문맥 확인

### 금지 작업
- 즉시 production onset 로직 변경
- G1 actual suppression rule 승격

### 잠정 판단
- BR-002 G1 actual rule보다 BR-004를 먼저 봐야 한다.
- 2026-04-23 audit-only recheck 기준:
  - total candidate panels `45`
  - `gangui` `36`, `ktc_ess` `9`
  - G1 hit `7` 전부가 later qualified secondary warning을 가진다.
- 2026-04-23 BR-004 shadow/counterfactual 기준:
  - BR-004 candidate panels `50`, changed panels `112`, event-type flips `30`
  - `conalog` changed `58`은 event flip이 아니라 `method_provenance_only_primary_marker_mismatch`
  - current G1 hits는 BR-004 적용 가정에서 `7 -> 0`
- 2026-04-23 false-positive risk review 기준:
  - `trigger_only_to_precursor` `30건`
  - `ktc_ess` `3건`은 `review_supported_context`
  - `gangui` `27건` 중 `1건`은 `review_supported_context`, `26건`은 `review_persistent_secondary_only`
  - `gangui` `26건`은 common-cause overlap은 약하지만 두 panel-root cluster에 집중되어 단순 잡음으로 버리기 어렵다.

### 복귀 조건
- BR-004 shadow/counterfactual 변화량 확보: 완료
- G1 후보를 BR-004 적용 후 다시 재계산: 완료, `7 -> 0`
- `trigger_only_to_precursor` 30건 false-positive risk review: 완료
- `secondary_window_selected_onset` shadow/audit column patch 후보 작성: 완료
- tri-site shadow column validation: 완료
- operator-facing event semantics 변경 여부는 별도 승인 전까지 보류

### shadow patch 결과
- audit columns `9개` 추가:
  - `secondary_window_candidate_flag`
  - `secondary_window_selected_onset_date`
  - `secondary_window_selected_marker`
  - `secondary_window_selected_gap_days`
  - `secondary_window_qualified_count`
  - `secondary_window_too_early_count`
  - `secondary_window_change_class`
  - `secondary_window_review_tier`
  - `secondary_window_reason`
- `/private/tmp/br004_shadow_columns_check/` 검증 기준:
  - raw-only audit 공통 columns 동일
  - raw-only final verdict 동일
  - `secondary_window_candidate_패널수` `112`
  - `secondary_window_trigger_only_to_precursor_패널수` `30`
  - `secondary_window_review_required_패널수` `30`

### 관련 문서/결정
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_004_SECONDARY_WARNING_WINDOW_SELECTION_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_004_SECONDARY_WARNING_WINDOW_SELECTION_V1.md)
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md)

## 6. 파킹 로트 상세

## [PL-20260423-001] warning_proximal_common_cause operator exposure
- `status`: parked
- `source_branch_id`: BR-20260423-001
- `related_gate`: Gate 5
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `review_after`: strict-trigger surface 안정화 후

### 보류 이유
- `warning_proximal_common_cause_flag`는 현재 확인 기준 미확정 꼬리에만 남아 있어, 지금 올리면 operator-facing 해석을 다시 넓힐 위험이 있다.

### 현재 위험도
- medium

### 지금 허용되는 최소 조치
- audit / definitions 설명 유지

### 다시 열 조건
- warning-anchor 사례가 실제 operator 판단에 유익하다는 근거가 더 생길 때

### 예상 복귀 지점
- Gate 5

### 관련 근거
- [OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_MLPE_RUNTIME_REDESIGN_V1.md)
- [OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE5_OUTPUT_POLICY_V1.md)

## [PL-20260423-002] final_delivery/stable 문서군 최종 wording sync
- `status`: parked
- `source_branch_id`: BR-20260423-003
- `related_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `review_after`: runtime semantics 추가 변동 종료 후

### 보류 이유
- runtime semantics가 아직 움직이는 중이라 stable/final_delivery 문서군을 지금 최종 wording으로 맞추면 다시 수정할 가능성이 높다.

### 현재 위험도
- low

### 지금 허용되는 최소 조치
- boundary note 수준 유지

### 다시 열 조건
- current/raw-only/common-cause surface wording이 더 이상 크게 흔들리지 않을 때

### 예상 복귀 지점
- Gate 7

### 관련 근거
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_NOTE_V1.md)
- [OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_STABLE_RUNTIME_MAPPING_SPEC_V1.md)

## 7. 메모
- 앞으로 메인 라인을 흔드는 질문이 생기면:
  - 먼저 여기 `BR-...`를 연다.
  - 그다음 패치를 시작한다.
  - branch가 잠정 종료되면 `resolved` 또는 `converted_to_parking`으로 갱신한다.
- branch 결론이 잠기면 Gate / decision log 문서와 연결하고, 필요하면 `merged_back`으로 상태를 바꾼다.

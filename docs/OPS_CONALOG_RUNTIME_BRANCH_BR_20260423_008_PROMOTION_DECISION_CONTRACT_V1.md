<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_008_PROMOTION_DECISION_CONTRACT_V1

## [BR-20260423-008] promotion decision contract
- `status`: decision_contract_draft
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-002부터 BR-007까지는 `전조형 고장` 승격 또는 backdating 억제 후보를 바로 production rule로 바꾸지 않고, shadow/audit 근거로 분해했다.
- 그 결과 “근거가 있어 보이는 후보”와 “operator-facing 사건유형을 바꿔도 되는 후보”가 다르다는 점이 확인됐다.
- BR-008의 목적은 다음 패치 전에 판단 기준을 고정해, 매번 같은 후보를 다시 헷갈리지 않게 만드는 것이다.

## 2. 이번 브랜치의 목적
- production code는 수정하지 않는다.
- `retrospective_onset_date`, `사건유형`, `최종고장양상`, final verdict는 변경하지 않는다.
- 기존 BR 산출물을 바탕으로 아래 decision bucket을 정의한다.
  - `promote_candidate`
  - `manual_review`
  - `blocked_cluster_risk`
  - `hold_shadow_only`
  - `backdate_suppression_candidate`
  - `audit_provenance_only`

## 3. 입력 근거
- BR-002: degradation onset fallback G1 shadow guard
  - G1 후보 `7 panels`, 전부 `ktc_ess`
  - 후보 의미: 현재 `전조형 고장`처럼 보이지만 extreme long-gap one-day degradation fallback이라 suppression 후보
- BR-004: secondary warning window shadow audit
  - secondary window candidates `112`
  - `trigger_only_to_precursor` `30`
  - review-required `30`
  - `audit_provenance_only` `62`
  - `audit_no_event_flip` `20`
  - operator-facing change 없는 audit bucket 합계 `82`
- BR-005: trigger-only review packet
  - `review_supported_context` `4`
  - `review_persistent_secondary_only` `26`
  - strict common-cause `2`
  - site-event history `4`
- BR-006: supported-context daily slice
  - manual review `4`
  - auto promotion `0`
  - retained daily-slice nonzero signal `1`
- BR-007: KTC strict-common review
  - strict-common strongest subset `2`
  - auto promotion `0`
  - `hold_shadow_only` `2`
  - retained daily-slice `signal_count_sum=0` `2`

## 4. Decision bucket contract

| bucket | operator-facing change | current count | meaning |
|---|---:|---:|---|
| `promote_candidate` | allowed only after all hard gates pass | 0 | 사건유형 또는 전조일을 바꿀 수 있는 후보 |
| `manual_review` | no | 4 | context는 있으나 자동 승격 근거가 부족한 후보 |
| `blocked_cluster_risk` | no | 26 | persistent secondary만 강하고 cluster false-positive risk가 큰 후보 |
| `hold_shadow_only` | no | 2 | 강한 context가 있어도 raw/audit confirmation이 부족한 후보 |
| `backdate_suppression_candidate` | no in this branch | 7 | current degradation fallback backdating 억제 후보 |
| `audit_provenance_only` | no | 82 | marker provenance 또는 onset date shadow만 기록하는 후보 |

## 5. Promotion hard gates
`trigger_only_to_precursor`를 operator-facing `전조형 고장`으로 승격하려면 아래를 모두 만족해야 한다.

1. `secondary_window_change_class = trigger_only_to_precursor`
2. case-level context가 하나 이상 있어야 한다.
   - `site_event_history_flag = true`
   - 또는 `strict_trigger_proximal_common_cause_flag = true`
   - 또는 `trigger_proximal_common_cause_flag = true`
3. onset 주변 retained daily slice에 독립 신호가 있어야 한다.
   - `signal_count_sum > 0`
   - 또는 `pre_ews_days + ews_warning_days + pre_alarm_days > 0`
4. terminal progression 근거가 있어야 한다.
   - `case_terminal_evidence = true`
   - 또는 `fault_like_days_between_onset_and_strict > 0`
   - 또는 `vdrop_days_between_onset_and_strict > 0`
5. cluster false-positive blocker가 없어야 한다.
   - 같은 root cluster가 `review_persistent_secondary_only`로 대량 묶인 경우는 자동 승격 금지
6. selected onset이 DTW-only 약신호이면 자동 승격 금지
   - 특히 `prealarm_cond_dtw_mid_or_hi`이면서 `signal_count_sum=0`이면 `hold_shadow_only`

## 6. Blocking rules
- `review_persistent_secondary_only`는 자동 승격하지 않는다.
  - BR-005 기준 `gangui` `26 panels`
  - strict common-cause `0`
  - site-event `0`
  - subgroup common-cause `0`
- `strict_common_cause + site_event_history`만으로는 자동 승격하지 않는다.
  - BR-007 기준 `ktc_ess` `2 panels`
  - selected marker가 `prealarm_cond_dtw_mid_or_hi`
  - retained daily slice `signal_count_sum=0`
- terminal evidence만으로 onset 승격을 허용하지 않는다.
  - terminal evidence는 고장 진행 확인이지, onset 날짜의 독립 확인이 아니다.

## 7. 현재 판정
- 현재 evidence 기준 operator-facing `promote_candidate`는 `0`건이다.
- `review_supported_context` `4`건은 계속 `manual_review`이다.
- 그중 `ktc_ess` strict-common `2`건은 더 좁혀도 `hold_shadow_only`이다.
- `gangui` persistent-secondary-only `26`건은 `blocked_cluster_risk`이다.
- BR-002 G1 `7`건은 방향이 다르다.
  - 이는 `급작 고장 -> 전조형 고장` 승격이 아니라, 현재 `전조형 고장` backdating을 억제할지 보는 suppression 후보이다.

## 8. 다음 구현 후보
- 다음 code patch를 한다면 바로 operator-facing 사건유형을 바꾸지 않는다.
- 1순위는 audit/final-review layer에 `promotion_decision_bucket` shadow column을 추가하는 것이다.
- 이 column은 최소 아래 값만 허용한다.
  - `audit_provenance_only`
  - `manual_review`
  - `blocked_cluster_risk`
  - `hold_shadow_only`
  - `backdate_suppression_candidate`
  - `promote_candidate`
- 단, 현재 evidence로는 `promote_candidate=0`이므로 production rerun 후에도 operator-facing flip은 없어야 한다.

## 9. 재현 커맨드
- status 확인:
  - `git status -sb`
- 기존 evidence 요약:
  - `python - <<'PY' ... read BR-005/006/007 csv and print counts ... PY`
- 문서/CSV invariant:
  - `python - <<'PY' ... validate BR-008 decision bucket counts ... PY`
- docs-only sanity compile:
  - `python -m py_compile pv_ae/panel_day_engine.py`

## 10. 복귀 조건
- BR-008 decision bucket이 합의되면 다음 BR은 code shadow column만 추가한다.
- code shadow column 추가 후 fresh tri-site rerun에서 아래를 확인한다.
  - operator-facing final verdict unchanged
  - `promote_candidate = 0`
  - `manual_review`, `blocked_cluster_risk`, `hold_shadow_only`, `backdate_suppression_candidate` counts match expected bands

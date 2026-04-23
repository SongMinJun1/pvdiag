<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_004_SECONDARY_WARNING_WINDOW_SELECTION_V1

## [BR-20260423-004] secondary warning window selection
- `status`: shadow_audit_implemented
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- 현재 onset 로직은 secondary warning 중 가장 이른 날짜 하나를 먼저 본다.
- 그 날짜가 `strict_trigger`보다 너무 이른 경우, 이후 `7~120일` window 안의 secondary warning이 있어도 다시 찾지 않고 `anom_subtype:degradation` fallback 또는 `runtime_trigger_only`로 내려갈 수 있다.
- 이 브랜치는 production onset 판정을 바꾸지 않고, later qualified secondary warning 후보를 audit-only shadow columns로 노출한다.

## 2. 패치 원칙
- `retrospective_onset_date`, `onset_method`, `사건유형`, `최종고장양상`, final verdict는 바꾸지 않는다.
- `trigger_only_to_precursor`는 실제 `급작 고장 -> 전조형 고장` 전환 후보이므로 operator-facing rule로 승격하지 않는다.
- BR-004 정보는 `panel_day_engine_runtime_fault_event_audit_v1.csv`의 shadow columns에만 추가한다.
- source copy와 release package copy는 동일하게 유지한다.

## 3. 추가 audit columns
- `secondary_window_candidate_flag`
- `secondary_window_selected_onset_date`
- `secondary_window_selected_marker`
- `secondary_window_selected_gap_days`
- `secondary_window_qualified_count`
- `secondary_window_too_early_count`
- `secondary_window_change_class`
- `secondary_window_review_tier`
- `secondary_window_reason`
- `common_cause_anchor_date`
- `common_cause_anchor_kind`
- `site_event_history_flag`
- `subgroup_common_cause_history_flag`
- `common_cause_history_flag`
- `strict_trigger_proximal_common_cause_flag`
- `warning_proximal_common_cause_flag`
- `trigger_proximal_common_cause_flag`

## 4. Shadow classification
- `method_provenance_only_primary_marker_mismatch`: 현재 event/onset date는 유지되지만 selected marker provenance가 다르다.
- `degradation_fallback_replaced_by_secondary`: current degradation fallback 전에 qualified secondary warning이 있다.
- `g1_degradation_fallback_replaced_by_secondary`: BR-002 G1 후보가 BR-004 secondary window로 설명된다.
- `trigger_only_to_precursor`: 현재 trigger-only 급작 고장인데 qualified secondary warning이 있어 전조형 전환 후보가 된다. 이 클래스는 review-required로 유지한다.
- `onset_date_shift_without_event_flip`: event type은 유지되지만 candidate onset date가 다르다.

## 5. 검증 결과
- baseline command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br004_head_baseline_check_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- patch command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br004_isolate_shadow_columns_check_v2 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- `py_compile`:
  - `python -m py_compile research/prognostics/runtime_rawonly_chain_common_v1.py research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- clean HEAD baseline 대비 결과:
  - runtime audit: `766 x 32 -> 766 x 49`
  - runtime audit common columns: 동일
  - runtime final verdict: `766 x 37 -> 766 x 37`
  - runtime final verdict common columns: 동일

## 6. Shadow counts
- `secondary_window_candidate_패널수`: `112`
- `secondary_window_trigger_only_to_precursor_패널수`: `30`
- `secondary_window_review_required_패널수`: `30`

## 7. Site x change class
- `conalog` `method_provenance_only_primary_marker_mismatch`: `58`
- `gangui` `degradation_fallback_replaced_by_secondary`: `10`
- `gangui` `trigger_only_to_precursor`: `27`
- `ktc_ess` `degradation_fallback_replaced_by_secondary`: `3`
- `ktc_ess` `g1_degradation_fallback_replaced_by_secondary`: `7`
- `ktc_ess` `method_provenance_only_primary_marker_mismatch`: `4`
- `ktc_ess` `trigger_only_to_precursor`: `3`

## 8. Review tier counts
- `audit_provenance_only`: `62`
- `audit_no_event_flip`: `20`
- `review_supported_context`: `4`
- `review_persistent_secondary_only`: `26`

## 9. 다음 단계
- `trigger_only_to_precursor`는 review-required로 유지한다.
- operator-facing event semantics 변경은 별도 승인 전까지 보류한다.
- BR-002 G1 actual suppression은 BR-004 shadow evidence를 먼저 축적한 뒤 다시 판단한다.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_004_SECONDARY_WARNING_WINDOW_SELECTION_V1

## [BR-20260423-004] secondary warning window selection
- `status`: shadow_audit_implemented
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23
- `target_review_date`: 2026-04-24

## 1. 이슈 요약
- BR-002 G1 shadow guard 검토 중, `degradation fallback` 자체보다 앞선 warning 선택 로직에 더 큰 허점이 발견됐다.
- 현재 onset 로직은 secondary warning 중 가장 이른 날짜 하나를 먼저 보고, 그 warning이 `strict_trigger`보다 `120일`을 초과해 너무 이르면 later qualified secondary warning을 다시 보지 않는다.
- 그 결과, `strict_trigger` 기준 `7~120일` 안에 들어오는 secondary warning이 있어도 `anom_subtype:degradation` fallback 또는 `runtime_trigger_only`로 내려갈 수 있다.

## 2. 왜 브랜치인가
- 이 수정은 단순 audit column 추가가 아니라 `retrospective_onset_date`, `onset_method`, `전조흔적_flag`, `사건유형`까지 바꿀 수 있다.
- 특히 `gangui`에서 `runtime_trigger_only -> secondary warning 기반 전조형` 전환 후보가 다수라서, 바로 rule patch로 가면 급작/전조 분포가 크게 흔들릴 수 있다.

## 3. 현재 근거
- `/private/tmp/br002_qualified_warning_recheck/` 기준:
  - G1 hit `7건` 전부가 later qualified secondary warning을 가진다.
  - 따라서 G1 hit 전체를 “degradation fallback 과민”으로만 해석하면 안 된다.
- `/private/tmp/br002_secondary_window_selection_evidence/` 기준:
  - total candidate panels: `45`
  - `gangui`: `36`
    - current `anom_subtype:degradation`: `10`
    - current `runtime_trigger_only`: `26`
  - `ktc_ess`: `9`
    - current `anom_subtype:degradation`: `6`
    - current `runtime_trigger_only`: `3`
- 이 후보들은 모두 “첫 secondary warning은 너무 이르지만, 이후 7~120일 window 안의 secondary warning이 존재”하는 패널이다.

## 4. BR-004 shadow/counterfactual 결과
- 산출물 위치: `/private/tmp/br004_secondary_window_shadow_evidence/`
- counterfactual rule:
  - primary warning precedence는 유지한다.
  - accepted primary warning이 없으면, secondary warning 전체 중 `strict_trigger` 기준 `7~120일` window에 들어오는 첫 날짜를 선택한다.
  - qualified secondary warning이 없을 때만 `anom_subtype:degradation` fallback으로 내려간다.
- headline:
  - BR-004 candidate panels: `50`
  - changed panels any: `112`
  - event-type changed panels: `30`
  - current G1 hits: `7`
  - BR-004 counterfactual 이후 G1 hits: `0`
- site별 변화:
  - `conalog`: candidate `0`, changed `58`, event-type flip `0`
  - `gangui`: candidate `37`, changed `37`, event-type flip `27`
  - `ktc_ess`: candidate `13`, changed `17`, event-type flip `3`
- change class:
  - `conalog` `58건`은 `method_provenance_only_primary_marker_mismatch`이다.
    - 실제 onset date는 그대로인데, current `onset_method=ews_warning`이 selected onset date를 만든 secondary marker와 불일치한다.
    - 따라서 event-type 변경 리스크가 아니라 provenance/audit consistency 이슈로 분리한다.
  - `gangui` `27건`과 `ktc_ess` `3건`은 `trigger_only_to_precursor`이다.
    - 이 클래스는 `급작 고장 -> 전조형 고장` 전환을 만들기 때문에 operator-facing rule로 즉시 승격하면 위험하다.
  - `ktc_ess` G1 hit `7건`은 `g1_degradation_fallback_replaced_by_secondary`이다.
    - direct G1 suppression보다 BR-004가 먼저 필요한 핵심 근거다.

## 5. `trigger_only_to_precursor` false-positive risk review
- 산출물 위치: `/private/tmp/br004_trigger_only_to_precursor_risk_review/`
- 대상:
  - `change_class == trigger_only_to_precursor`
  - 총 `30건`
  - `gangui` `27건`
  - `ktc_ess` `3건`
- review tier:
  - `ktc_ess` `3건`: `review_supported_context`
    - 전부 site-event history를 가진다.
    - 그중 `2건`은 strict-trigger proximal common-cause도 겹친다.
  - `gangui` `1건`: `review_supported_context`
    - site-event history를 가진다.
  - `gangui` `26건`: `review_persistent_secondary_only`
    - strict/subgroup/site common-cause overlap은 없다.
    - 하지만 단발 신호가 아니라 두 panel-root cluster에 집중된다.
    - `bf1a912f-6cf0-4f12-8e97-9d9d86576511`: `20건`
    - `4fd0c566-e25e-4d51-96ca-57cc46940593`: `7건`
    - 평균 qualified secondary warning count는 각각 `94.3`, `100.0`이다.
- 판단:
  - `ktc_ess`는 문맥 지지가 비교적 강하다.
  - `gangui`는 무시할 신호는 아니지만, operator-facing `급작 -> 전조` 전환으로 바로 승격하기에는 common-cause 근거가 약하다.
  - 따라서 BR-004의 다음 구현은 actual event semantics 변경이 아니라, `secondary_window_selected_onset` 계열 shadow/audit column + review-required 노출이 안전하다.

## 6. 지금 허용되는 것
- audit-only counterfactual 생성
- candidate panel별 later qualified warning 날짜 확인
- `first secondary overall` vs `first qualifying secondary within window` 비교
- gangui 급작 전환 후보의 common-cause / cluster 문맥 확인

## 7. 지금 금지되는 것
- 즉시 production onset 로직 변경
- G1 actual suppression rule 승격
- `runtime_trigger_only -> 전조형 고장` 전환을 operator-facing 확정으로 해석

## 8. 잠정 판단
- BR-002의 G1은 여전히 유효한 shadow flag지만, 실제 suppression rule로 올리기 전에 BR-004를 먼저 봐야 한다.
- 현재 더 안전한 다음 patch 후보는:
  - **secondary warning 후보 중 strict trigger 기준 허용 window 안에 들어오는 첫 날짜를 선택하고, 그 이후에도 없을 때만 degradation fallback을 사용한다**.
- 단, 이 후보는 `gangui` 급작 고장 다수를 전조형으로 바꿀 수 있으므로, production patch 전에 `trigger_only_to_precursor` 30건을 별도 false-positive risk review로 묶어야 한다.
- 구현 순서는 `method/provenance consistency`와 `event-type changing onset selection`을 분리하는 편이 안전하다.
- 2026-04-23 false-positive risk review 이후 잠정 구현 후보:
  - 1차: shadow/audit column으로 `secondary_window_selected_onset`, `secondary_window_selected_marker`, `secondary_window_change_class`, `secondary_window_review_tier`를 노출한다.
  - 2차: `trigger_only_to_precursor`는 review-required로 유지하고, operator-facing 사건유형은 바로 바꾸지 않는다.

## 9. shadow/audit column patch 결과
- patch scope:
  - `research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
  - `release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- 추가 audit columns:
  - `secondary_window_candidate_flag`
  - `secondary_window_selected_onset_date`
  - `secondary_window_selected_marker`
  - `secondary_window_selected_gap_days`
  - `secondary_window_qualified_count`
  - `secondary_window_too_early_count`
  - `secondary_window_change_class`
  - `secondary_window_review_tier`
  - `secondary_window_reason`
- validation command:
  - `python -m py_compile research/prognostics/runtime_rawonly_chain_common_v1.py research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br004_shadow_columns_check --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- validation result:
  - raw-only audit: 기존 공통 columns 동일
  - raw-only final verdict: 기존 columns 전체 동일
  - audit shape: `766 x 40 -> 766 x 49`
  - final verdict shape: `766 x 37 -> 766 x 37`
- shadow class counts:
  - `conalog` `method_provenance_only_primary_marker_mismatch`: `58`
  - `gangui` `degradation_fallback_replaced_by_secondary`: `10`
  - `gangui` `trigger_only_to_precursor`: `27`
  - `ktc_ess` `degradation_fallback_replaced_by_secondary`: `3`
  - `ktc_ess` `g1_degradation_fallback_replaced_by_secondary`: `7`
  - `ktc_ess` `method_provenance_only_primary_marker_mismatch`: `4`
  - `ktc_ess` `trigger_only_to_precursor`: `3`
- summary counts:
  - `secondary_window_candidate_패널수`: `112`
  - `secondary_window_trigger_only_to_precursor_패널수`: `30`
  - `secondary_window_review_required_패널수`: `30`
- 산출물:
  - `/private/tmp/br004_shadow_columns_check/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
  - `/private/tmp/br004_shadow_columns_check/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_summary_v1.csv`
  - `/private/tmp/br004_shadow_columns_check/raw_only_chain_workspace/_share/panel_day_engine_runtime_final_verdict_v1.csv`

## 10. 복귀 조건
- tri-site 기준 BR-004 counterfactual 변화량 확보: 완료
- gangui `runtime_trigger_only -> 전조형` 후보의 false-positive 위험 검토: 완료
- G1 suppression 후보를 BR-004 적용 후 다시 재계산: 완료, `7 -> 0`
- shadow/audit column patch 후보 작성: 완료
- operator-facing event semantics 변경 여부는 별도 승인 전까지 보류

## 11. 관련 문서/결정
- [OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_002_DEGRADATION_ONSET_FALLBACK_GUARD_V1.md)
- [OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md)
- [OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md](/Users/b9gc/pvdiag/docs/OPS_CONALOG_RUNTIME_GATE3_PRECURSOR_PROMOTION_RULE_V1.md)

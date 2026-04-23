<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_013_G1_SUPPRESSED_EVENT_SHADOW_COLUMNS_V1

## [BR-20260423-013] G1 suppressed-event shadow columns
- `status`: shadow_audit_implemented
- `branch_type`: B
- `current_gate`: Gate 3
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-012는 G1 suppression을 표로만 simulation했다.
- BR-013은 같은 판단을 runtime fault-event audit에 shadow columns로 구현한다.
- production verdict와 operator-facing event semantics는 변경하지 않는다.

## 2. 구현 범위
- changed code:
  - `research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
  - `release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py`
  - `release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- untouched:
  - `pv_ae/panel_day_engine.py`
  - runtime final verdict semantics
  - operator-facing 사건유형 output

## 3. 추가 audit columns
- `g1_suppressed_event_shadow_flag`
- `g1_suppressed_event_shadow_rule_name`
- `g1_suppressed_event_shadow_current_onset_date`
- `g1_suppressed_event_shadow_strict_trigger_date`
- `g1_suppressed_event_shadow_current_event_type_ko`
- `g1_suppressed_event_shadow_current_final_pattern_ko`
- `g1_suppressed_event_shadow_event_type_if_applied_ko`
- `g1_suppressed_event_shadow_final_pattern_if_applied_ko`
- `g1_suppressed_event_shadow_transition_class`
- `g1_suppressed_event_shadow_reason`

## 4. Summary columns
- `g1_suppressed_event_shadow_candidate_패널수`
- `g1_suppressed_event_shadow_precursor_to_sudden_패널수`

## 5. Fresh tri-site validation
- baseline command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br013_baseline_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- patched command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br013_patched_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- local validation:
  - `/private/tmp/br013_g1_suppressed_event_shadow_validation_v1/br013_validation_summary_v1.json`

## 6. 핵심 결과
| check | result |
|---|---|
| baseline audit shape | `766 x 51` |
| patched audit shape | `766 x 61` |
| new audit columns | `10` |
| missing audit columns | `0` |
| audit common columns equal | `true` |
| baseline final verdict shape | `766 x 37` |
| patched final verdict shape | `766 x 37` |
| final verdict common columns equal | `true` |
| final verdict full table equal | `true` |
| G1 shadow rows | `7` |
| G1 shadow transition | `전조형 고장 -> 급작 고장 = 7` |
| G1 shadow site | `ktc_ess = 7` |
| strict-proximal common-cause overlap | `6 / 7` |
| site-event overlap | `7 / 7` |
| subgroup overlap | `5 / 7` |

## 7. 판단
- BR-013은 원하는 안전 조건을 만족했다.
- audit에는 G1 suppressed-event interpretation이 추가되지만, 기존 audit 공통 컬럼은 변하지 않는다.
- final verdict는 전체 table equality가 성립하므로 operator-facing output은 변하지 않는다.
- 따라서 다음 단계에서 논의할 수 있는 것은 “운영 의미 변경”이 아니라 “shadow 결과를 reviewer가 승인할지”다.

## 8. Decision lock
- G1 shadow rows는 7건으로 고정한다.
- `gangui` short-gap plausible / blocked cluster set은 변경하지 않는다.
- final verdict 변경은 이번 branch 범위 밖이다.
- operator-facing `전조형 고장 -> 급작 고장` 전환은 별도 승인 branch에서만 다룬다.

## 9. 추가 검증
- command:
  - `python -m py_compile pv_ae/panel_day_engine.py research/prognostics/runtime_rawonly_chain_common_v1.py research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/runtime_rawonly_chain_common_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- command:
  - `git diff --check`

## 10. 다음 단계
- BR-013을 merge한 뒤에는 G1 shadow 결과를 사람이 승인할지 정한다.
- 승인 전에는 final verdict나 operator-facing table을 바꾸지 않는다.
- 승인한다면 별도 BR에서 final verdict semantic diff를 먼저 preview-only로 만들고, 그 다음 production 변경 여부를 결정한다.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_V1

## [BR-20260423-019] Fault subtype hypothesis shadow columns
- `status`: subtype_shadow_columns_validated
- `branch_type`: B
- `current_gate`: Gate 7
- `return_gate`: Gate 7
- `owner`: Codex + 사용자
- `created_at`: 2026-04-23

## 1. 이슈 요약
- BR-018에서 세부 고장명은 운영 확정 라벨이 아니라 `hypothesis`로 시작한다고 잠갔다.
- BR-019는 그 hypothesis를 runtime fault-event audit에 shadow column으로만 붙인다.
- 목적은 전조/급작 판정을 바꾸는 것이 아니라, "이 신호가 어떤 세부 고장 양상처럼 생겼는가"를 근거와 함께 보이게 하는 것이다.

## 2. Scope guard
- `pv_ae/panel_day_engine.py`는 수정하지 않는다.
- runtime final verdict와 cause heuristic 결과는 바꾸지 않는다.
- subtype column은 operator-facing label이 아니다.
- `subtype_production_write_allowed`는 모든 row에서 `0`이다.
- common-cause evidence는 subtype shape를 덮어쓰기보다 `subtype_hold_reason_ko`와 `subtype_evidence_tags`에 남긴다.

## 3. Added shadow columns
| column | meaning |
|---|---|
| `fault_family_hypothesis_shadow_ko` | 고장 계열 가설 |
| `fault_subtype_hypothesis_shadow_ko` | 계열 안의 세부 고장 가설 |
| `subtype_evidence_tags` | subtype 근거 태그 |
| `subtype_confidence_shadow` | subtype confidence; BR-019에서는 모두 `hold` |
| `subtype_hold_reason_ko` | operator-facing 승격을 막는 이유 |
| `subtype_production_write_allowed` | always `0` |

## 4. Classification policy
- G1 suppressed-event rows are handled first as `장기 gap 단일 저하 보류형`.
- Diode/vdrop shape is preserved as `bypass diode 동작·고장 의심형`.
- `algorithm_family_ko = 개방/장치이상형` is preserved as open-connection subtype before degradation/shadow fallback.
- Module/degradation/shadow evidence maps to degradation/soiling/shading subtype.
- common-cause evidence does not erase the subtype shape; it forces `hold` and is recorded in tags/reason.
- fallback external/common-cause subtype is used only when no stronger shape subtype exists.

## 5. Fresh tri-site evidence
- run root:
  - `/private/tmp/br019_tri_site_v3`
- raw-only audit:
  - `/private/tmp/br019_tri_site_v3/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- raw-only final verdict:
  - `/private/tmp/br019_tri_site_v3/raw_only_chain_workspace/_share/panel_day_engine_runtime_final_verdict_v1.csv`
- raw-only heuristic:
  - `/private/tmp/br019_tri_site_v3/raw_only_chain_workspace/_share/panel_day_engine_runtime_cause_candidate_heuristics_v1.csv`

## 6. Results
- audit rows: `766`
- audit columns: `69`
- subtype shadow populated rows: `145`
- subtype production write allowed sum: `0`
- subtype confidence:
  - `hold`: `145`
  - `low`: `0`
  - `medium`: `0`
  - `high`: `0`

## 7. Subtype distribution
| family | subtype | confidence | panel_count |
|---|---|---|---:|
| `접속 불량·부분 개방 계열` | `간헐 접촉저항형` | `hold` | 88 |
| `다이오드·서브스트링 계열` | `bypass diode 동작·고장 의심형` | `hold` | 25 |
| `외부계통·공통원인 계열` | `site-wide grid/inverter 교란형` | `hold` | 11 |
| `열화·오염·음영 계열` | `누적 오염·열화형` | `hold` | 10 |
| `열화·오염·음영 계열` | `장기 gap 단일 저하 보류형` | `hold` | 7 |
| `열화·오염·음영 계열` | `일시 환경 episode형` | `hold` | 2 |
| `접속 불량·부분 개방 계열` | `부분 개방 진행형` | `hold` | 2 |

## 8. Behavior validation
- BR-017 audit common columns equal: `true`
- BR-017 raw-only final verdict equal: `true`
- BR-017 raw-only cause heuristic equal: `true`
- engine core shadow compare all matched: `true`

## 9. Evidence outputs
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_SITE_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_VALIDATION_V1.json`

## 10. Reproduction
- before command:
  - `git status -sb`
- fresh tri-site command:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br019_tri_site_v3 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`
- validation command:
  - `python -m py_compile research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py pv_ae/panel_day_engine.py`

## 11. Decision
- BR-019 is safe as an audit/evidence schema expansion.
- It materially improves completeness because subtype shape is now visible for all 145 raw-only fault panels.
- It remains conservative because every subtype hypothesis is `hold` and production write allowed is `0`.
- Next step should review whether common-cause hold can be decomposed into separate `shape_confidence` and `promotion_blocker` fields before any confidence is raised.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_021_SHAPE_CONFIDENCE_BLOCKER_SPLIT_V1

## Purpose
- BR-019의 `subtype_confidence_shadow`는 세부고장 형태가 그럴듯한지와 운영 승격을 막는 이유를 한 값에 섞고 있었다.
- BR-021은 이 둘을 분리해, "형태 검토"와 "승격 차단"을 별도 audit 축으로 남긴다.
- 이 변경은 runtime fault-event audit의 shadow/evidence schema만 확장하며, production verdict semantics는 바꾸지 않는다.

## Scope
- 추가 audit columns:
  - `subtype_shape_confidence_shadow`
  - `subtype_promotion_blocker_shadow`
  - `subtype_promotion_blocker_reason_ko`
- 기존 `subtype_confidence_shadow`는 backward compatibility를 위해 그대로 유지한다.
- `subtype_production_write_allowed`는 계속 `0`으로 고정한다.

## Reproduction Commands
- pre-patch hygiene:
  - `python -m py_compile research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- post-patch fresh tri-site:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br021_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`

## Evidence Artifacts
- fresh tri-site root: `/private/tmp/br021_tri_site_v1`
- runtime audit: `/private/tmp/br021_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- validation json: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_021_VALIDATION_V1.json`
- shape summary: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_021_SHAPE_CONFIDENCE_SUMMARY_V1.csv`
- blocker summary: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_021_PROMOTION_BLOCKER_SUMMARY_V1.csv`

## Results
| metric | value |
|---|---:|
| audit rows | 766 |
| audit columns | 72 |
| subtype shadow populated rows | 145 |
| `subtype_production_write_allowed_sum` | 0 |
| shape confidence medium | 136 |
| shape confidence low | 9 |
| promotion blocker common_cause | 138 |
| promotion blocker backdating_risk | 7 |
| legacy `subtype_confidence_shadow=hold` | 145 |

## Stability Checks
| check | result |
|---|---|
| BR-019 old audit common columns equal | true |
| old audit common column count | 69 |
| raw-only final verdict equal to BR-019 | true |
| raw-only heuristic equal to BR-019 | true |
| engine core shadow compare all match | true |

## Interpretation
- `subtype_confidence_shadow`가 모두 `hold`였던 이유는 세부 형태가 전부 약해서가 아니라, 대부분이 common-cause promotion blocker에 묶여 있었기 때문이다.
- 새 축 기준으로는 145개 중 136개가 형태상 `medium`이다. 단, 이 값은 operator-facing 승격 가능성을 뜻하지 않는다.
- 138개는 `common_cause` blocker로 묶였고, 7개는 BR-002/BR-018 계열의 long-gap one-day degradation backdating risk로 묶였다.
- 즉 "형태 가설은 볼 만하지만, 아직 개별 패널 전조/세부고장으로 올리면 위험하다"가 이번 evidence의 핵심 결론이다.

## Decision
- BR-021은 merge 가능한 audit/schema refinement다.
- production output, final verdict, heuristic rank는 변경하지 않는다.
- 다음 단계는 `common_cause` blocker 내부를 site-wide, strict-proximal, subgroup/root로 더 잘게 나누는 shadow-only BR로 진행한다.

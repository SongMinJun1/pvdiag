<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_022_COMMON_CAUSE_BLOCKER_DETAIL_V1

## Purpose
- BR-021 split subtype shape confidence from the broad promotion blocker.
- BR-022 keeps the broad `subtype_promotion_blocker_shadow` value stable, but adds a more specific detail axis so `common_cause` no longer hides several different reasons.
- This is still audit/shadow only. It does not change final verdict, cause heuristic, or operator-facing semantics.

## Scope
- Added audit columns:
  - `group_off_history_flag`
  - `subtype_promotion_blocker_detail_shadow`
- Kept BR-021 common columns byte-equivalent by table value:
  - existing `subtype_promotion_blocker_shadow`
  - existing `subtype_promotion_blocker_reason_ko`
  - existing subtype tags/confidence columns
- Kept `subtype_production_write_allowed = 0`.

## Detail Buckets
| detail bucket | meaning |
|---|---|
| `site_event` | site-level event evidence is present and takes priority as the blocker detail |
| `strict_trigger_proximal` | strict trigger is near a common-cause anchor without site-event priority |
| `subgroup_common_cause` | root/subgroup common-cause evidence is present without stronger site/strict priority |
| `group_off` | group-off evidence explains the broad common-cause blocker |
| `backdating_risk` | G1 long-gap one-day degradation backdating risk |

## Reproduction Commands
- pre-patch hygiene:
  - `python -m py_compile research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py release/conalog_full_runtime_v1/package/research/prognostics/build_panel_day_engine_runtime_fault_event_audit_v1.py`
- post-patch fresh tri-site:
  - `python release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/br022_tri_site_v1 --sites conalog,gangui,ktc_ess --reuse-existing-site-outs-root /Users/b9gc/pvdiag/data`

## Evidence Artifacts
- fresh tri-site root: `/private/tmp/br022_tri_site_v1`
- runtime audit: `/private/tmp/br022_tri_site_v1/raw_only_chain_workspace/_share/panel_day_engine_runtime_fault_event_audit_v1.csv`
- validation json: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_022_VALIDATION_V1.json`
- detail summary: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_022_COMMON_CAUSE_BLOCKER_DETAIL_SUMMARY_V1.csv`
- site summary: `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_022_COMMON_CAUSE_BLOCKER_SITE_SUMMARY_V1.csv`

## Results
| metric | value |
|---|---:|
| audit rows | 766 |
| audit columns | 74 |
| subtype shadow populated rows | 145 |
| `subtype_production_write_allowed_sum` | 0 |
| blocker `common_cause` | 138 |
| detail `site_event` | 60 |
| detail `strict_trigger_proximal` | 49 |
| detail `group_off` | 28 |
| detail `subgroup_common_cause` | 1 |
| detail `backdating_risk` | 7 |

## Stability Checks
| check | result |
|---|---|
| BR-021 old audit common columns equal | true |
| old audit common column count | 72 |
| raw-only final verdict equal to BR-021 | true |
| raw-only heuristic equal to BR-021 | true |
| engine core shadow compare all match | true |

## Interpretation
- BR-021의 `common_cause=138`은 하나의 원인이 아니라 네 가지 blocker detail로 분리된다.
- 가장 큰 축은 `site_event=60`이고, 그다음은 `strict_trigger_proximal=49`, `group_off=28`, `subgroup_common_cause=1`이다.
- `gangui`에는 `group_off=28`이 크게 존재한다. 이는 기존 blocked-cluster 계열을 다시 볼 때 site-level event가 아니라 group-level episode로 분리해야 함을 시사한다.
- `conalog`는 `site_event=34`, `strict_trigger_proximal=38`로 갈라진다. 같은 `common_cause`라도 site event와 strict-proximal evidence를 같은 방식으로 판단하면 안 된다.
- `ktc_ess`는 `site_event=21`과 별도 `backdating_risk=7`이 같이 존재한다. backdating guard 판단은 여전히 공통원인 판단과 분리해야 한다.

## Decision
- BR-022 is safe to merge as an evidence-layer blocker-detail refinement.
- No subtype promotion is allowed by this branch.
- Next safe step is to generate a review packet for `group_off` and `strict_trigger_proximal` blocker details before any subtype promotion discussion.

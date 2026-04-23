<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## Purpose
- runtime rule work is split into small branches so evidence does not get mixed with production semantics.
- this register records the current decision path and prevents re-opening the same question without new evidence.

## Current Branch
| branch | status | scope | next decision |
|---|---|---|---|
| `BR-20260423-012` | `shadow_simulation_generated` | G1 backdate suppression before/after simulation for ktc_ess 7 rows | decide whether to implement suppressed-event shadow columns in audit only |

## Completed Runtime Branches
| branch | status | key result | operator-facing change |
|---|---|---|---|
| `BR-20260423-002` | `merged_shadow_audit` | G1 extreme long-gap degradation fallback guard marks 7 ktc_ess backdating-suppression candidates | no |
| `BR-20260423-004` | `merged_shadow_audit` | secondary warning window audit exposes 112 candidates and 30 trigger-only-to-precursor review cases | no |
| `BR-20260423-005` | `merged_review_packet` | trigger-only candidates split into 4 supported-context and 26 persistent-secondary-only cluster-risk cases | no |
| `BR-20260423-006` | `merged_review_packet` | supported-context daily slice keeps all 4 as manual review and auto promotion 0 | no |
| `BR-20260423-007` | `merged_review_packet` | ktc_ess strict-common strongest 2 cases remain hold_shadow_only | no |
| `BR-20260423-008` | `merged_decision_contract` | promotion/backdating decision buckets fixed before code shadowing | no |
| `BR-20260423-009` | `shadow_audit_implemented` | audit adds `promotion_decision_bucket` and keeps `promote_candidate=0` | no |
| `BR-20260423-010` | `review_packet_generated` | bucket packet gives 112 non-empty rows and 37 action-queue rows | no |
| `BR-20260423-011` | `deep_packet_generated` | gangui blocked_cluster_risk 26 rows collapse to 2 roots with no site/subgroup/strict-proximal support | no |
| `BR-20260423-012` | `shadow_simulation_generated` | G1 suppression simulation maps ktc_ess 7 rows from current 전조형 고장 to shadow 급작 고장 with no code change | no |

## Decision Locks
- `trigger_only_to_precursor` is never promoted directly from secondary-window persistence alone.
- `strict_common_cause + site_event_history` is not enough for automatic promotion when retained daily signal is zero.
- `gangui` persistent-secondary cluster cases stay blocked until cluster false-positive risk is resolved.
- BR-002 G1 is a backdating suppression path, not a precursor promotion path.
- Current evidence has `promote_candidate = 0`.
- BR-009 buckets are exclusive: `manual_review=2`, `hold_shadow_only=2`, `blocked_cluster_risk=26`, `backdate_suppression_candidate=7`, `audit_provenance_only=75`.
- BR-010 action queue excludes provenance-only rows: `37` rows remain for review.
- BR-011 closes `blocked_cluster_risk=26` as `blocked_counterexample_hold`: all rows are `gangui`, 2 roots, selected gaps 115-120 days, site/subgroup/strict-proximal support 0.
- BR-012 keeps `backdate_suppression_candidate=7` as shadow-only: if G1 is applied, all 7 become `전조형 고장 -> 급작 고장` simulation rows, but production semantics stay unchanged.

## Next Safe Implementation
- keep `promotion_decision_bucket` as an audit/shadow field only.
- use bucket-specific review packets before proposing any operator-facing event semantic change.
- next branch may implement G1 suppressed-event shadow columns in runtime audit only, followed by fresh tri-site rerun and final-verdict invariant checks.
- only after reviewer confirmation consider a separate operator-facing rule proposal.

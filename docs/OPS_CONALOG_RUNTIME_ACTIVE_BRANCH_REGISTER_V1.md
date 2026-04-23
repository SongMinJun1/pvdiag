<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## Purpose
- runtime rule work is split into small branches so evidence does not get mixed with production semantics.
- this register records the current decision path and prevents re-opening the same question without new evidence.

## Current Branch
| branch | status | scope | next decision |
|---|---|---|---|
| `BR-20260423-008` | `decision_contract_draft` | promotion/backdating decision buckets only | if accepted, implement shadow `promotion_decision_bucket` column before any operator-facing rule change |

## Completed Runtime Branches
| branch | status | key result | operator-facing change |
|---|---|---|---|
| `BR-20260423-002` | `merged_shadow_audit` | G1 extreme long-gap degradation fallback guard marks 7 ktc_ess backdating-suppression candidates | no |
| `BR-20260423-004` | `merged_shadow_audit` | secondary warning window audit exposes 112 candidates and 30 trigger-only-to-precursor review cases | no |
| `BR-20260423-005` | `merged_review_packet` | trigger-only candidates split into 4 supported-context and 26 persistent-secondary-only cluster-risk cases | no |
| `BR-20260423-006` | `merged_review_packet` | supported-context daily slice keeps all 4 as manual review and auto promotion 0 | no |
| `BR-20260423-007` | `merged_review_packet` | ktc_ess strict-common strongest 2 cases remain hold_shadow_only | no |

## Decision Locks
- `trigger_only_to_precursor` is never promoted directly from secondary-window persistence alone.
- `strict_common_cause + site_event_history` is not enough for automatic promotion when retained daily signal is zero.
- `gangui` persistent-secondary cluster cases stay blocked until cluster false-positive risk is resolved.
- BR-002 G1 is a backdating suppression path, not a precursor promotion path.
- Current evidence has `promote_candidate = 0`.

## Next Safe Implementation
- add `promotion_decision_bucket` as an audit/shadow field only.
- rerun tri-site and prove final verdict/event semantics are unchanged.
- only after that consider a separate operator-facing rule proposal.

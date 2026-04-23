<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1

## Purpose
- runtime rule work is split into small branches so evidence does not get mixed with production semantics.
- this register records the current decision path and prevents re-opening the same question without new evidence.

## Current Branch
| branch | status | scope | next decision |
|---|---|---|---|
| `BR-20260423-019` | `subtype_shadow_columns_validated` | runtime fault-event audit emits subtype hypothesis shadow columns for 145 raw-only fault panels | review shape confidence vs promotion blocker separation |

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
| `BR-20260423-013` | `shadow_audit_implemented` | audit adds 10 G1 suppressed-event shadow columns; final verdict remains byte-equivalent by table value | no |
| `BR-20260423-014` | `semantic_preview_generated` | preview shows 7 ktc_ess rows would change 13 operator-facing columns and 91 cells; no production output written | no |
| `BR-20260423-015` | `apply_ready_sidecar_generated` | strict-proximal support splits G1 preview into 6 apply-ready rows and 1 hold-review row | no |
| `BR-20260423-016` | `semantic_patch_validated` | applies G1 semantics to 6 strict-proximal rows; runtime final verdict changes 6 rows/14 columns/84 cells; cause top ranks unchanged | yes, raw-only candidate runtime semantics only |
| `BR-20260423-017` | `morphology_atlas_shadow_generated` | atlas 6 families, threshold candidates 6 axes, shadow rows 145; G1 6 rows blocked as long-gap one-day episodes | no |
| `BR-20260423-018` | `subtype_hypothesis_roadmap_locked` | locks 17 subtype hypotheses under 6 family buckets; next implementation must be shadow-only subtype evidence columns | no |
| `BR-20260423-019` | `subtype_shadow_columns_validated` | adds 6 subtype hypothesis shadow columns to runtime fault-event audit; 145 populated, production write sum 0, final verdict/heuristic unchanged | no |

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
- BR-013 implements the same G1 result as audit shadow columns only: audit common columns equal `true`, final verdict full table equal `true`, G1 shadow rows `7`.
- BR-014 previews operator-facing impact only: 7 ktc_ess rows, 13 columns, 91 cells, production output written `0`; 1 row lacks strict-proximal common-cause support.
- BR-015 reduces first-patch scope to strict-proximal-supported rows only: apply-ready `6`, hold-review `1`, production output written `0`.
- BR-016 applies only those 6 rows and keeps the hold row excluded. Runtime final verdict changes `6` rows, `14` columns, `84` cells; the extra column beyond BR-015 is derived `대표판정_ko`.
- BR-016 blocks unintended cause-candidate rank drift: top1/top2/top3 cause rank drift rows `0`; published strict current output changed rows `0`.
- BR-017 is atlas/shadow only: `production_write_allowed_sum = 0`.
- BR-017 G1 episode basis uses `g1_suppressed_event_shadow_current_onset_date`, because BR-016-applied rows no longer carry current `retrospective_onset_date`.
- BR-017 v1 thresholds produce confirmed precursor candidates `0`; this is a conservative starting point, not a final rule.
- BR-018 locks subtype names as `hypothesis`, not operator-facing final labels.
- BR-018 requires subtype evidence to be defended by at least two axes before any promotion discussion: examples are duration+continuity, recurrence+VI-shape, or spatiality+fast-recovery.
- BR-018 keeps sensor/measurement and external/common-cause subtype paths out of individual panel precursor promotion.
- BR-019 appends subtype hypothesis columns to the audit/evidence layer only; `subtype_production_write_allowed_sum = 0`.
- BR-019 keeps old audit common columns, raw-only final verdict, and raw-only heuristic equal to BR-017.
- BR-019 records subtype shape first and common-cause as a hold reason/tag, so subtype review can proceed without operator-facing promotion.

## Next Safe Implementation
- keep `promotion_decision_bucket` as an audit/shadow field only.
- use bucket-specific review packets before proposing any operator-facing event semantic change.
- before any new production semantic patch, keep duration/gap/continuity/spatiality separated by fault-family threshold candidates.
- split `subtype_confidence_shadow` into shape confidence and promotion blocker only after reviewing BR-019 hold cases.
- keep `subtype_production_write_allowed = 0` until a fresh tri-site review proves a subtype can be raised without final verdict drift.

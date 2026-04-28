<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_043_V1

## Decision
- Accept BR-061 `result_delta_scorecard` as the answer format for "how much did the result change?" before and after future engine patches.
- Keep accuracy/F1 improvement claims blocked until a truth-label evaluation is explicitly run.
- Use `core_result_delta_0` as the current stable baseline claim.

## Reason
- The recent BR-025 through BR-060 work mostly improved evidence separation, blocker handling, and prepatch safety.
- That work should not be described as detector-performance improvement when the core runtime result did not change.
- A scorecard prevents two common mistakes:
  - mistaking safety/evidence improvements for accuracy gains,
  - mistaking raw-only candidate counts for validated operator-facing performance.

## Evidence
- `/private/tmp/panel_engine_result_delta_scorecard_check` reports:
  - `overall_status = pass`
  - `core_all_compared_sites_match = 1`
  - `core_total_diff_count = 0`
  - `raw_only_candidate_row_count = 72`
  - `published_current_row_count = 72`
  - `precursor_candidate_row_count = 0`
  - `raw_only_fault_signal_row_count = 72`
  - `proximal_common_cause_fault_signal_count = 64`
  - `proximal_common_cause_fault_signal_ratio = 0.888889`
  - `performance_improvement_claim_allowed = no_truth_label_not_claimed`
  - `result_change_claim_ko = core_result_delta_0`

## Consequence
- The correct current answer is:
  - result change: `0` at core level,
  - candidate context: visible and quantified,
  - performance improvement: not claimed.
- Future algorithm patches must beat this baseline with a post-patch scorecard plus truth/evaluation evidence before performance improvement wording is allowed.

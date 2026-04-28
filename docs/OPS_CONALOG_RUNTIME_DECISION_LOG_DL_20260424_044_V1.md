<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_044_V1

## Decision
- Accept BR-062 `result_delta_scorecard_compare` as the required before/after comparator for future direct engine patch claims.
- Keep performance-improvement wording blocked unless a truth-label evaluation is provided in addition to the scorecard compare.
- Treat result deltas as review signals, not automatic improvements.

## Reason
- BR-061 created the baseline scorecard, but a single baseline still leaves before/after comparison to manual interpretation.
- BR-062 makes the comparison executable and reproducible.
- This prevents two subtle mistakes:
  - claiming improvement from candidate-count movement alone,
  - hiding core-result drift inside a large report rerun.

## Evidence
- `/private/tmp/panel_engine_result_delta_scorecard_compare_check` reports for BR-061 baseline vs fresh conalog rerun scorecard:
  - `overall_status = pass`
  - `metric_count = 19`
  - `changed_metric_count = 0`
  - `core_result_changed_flag = 0`
  - `raw_only_candidate_row_count_delta = 0`
  - `precursor_candidate_row_count_delta = 0`
  - `fault_panel_count_delta = 0`
  - `performance_improvement_claim_allowed = not_allowed_without_truth_label_eval`
  - `result_change_summary_ko = no_result_change_detected`

## Consequence
- Future patch review order is now:
  - run BR-060 prepatch runbook,
  - generate BR-061 baseline/post scorecards,
  - run BR-062 scorecard compare,
  - only then discuss whether a result change is acceptable.
- Accuracy/F1 improvement remains out of scope until truth-label evaluation is added.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_045_V1

## Decision
- Allow BR-063 as a small direct `pv_ae/panel_day_engine.py` cleanup rehearsal.
- Keep `release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py` byte-identical with the source panel engine.
- Scope is limited to replacing targeted `critical_fault == True` comparisons with a reusable bool mask.
- Treat the change as behavior-preserving unless BR-061/062 result delta checks prove otherwise.

## Reason
- The previous safety work exposed that direct engine patches need a full gate rehearsal before semantic changes are attempted.
- The `critical_fault` split is a suitable rehearsal because:
  - it is local,
  - it removes ambiguous pandas boolean equality,
  - it can keep source/package byte-identical,
  - it should not alter thresholds, labels, or output columns.

## Evidence Required
- critical bool mask safety review must pass.
- BR-054 panel-engine patch safety gate must pass.
- BR-060 combined prepatch runbook must pass.
- BR-061 post-patch scorecard must be generated.
- BR-062 scorecard compare must show no unexpected result drift.

## Evidence Result
- critical bool mask safety review:
  - `overall_status = pass`
  - `source_package_hash_equal = 1`
  - `source_old_bool_equality_count = 0`
  - `package_old_bool_equality_count = 0`
  - `source_new_mask_count = 1`
  - `package_new_mask_count = 1`
- BR-054 safety gate:
  - `overall_status = pass`
  - `fail_gate_count = 0`
- BR-060 prepatch runbook:
  - `overall_status = pass`
  - `engine_change_detected = 1`
- BR-061 post-patch scorecard:
  - `overall_status = pass`
  - `core_total_diff_count = 0`
- BR-062 compare:
  - `overall_status = pass`
  - `changed_metric_count = 0`
  - `core_result_changed_flag = 0`

## Consequence
- This patch does not improve detector performance.
- If all gates stay green, it proves the direct-engine patch workflow is usable for later semantic candidates.

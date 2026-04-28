<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_056_V1

## Decision
- Accept BR-074 as the trace review closure for BR-073's two manual common-cause targets.
- Treat the `gangui` row as a raw-only near-anchor trace only.
- Treat the `ktc_ess` row as a post-current common-cause/date-alignment mismatch.
- Keep official/current bridge candidates, semantic patch candidates, operator promotion, engine patching, and threshold patching at `0`.

## Why
- BR-073 reduced the common-cause structural blocker frontier from `49` rows to `2` manual trace targets.
- BR-074 shows those two targets do not close the missing official/current common-cause family:
  - `gangui` has a raw direct `group_off_date` row on `2025-11-28`, near raw-only signal dates `2025-11-15` and `2025-11-26`, but no official/current row.
  - `ktc_ess` has a raw direct `site_event_soft` row on `2025-10-26`, while the official/current and raw-only report dates are `2025-08-16`; the nearest signed gap is `71` days.
- The first can explain raw-only report generation.
- The second is too date-displaced to be used as current common-cause closure.

## Evidence
- BR-074 output root:
  - `/private/tmp/common_cause_manual_trace_review_check`
- Real result:
  - detail rows: `2`
  - raw-only report bridge candidate sum: `1`
  - official/current bridge candidate sum: `0`
  - semantic patch candidate sum: `0`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime output changes.
- No `panel_day_engine.py` semantic change.
- No new positive common-cause or panel-local label.
- The common-cause manual trace queue is now closed for this branch line.

## Next Required Action
- Preserve BR-071 through BR-074 as common-cause regression/hold evidence before any semantic algorithm patch.
- Do not loosen common-cause promotion semantics from raw-only near-anchor evidence alone.
- Do not reinterpret post-current common-cause rows as current closure unless an independent report-date correction is attached.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_047_V1

## Decision
- Accept BR-065 `local_morphology_family_shape_review` as the next narrowing layer after BR-064.
- Keep BR-065 audit-only:
  - `operator_promotion_allowed_flag = 0`
  - `engine_patch_candidate_flag = 0`

## Why
- BR-064 isolated 10 local morphology rows, but those rows still did not prove a fault family.
- Family-shape evidence must be checked against panel-day morphology before threshold proposals.
- A few diode-like VI days are not enough if the dominant pattern is voltage-dominant hard signal.

## Evidence
- BR-065 output root:
  - `/private/tmp/local_morphology_family_shape_review_check`
- Real result:
  - detail rows: `10`
  - two-axis review ready rows: `2`
  - recovery/recurrence-only hold rows: `8`
  - voltage-dominant hard-signal review rows: `2`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`

## Impact
- No production output changes.
- No `panel_day_engine.py` semantic change.
- The next review target is the 2 voltage-dominant rows, not all 10 local morphology rows.

## Next Required Action
- For the 2 `voltage_dominant_hard_signal_review` rows, separate:
  - partial-open/contact/voltage-axis physical fault hypothesis
  - measurement/reference/channel artifact hypothesis
- Do not propose a threshold until this distinction is evidence-backed.

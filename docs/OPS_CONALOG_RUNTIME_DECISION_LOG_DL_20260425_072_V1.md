<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_072_V1

## Decision
- Accept BR-090 as a pilot subtype-threshold replay over the BR-089 mixed truth input.
- Do not approve threshold tuning.
- Block broad duration/event-only candidates because they trigger deferred durable holds.
- Keep voltage-preserved and strict severity candidates as evidence-collection targets only.
- Keep direct `panel_day_engine.py` edits blocked.

## Why
- BR-089 finally produced a mixed replay set, but it is tiny: `1` positive and `9` negatives.
- Labeled-only performance would overstate confidence because broad rules can avoid the 9 negative rows while still firing on unadjudicated durable holds.
- BR-090 therefore adds `deferred_hold_hits` as an ambiguity-pressure metric.
- The replay shows:
  - duration/event-only rules trigger `6/6` deferred holds
  - low-mid `>=2d` triggers `3/6` deferred holds
  - voltage-preserved and strict low-mid candidates trigger the single positive and `0` holds
- Clean pilot behavior is not the same as tuning approval because positive support is only one row.

## Evidence
- BR-090 output root:
  - `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check`
- Real result:
  - replay case rows: `112`
  - summary rows: `7`
  - threshold tuning approved sum: `0`
  - patch authorization sums: `0`
- Decision counts:
  - `blocked_hold_pressure_and_insufficient_support`: `3`
  - `pilot_candidate_collect_more_positive_truth`: `4`
- Best evidence direction:
  - voltage-preserved shape candidates had TP `1`, FP `0`, deferred hold hits `0`
  - but support remains below threshold for tuning approval

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The project now has an executable replay harness that separates labeled performance from hold pressure.

## Next Required Action
- Collect more positive durable precursor truth, especially voltage-preserved shape cases.
- Re-examine the 6 deferred holds before loosening duration/event thresholds.
- Re-run BR-090 once there are at least 3 independent positives.
- Keep direct engine edits behind the BR-076 3-gate prepatch runbook.

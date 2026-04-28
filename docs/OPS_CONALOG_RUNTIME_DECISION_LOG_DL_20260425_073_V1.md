<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_073_V1

## Decision
- Accept BR-091 as a raw-shape review of the 6 BR-089 durable holds.
- Do not promote any of the 6 holds to positive truth.
- Keep voltage-preserved threshold candidates blocked until new positive truth is found elsewhere.
- Track current-limited/current-axis morphology as a separate subtype evidence lane.
- Keep direct `panel_day_engine.py` edits blocked.

## Why
- BR-090 showed that broad duration/event rules hit all 6 deferred holds.
- The key question was whether any of those 6 holds could be rescued as voltage-preserved positives after raw waveform proxy review.
- BR-091 recomputed selected raw-day V/I/P ratios for 48 selected raw days and found:
  - repeated voltage-low/current-preserved support: `0` rows
  - current-limited/current-axis support: `2` rows
  - no-low-shape selected raw support: `3` rows
  - weak/sparse support: `1` row
- This means the safe move is not to widen the positive set from these holds.

## Evidence
- BR-091 output root:
  - `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check`
- Real result:
  - hold summary rows: `6`
  - selected raw day rows: `48`
  - positive truth candidates: `0`
  - threshold tuning approved sum: `0`
  - patch authorization sums: `0`
- Decision counts:
  - `stay_hold_current_limited_shape`: `2`
  - `stay_hold_no_low_shape_on_selected_raw_days`: `3`
  - `stay_hold_weak_or_sparse_shape`: `1`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The immediate durable-hold ambiguity is reduced: these 6 are not the next positive truth source for voltage-preserved thresholding.

## Next Required Action
- Search for additional positive voltage-preserved durable precursor truth outside these 6 holds.
- Keep current-limited morphology in a separate subtype backlog.
- Re-run BR-090 only after the positive truth set grows.
- Keep direct engine edits behind the BR-076 3-gate prepatch runbook.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_071_V1

## Decision
- Accept BR-089 as a durable shape-review pass over the 7 BR-088 deferred precursor rows.
- Fill exactly 1 positive precursor truth label where voltage-low/current-preserved durable shape evidence is strong.
- Carry forward 9 BR-088 negative counterexamples.
- Leave 6 durable rows unassigned until raw waveform or independent family-shape evidence is stronger.
- Do not approve threshold tuning or direct `panel_day_engine.py` edits.

## Why
- BR-088 created negative replay candidates but had zero positive replay rows.
- Threshold replay needs both positive and negative truth rows, but positive rows must not be invented from weak durable context.
- BR-089 therefore uses a narrow positive rule:
  - repeated event days
  - persistent low `mid_ratio`
  - repeated voltage-low/current-preserved morphology
  - at least one hard anchor
  - no common-cause overlap
  - limited data-bad days
- Only `BR082-EPR-010` passes that rule.

## Evidence
- BR-089 output root:
  - `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check`
- Real result:
  - review rows: `16`
  - positive replay candidate rows: `1`
  - negative replay candidate rows: `9`
  - durable hold rows: `6`
  - threshold replay input candidate rows: `10`
  - threshold tuning approved: `0`
  - patch authorization sums: `0`
- Positive seed:
  - `BR089-DSR-010` / `BR084-RTR-010` / `BR082-EPR-010`
  - `site=conalog`
  - `panel_id=7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0`
  - `event_A_days=21`
  - `low_mid_days=21`
  - `voltage_low_current_ok_days=20`
  - `hard_anchor_days=1`
  - `common_cause_days=0`
- BR-084 mixed rebuild check:
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check`
  - `reviewed_negative=9`
  - `reviewed_positive=1`
  - `needs_evidence=6`
  - `threshold_replay_ready_count=10`
  - BR-083 fail counts: `0`
  - patch authorization sums: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The project now has a small mixed truth input suitable for pilot replay review, but not enough evidence for threshold tuning approval.

## Next Required Action
- Run a pilot subtype-threshold replay review using the BR-089 mixed input.
- Treat that replay as evidence scoring, not production tuning.
- Keep the 6 durable holds open for raw waveform or independent family-shape review.
- Keep direct engine edits blocked by the BR-076 3-gate prepatch runbook.

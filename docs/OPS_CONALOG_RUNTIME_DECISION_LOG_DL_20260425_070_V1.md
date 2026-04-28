<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_070_V1

## Decision
- Accept BR-088 as a conservative negative-only adjudication pass over BR-087.
- Fill BR-084 review input for 9 source-backed negative counterexamples.
- Do not fill any positive precursor label from BR-088.
- Do not open threshold replay from negative-only replay-ready rows.

## Why
- BR-087 separated review direction from truth labels.
- Two groups have enough source-backed evidence for conservative negative labels:
  - long-gap one-day/backdating rows with `block_precursor_backdating`
  - strict-sudden rows with `no_precursor_promotion`, gap `0d`, and prior signal count `0`
- Durable precursor rows remain plausible, but they still lack a defensible family-shape/continuity proof in the current evidence packet.

## Evidence
- BR-088 output root:
  - `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check`
- Real result:
  - adjudication rows: `16`
  - filled negative labels: `9`
  - filled positive labels: `0`
  - deferred rows: `7`
  - threshold replay input candidate rows: `9`
  - patch authorization sums: `0`
- BR-084 rebuild check:
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br088_conservative_check`
  - `reviewed_negative=9`
  - `needs_evidence=7`
  - `negative_counterexample=9`
  - `unassigned=7`
  - `threshold_replay_ready_count=9`
  - reviewed positive rows: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The project now has negative counterexamples, but still needs positive precursor truth rows before threshold replay.

## Next Required Action
- Inspect the 7 deferred durable precursor rows for raw/shape evidence.
- Fill positive labels only where same-family continuity and common-cause rejection are defensible.
- Rebuild BR-084 with a mixed positive/negative review input.
- Open subtype-conditioned threshold replay only after both sides exist.

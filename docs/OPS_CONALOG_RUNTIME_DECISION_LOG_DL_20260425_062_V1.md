<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_062_V1

## Decision
- Accept BR-080 as the current subtype truth expansion backlog.
- Keep subtype hypotheses below operator-facing labels until exact subtype truth and counterexamples exist.
- The next implementation target is `panel_day_engine_episode_truth_map_v1`.

## Why
- BR-079 identified subtype truth as the first P0 blocker for algorithm evolution.
- BR-080 converts the subtype roadmap into a reproducible backlog rather than relying on conversation memory.
- Current candidates are useful context, but they are not exact truth support:
  - shadow subtype panels are review context
  - family candidate pools are review context
  - physical confirmation rows are still gaps
  - common-cause rows are still reservoir/structural-blocker context

## Evidence
- BR-080 output root:
  - `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check`
- Real result:
  - subtype backlog rows: `17`
  - family summary rows: `6`
  - P0 subtype backlog rows: `12`
  - current exact truth support sum: `0`
  - missing optional inputs: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- Future subtype and threshold work now has an explicit truth backlog.

## Next Required Action
- Build `panel_day_engine_episode_truth_map_v1`.
- Use the episode map to separate:
  - durable precursor
  - one-day episode
  - long-gap backdating
  - true sudden fault
  - common-cause or measurement displacement
- Only after subtype/episode truth exists should subtype-conditioned threshold replay be opened.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

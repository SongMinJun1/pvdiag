<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_063_V1

## Decision
- Accept BR-081 as the current episode truth map.
- Keep every episode row in `truth_pending` status until a review packet proves or rejects the episode interpretation.
- Use `panel_day_engine_episode_truth_review_packet_v1` as the next implementation target.

## Why
- BR-080 showed current subtype hypotheses have exact truth support `0`; threshold replay would be premature without episode-level truth rows.
- The user question is not only "did a fault occur?", but whether a previous signal was:
  - a real durable precursor
  - a one-day or sparse episode
  - long-gap backdating
  - strict-sudden behavior
  - common-cause/group displacement
  - recovery/recurrence observation
- BR-081 makes those categories explicit before any rule or threshold is changed.

## Evidence
- BR-081 output root:
  - `/private/tmp/panel_day_engine_episode_truth_map_br081_check`
- Real result:
  - episode truth map rows: `244`
  - summary rows: `10`
  - action rows: `5`
  - truth status: `truth_pending=244`
  - bucket counts: `common_cause_or_group_episode_hold=205`, `recovery_recurrence_observation=12`, `long_gap_backdating_hold=12`, `durable_precursor_candidate_review=7`, `episode_truth_requirement=5`, `strict_anchor_sudden_review=3`
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
- Future precursor-vs-abrupt and subtype-threshold work now has an explicit episode review map.

## Next Required Action
- Build `panel_day_engine_episode_truth_review_packet_v1`.
- Start with:
  - `long_gap_backdating_hold`
  - `strict_anchor_sudden_review`
  - `durable_precursor_candidate_review`
- Keep common-cause and recovery/recurrence buckets as held review lanes, not promotion seeds.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

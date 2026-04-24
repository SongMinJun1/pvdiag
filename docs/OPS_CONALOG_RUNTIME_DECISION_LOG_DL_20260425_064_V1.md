<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_064_V1

## Decision
- Accept BR-082 as the current episode truth review packet.
- Review units are deduplicated episode rows, not raw source-lens rows.
- Keep all reviewer truth labels blank until evidence is actually attached.

## Why
- BR-081 intentionally preserved the G1 long-gap lens as a duplicate source lens.
- Reviewing those duplicates as separate rows would make the process noisy and error-prone.
- BR-082 collapses duplicate lenses from `22` selected source rows to `16` review rows while keeping source traceability.
- This lets the next step focus on the real question:
  - real precursor
  - over-backdated or sparse episode
  - strict-sudden without prior episode
  - common-cause/measurement hold
  - insufficient evidence hold

## Evidence
- BR-082 output root:
  - `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check`
- Real result:
  - input episode map rows: `244`
  - selected source lens rows: `22`
  - review packet rows: `16`
  - collapsed duplicate lens rows: `6`
  - review tracks: `durable_precursor_review=7`, `long_gap_backdating_review=6`, `strict_sudden_prior_episode_review=3`
  - review priorities: `P0=9`, `P1=7`
  - reviewer truth labels assigned: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- Future threshold replay now has a concrete review packet to fill before replay.

## Next Required Action
- Attach evidence or reviewer labels to BR-082 rows, then build `panel_day_engine_reviewed_episode_truth_rows_v1`.
- Keep common-cause and recovery/recurrence buckets as separate held packet lanes.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

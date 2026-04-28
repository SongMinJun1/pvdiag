<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_066_V1

## Decision
- Accept BR-084 as the current reviewed episode truth-row intake table.
- Do not open subtype-conditioned threshold replay yet, because no reviewer evidence labels are attached.
- Treat all current BR-084 rows as `needs_evidence`.

## Why
- BR-083 confirmed the BR-079 through BR-082 scaffold is internally consistent.
- However, consistency is not the same as truth evidence.
- The safe next step is to create a structured place for reviewer evidence and labels, while keeping replay and production changes blocked until labels are actually attached.

## Evidence
- BR-084 output root:
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check`
- Real result:
  - input review packet rows: `16`
  - reviewed truth rows: `16`
  - review status: `needs_evidence=16`
  - truth role: `unassigned=16`
  - reviewer truth labels assigned: `0`
  - threshold replay ready rows: `0`
  - BR-083 fail count: `0`
  - BR-083 P0 fail count: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- Future replay work now has a structured evidence/label intake table.

## Next Required Action
- Attach evidence paths and reviewer labels to BR-084 rows.
- Rebuild BR-084 with `--review-input`.
- Only after positive and negative replay-ready rows exist should `panel_day_engine_subtype_threshold_replay_v1` be opened.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

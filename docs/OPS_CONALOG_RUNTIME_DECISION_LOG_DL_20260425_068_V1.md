<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_068_V1

## Decision
- Accept BR-086 as the source-trace guard for BR-085 evidence attachment.
- Do not fill reviewer labels from source trace alone.
- Keep threshold replay blocked until BR-084 is rebuilt from explicitly filled positive/negative review rows.

## Why
- BR-085 created useful cards and a blank review template, but a reviewer still needed confidence that the cited source rows were real and recoverable.
- BR-086 confirms the source references resolve to actual BR-017 CSV rows and match expected site/panel/date identity.
- This removes an artifact-recovery blocker without crossing into truth-label assignment.

## Evidence
- BR-086 output root:
  - `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check`
- Real result:
  - review rows: `16`
  - source references: `22`
  - source rows resolved: `22`
  - source identity matches: `22`
  - source identity mismatches: `0`
  - trace-ready references: `22`
  - reviewer truth labels assigned: `0`
  - reviewer evidence paths filled: `0`
  - threshold replay ready rows: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The next reviewer can now adjudicate rows from source-backed cards rather than reconstructing source row provenance manually.

## Next Required Action
- Inspect BR-086 trace audit with BR-085 evidence cards.
- Fill the BR-085 review template only where a label is defensible.
- Rebuild BR-084 with the filled review template.
- Open subtype-conditioned threshold replay only after positive and negative replay-ready rows exist.

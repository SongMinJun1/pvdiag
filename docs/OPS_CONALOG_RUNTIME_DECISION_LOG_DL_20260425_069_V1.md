<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_069_V1

## Decision
- Accept BR-087 as a human adjudication worksheet over the BR-085/BR-086 evidence stack.
- Use `suggested_review_direction` only as review guidance.
- Keep reviewer labels blank until a human fills a copy of the draft review input with evidence paths.
- Keep threshold replay blocked until BR-084 is rebuilt from explicitly filled positive/negative review rows.

## Why
- BR-086 proved that source references resolve, but source trace readiness is still not a truth label.
- The next risk is reviewer confusion: long-gap backdating, strict-sudden prior-episode, and durable precursor rows need different judging questions.
- BR-087 reduces that confusion by compressing 22 source trace rows into 16 worksheet rows and separating review direction from truth-label assignment.

## Evidence
- BR-087 output root:
  - `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check`
- Real result:
  - source trace rows compressed: `22 -> 16`
  - worksheet rows: `16`
  - trace-ready worksheet rows: `16`
  - `negative_or_hold_candidate`: `6`
  - `strict_sudden_negative_candidate`: `3`
  - `manual_positive_or_hold_candidate`: `7`
  - reviewer truth labels assigned: `0`
  - reviewer evidence paths filled: `0`
  - threshold replay ready rows: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`
- BR-084 reverse check with the unfilled BR-087 draft:
  - reviewed truth rows: `16`
  - review status counts: `needs_evidence=16`
  - truth role counts: `unassigned=16`
  - threshold replay ready rows: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- The next reviewer now has one row per review packet, not scattered source trace rows.

## Next Required Action
- Inspect BR-087 worksheet rows with BR-085 evidence cards and BR-086 source traces.
- Fill a copied review input only where label, evidence path, and reviewer notes are defensible.
- Rebuild BR-084 with the filled review input.
- Open subtype-conditioned threshold replay only after positive and negative replay-ready rows exist.

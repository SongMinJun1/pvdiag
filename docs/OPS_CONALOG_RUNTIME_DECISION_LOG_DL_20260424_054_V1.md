<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_054_V1

## Decision
- Accept BR-072 as the current common-cause exact same-day seed search.
- Keep exact common-cause family closure at `0`.
- Keep raw same-day direct common-cause rows as `candidate_reservoir + structural_blocker`, not production or threshold seeds.
- Continue report-lane/date-alignment blocker removal before reopening any common-cause semantic algorithm patch.

## Why
- BR-072 confirms there is meaningful evidence, but not yet closure-grade evidence.
- The useful frontier is:
  - `49` panels with raw same-day direct common-cause evidence
  - `101` raw direct rows
  - `49` structural blockers where report-layer/date alignment still prevents official/current same-day closure
- The current conservative stance is therefore not stalling the work.
- It is preventing a category error:
  - raw row presence is not the same as official/current exact family closure
  - spatial/common-cause evidence is not panel-local fault-family evidence

## Evidence
- BR-072 output root:
  - `/private/tmp/common_cause_exact_seed_search_check`
- Real result:
  - detail rows: `176`
  - exact family closure candidates: `0`
  - candidate reservoir panels: `49`
  - structural blocker panels: `49`
  - BR-071 blocker/regression seed panels retained: `50`
  - supportive/context hold panels: `127`
  - operator promotion allowed sum: `0`
  - engine patch candidate sum: `0`
  - threshold patch allowed sum: `0`
- Site shape:
  - `gangui`: `19` raw-direct panels / `71` raw-direct rows, no official/current entry
  - `ktc_ess`: `30` raw-direct panels / `30` raw-direct rows, one official/current entry but no same-day overlap; nearest current gap `71` days
  - `conalog`: common-cause context only, no raw same-day direct common-cause reservoir in this search

## Impact
- No runtime output changes.
- No `panel_day_engine.py` semantic change.
- No new positive fault-family label.
- Adds an executable search layer that distinguishes:
  - `exact_family_closure`
  - `candidate_reservoir`
  - `structural_blocker`
  - `supportive_hint`
  - BR-071 blocker/regression usage tag

## Next Required Action
- Use BR-072 before any future common-cause semantic patch discussion.
- Treat `49 panels / 101 rows` as the next search reservoir.
- Target the structural blockers:
  - report-lane entry absence
  - official/current date displacement
  - raw-only or precursor-only common-cause evidence that has not closed at the current report layer
- Do not loosen production semantics until exact closure or a clearly scoped structural-blocker patch target is proven.

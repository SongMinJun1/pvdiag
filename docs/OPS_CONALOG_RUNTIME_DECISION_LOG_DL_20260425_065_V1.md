<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260425_065_V1

## Decision
- Accept BR-083 as the current direction/assumption audit guard.
- Require BR-083 to stay green before moving from BR-082 review packets to reviewed episode truth rows or threshold replay.

## Why
- BR-081 exposed a real near-miss: G1 long-gap rows could be hidden if proxy duration/common-cause precedence was read too broadly.
- BR-082 also introduced a deliberate duplicate-lens collapse step, which must be protected because source-lens rows and review rows are different units.
- The safest response is not to freeze progress, but to make the assumptions executable before the next semantic step.

## Evidence
- BR-083 output root:
  - `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check`
- Real result:
  - total checks: `40`
  - pass count: `40`
  - fail count: `0`
  - P0 fail count: `0`
  - summary rows: `15`
  - action rows: `4`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Impact
- No runtime semantics change.
- No `panel_day_engine.py` change.
- No threshold change.
- No operator-facing output change.
- No release artifact regeneration.
- Future reviewed truth-row work now has a preflight guard against direction drift.

## Next Required Action
- If BR-083 remains green, attach evidence or reviewer labels to BR-082 rows and build `panel_day_engine_reviewed_episode_truth_rows_v1`.
- If BR-083 fails, repair the failed branch artifact before continuing.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

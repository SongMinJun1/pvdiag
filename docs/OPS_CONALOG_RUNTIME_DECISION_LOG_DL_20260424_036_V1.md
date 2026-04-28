<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_036_V1

## Decision
- Tighten the panel-engine patch safety gate before moving to the next evidence or engine task.
- Treat BR-054 as the effective safety contract for future `pv_ae/panel_day_engine.py` and packaged mirror changes.

## Reason
- BR-053 established the gate structure, but review found four precision holes:
  - package-only engine drift was not blocked.
  - source/package content equality was not checked.
  - deleted evidence could still be counted by path pattern.
  - unrelated docs/smoke/build files could satisfy the gate by filename alone.
- Since the project is approaching possible engine work, these holes should be closed before continuing.

## Evidence
- Synthetic smoke now verifies:
  - `source-only` fails.
  - `package-only` fails.
  - `source/package content mismatch` fails.
  - `deleted required evidence` fails.
  - complete source/package/doc/smoke/shadow packet passes.
- Current real patch has no engine code change and passes the tightened gate.

## Consequence
- No runtime verdict, threshold, row universe, or operator-facing semantic changed.
- The next evidence task can still be `no_report_heuristic_match` decomposition.
- Any future engine patch must pass the tightened gate before commit:
  - source/package both changed
  - source/package byte-identical
  - related active docs/builders/smokes present
  - no deleted required evidence used as proof
  - no `data/<site>/raw` or `data/<site>/out` payloads committed

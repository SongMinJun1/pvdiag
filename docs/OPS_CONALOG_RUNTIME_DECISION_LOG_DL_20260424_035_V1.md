<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_035_V1

## Decision
- Before any direct `pv_ae/panel_day_engine.py` algorithm patch, require a reproducible safety-gate packet.
- Accept BR-053 as the minimum gate for panel-engine source/package changes.

## Reason
- The roadmap is now close to actual engine work, but the evidence line still has open blockers:
  - exact-family closure is still missing.
  - `no_report_heuristic_match = 8` is not yet decomposed.
  - common-cause, report-lane friction, and local morphology axes must remain separated.
- A direct engine edit without packet-level checks could silently mix:
  - evidence-only sidecars
  - production semantics
  - source/package mirrors
  - generated data
  - public paper/operator documentation
- The safety gate turns that risk into a visible pass/fail table before the patch is allowed to proceed.

## Evidence
- `/private/tmp/panel_engine_patch_safety_gate_check` reports:
  - `engine_change_detected = 0`
  - `source_engine_changed = 0`
  - `package_engine_changed = 0`
  - `overall_status = pass`
- synthetic smoke verifies:
  - docs/safety-only packets pass.
  - source-engine-only packets fail.
  - complete source/package/doc/smoke/shadow packets pass.

## Consequence
- This decision does not change runtime verdicts, thresholds, row universe, or operator-facing semantics.
- The next evidence implementation may continue, but any future `panel_day_engine.py` patch must first include:
  - BR note
  - decision log
  - shadow/safety/audit builder
  - smoke test
  - active register update
  - Gate7 update or reaffirmation
  - public behavior documentation when behavior can change
  - packaged mirror sync when source engine changes
  - no committed `data/<site>/raw` or `data/<site>/out` payloads

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_083_DIRECTION_ASSUMPTION_AUDIT_V1

## Purpose
- Add a reproducible guard before continuing beyond BR-082.
- Audit BR-079 through BR-082 for direction drift, stale counts, bucket precedence errors, duplicate-lens confusion, premature truth assignment, and accidental patch authorization.
- Specifically guard the recently observed risk:
  - G1 long-gap rows must not disappear into a broader common-cause bucket.
  - BR-082 must collapse duplicate source lenses for review while preserving source traceability.
- Keep this branch guard-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_direction_assumption_audit_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check` | BR-079 algorithm evolution map outputs |
| `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check` | BR-080 subtype truth backlog outputs |
| `/private/tmp/panel_day_engine_episode_truth_map_br081_check` | BR-081 episode truth map outputs |
| `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check` | BR-082 episode truth review packet outputs |

## Outputs
- `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_summary_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_note_v1.md`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.json`

## Real Result
- total checks: `40`
- pass count: `40`
- fail count: `0`
- P0 fail count: `0`
- summary rows: `15`
- action rows: `4`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Guarded Assumptions
| assumption | result |
| --- | --- |
| BR-079 layer/gap/action counts match JSON and CSV | PASS |
| BR-079 recommended next branch remains subtype truth backlog | PASS |
| BR-080 exact truth support remains `0` | PASS |
| BR-080 recommended next branch remains episode truth map | PASS |
| BR-081 all rows remain `truth_pending` | PASS |
| BR-081 bucket counts match expected counts | PASS |
| BR-081 G1 long-gap lens is preserved as `long_gap=6`, `common_hold=1` | PASS |
| BR-081 durable precursor candidates have `common_cause_flag_sum=0` | PASS |
| BR-082 source lens collapse is `22 -> 16`, collapsed `6` | PASS |
| BR-082 long-gap rows retain both G1 and episode-shadow source artifacts | PASS |
| BR-082 reviewer truth labels remain blank | PASS |
| BR-079 through BR-082 recommended-next chain is intact | PASS |
| BR-079 through BR-082 direct engine boundary still mentions BR-076 3-gate | PASS |

## Important Read
- BR-083 says the recent scaffolding is internally consistent; it does not say the algorithm is correct or production-ready.
- A future failure in this guard should block reviewed truth rows, threshold replay, and direct engine work until repaired.
- Direct `panel_day_engine.py` edits remain behind the BR-076 3-gate prepatch runbook.

## Ordered Next Path
1. Use BR-083 before continuing beyond BR-082.
2. If BR-083 remains green, attach reviewer evidence or labels to BR-082 rows.
3. Build `panel_day_engine_reviewed_episode_truth_rows_v1`.
4. Run subtype-conditioned threshold replay only after reviewed episode truth rows exist.
5. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-083 as the current direction/assumption guard for BR-079 through BR-082.
- The next safest implementation remains `panel_day_engine_reviewed_episode_truth_rows_v1`, but only after BR-083 stays green.
- BR-083 does not approve threshold tuning, semantic loosening, operator-facing precursor promotion, or direct engine edits.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py research/prognostics/smoke_test_panel_day_engine_direction_assumption_audit_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_direction_assumption_audit_v1.py
python3 research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_direction_assumption_audit_br083_check
```

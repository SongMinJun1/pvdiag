<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_100_UNLABELED_FAULT_CANDIDATE_FRONTIER_V1

## Purpose
- Test the hypothesis that the 6 labeled/current faults are not the full fault universe.
- Separate confirmed/seed-reviewed labels from data-only unlabeled fault-like candidates.
- Keep this branch audit-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py`

## Input
| input | role |
| --- | --- |
| `release/conalog_full_runtime_v1/package/_share/panel_date_reaudit_working.csv` | packaged seed/re-audit candidate table |

## Outputs
- `/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check/panel_day_engine_unlabeled_fault_candidate_frontier_v1.csv`
- `/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check/panel_day_engine_unlabeled_fault_candidate_priority_v1.csv`
- `/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check/panel_day_engine_unlabeled_fault_candidate_site_summary_v1.csv`
- `/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check/panel_day_engine_unlabeled_fault_candidate_note_v1.md`
- `/private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check/panel_day_engine_unlabeled_fault_candidate_frontier_v1.json`

## Real Result
- source rows: `114`
- seed positive fault rows: `5`
- seed non-panel/negative rows: `8`
- seed needs-more-info rows: `1`
- unlabeled rows: `100`
- unlabeled persistent rows: `8`
- strong unlabeled data-only candidates: `8`
- strong unlabeled isolated candidates: `3`
- strong unlabeled common-cause-screen candidates: `5`
- strong unlabeled 30d+ lead candidates: `6`
- trigger-only unlabeled rows: `92`
- trigger-only bulk/common-cause screen rows: `85`
- truth intake allowed sum: `0`
- engine patch allowed sum: `0`

## Bucket Counts
| bucket | rows | interpretation |
| --- | ---: | --- |
| `L_reviewed_seed_positive_fault` | 5 | already reviewed positive references |
| `L_reviewed_seed_non_panel_or_negative` | 8 | already reviewed negative or non-panel/group-side rows |
| `L_reviewed_seed_needs_more_info` | 1 | reviewed but still unresolved |
| `U1_strong_persistent_lead_review` | 8 | strongest data-only unlabeled review targets |
| `U3_trigger_only_common_cause_screen` | 85 | trigger-only rows that first need breadth/common-cause screen |
| `U4_trigger_only_singleton_screen` | 7 | low-confidence singleton strict-trigger-only screen |

## Site Split
| site | total_rows | unlabeled_rows | strong_unlabeled_candidate_rows | isolated_strong_rows | common_cause_screen_strong_rows | strong_unlabeled_30d_plus_rows | trigger_only_unlabeled_rows | trigger_only_bulk_screen_rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conalog` | 72 | 64 | 4 | 3 | 1 | 2 | 60 | 60 |
| `gangui` | 40 | 36 | 4 | 0 | 4 | 4 | 32 | 25 |
| `ktc_ess` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Interpretation
- The labeled/current fault count is not the full fault universe; it is only the confirmed/seed-reviewed subset available now.
- The safest expansion target is the `8` unlabeled rows with `persistent_5of7`, `high` confidence, and at least `7` lead days.
- Only `3` of those strong candidates are isolated by current breadth counts; the other `5` still need common-cause/root/group clearance.
- The `92` trigger-only unlabeled rows are not automatically fault-like. `85` of them sit in bulk/common-cause screen territory, so direct promotion would likely inflate false positives.

## Safety Boundary
- BR-100 is a candidate-frontier audit, not truth intake.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` are always `0`.
- Any candidate promoted later must first gain exact-panel raw evidence plus independent maintenance/inspection or physical confirmation and explicit common-cause/artifact clearance.

## Ordered Next Path
1. Review the `8` `U1_strong_persistent_lead_review` rows first.
2. Split them into isolated physical candidates versus breadth/common-cause candidates.
3. For isolated rows, attach raw curve snippets and exact-panel maintenance/inspection evidence.
4. For breadth rows, clear site/root/group common-cause before any panel-local interpretation.
5. Only after attachment should a separate truth-intake branch consider expanding positive labels beyond the seed/current fault set.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py research/prognostics/smoke_test_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py
python3 research/prognostics/build_panel_day_engine_unlabeled_fault_candidate_frontier_v1.py --repo-root "$(pwd)" --input-dir release/conalog_full_runtime_v1/package/_share --output-dir /private/tmp/panel_day_engine_unlabeled_fault_candidate_frontier_br100_check
```

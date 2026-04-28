<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_080_SUBTYPE_TRUTH_EXPANSION_BACKLOG_V1

## Purpose
- Implement the BR-079 next action: build `panel_day_engine_subtype_truth_expansion_backlog_v1`.
- Convert the BR-018 subtype hypothesis map into a concrete truth/evidence backlog.
- Keep subtype names as review hypotheses until exact truth rows and counterexamples exist.
- Keep this branch evidence/backlog-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py`

## Inputs
| input | role |
| --- | --- |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_018_FAULT_SUBTYPE_HYPOTHESIS_MAP_V1.csv` | canonical subtype hypothesis row universe |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_FAULT_MORPHOLOGY_ATLAS_V1.csv` | family-level morphology context |
| `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_gap_audit_v1.csv` | BR-079 gap boundary |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_019_FAULT_SUBTYPE_SHADOW_SUMMARY_V1.csv` | current shadow subtype context |
| `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv` | family candidate context |
| `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv` | local morphology shape context |
| `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv` | physical confirmation gap context |
| `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv` | common-cause bridge/reservoir context |

## Outputs
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_summary_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_note_v1.md`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_v1.json`

## Real Result
- subtype backlog rows: `17`
- family summary rows: `6`
- P0 subtype backlog rows: `12`
- current exact truth support sum: `0`
- missing optional inputs: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Family Summary
| family | subtype rows | P0 rows | current context |
| --- | ---: | ---: | --- |
| `degradation_soiling_shadow` | 4 | 2 | shadow panels 19; next artifact `panel_day_engine_episode_truth_map_v1` |
| `open_connection_partial` | 3 | 3 | shadow panels 90; candidate pool 2; physical confirmation gap 2 |
| `diode_substring` | 3 | 3 | shadow panels 25; candidate pool 3 |
| `measurement_feedback` | 3 | 0 | candidate pool 6; measurement QA truth packet needed |
| `external_common_cause` | 3 | 3 | candidate pool 176; common-cause reservoir/structural rows 98 |
| `strict_anchor_sudden` | 1 | 1 | not a BR-017 morphology family; next artifact `panel_day_engine_episode_truth_map_v1` |

## Important Read
- `current_candidate_pool_count` and related counts are context/backlog material, not exact truth support.
- `current_exact_truth_support_count` is intentionally `0` for every subtype row.
- Therefore BR-080 does not approve:
  - operator-facing subtype labels
  - threshold updates
  - AE root-cause claims
  - voltage-axis loosening
  - common-cause semantic loosening
  - direct `panel_day_engine.py` edits

## Ordered Next Path
1. Build `panel_day_engine_episode_truth_map_v1`.
2. Build exact subtype review packets for open/diode/degradation/strict-sudden P0 rows.
3. Attach exact-panel physical confirmation evidence for voltage-dominant review rows, then rerun BR-069/070.
4. Build common-cause bridge exact-closure packet before common-cause semantic loosening.
5. Only after truth rows exist, run subtype-conditioned threshold replay.

## Decision
- Treat BR-080 as the current subtype truth expansion backlog.
- Use it before making subtype labels or threshold claims.
- The next safest implementation is `panel_day_engine_episode_truth_map_v1`.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py research/prognostics/smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py
python3 research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check
```

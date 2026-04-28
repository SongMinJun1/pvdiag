<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_079_ALGORITHM_EVOLUTION_MAP_V1

## Purpose
- Freeze the current `panel_day_engine.py` algorithm as an evidence-layer map before changing the algorithm.
- Make the next development path explicit: subtype truth first, episode truth second, threshold replay third, direct engine review last.
- Keep this branch audit/navigation-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_algorithm_evolution_map_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_algorithm_evolution_map_v1.py`

## Outputs
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_layer_map_v1.csv`
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_gap_audit_v1.csv`
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_summary_v1.csv`
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_note_v1.md`
- `/private/tmp/panel_day_engine_algorithm_evolution_map_br079_check/panel_day_engine_algorithm_evolution_map_v1.json`

## Real Result
- mapped algorithm layers: `10`
- evidence gaps: `7`
- P0 gaps: `4`
- ordered next actions: `6`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Algorithm Read
| layer family | current role | safe interpretation |
| --- | --- | --- |
| train-only vbin reference | peer/reference stratification | context only, not root-cause evidence |
| AE reconstruction anomaly | morphology/anomaly detector | candidate signal only, not root-cause classifier |
| daily rule/subtype labels | hypothesis assignment | needs episode and multi-axis evidence before promotion |
| group-off/common-cause gate | local-promotion suppressor | protects against panel-local overpromotion |
| V-drop critical SSOT | hard-evidence candidate | blocked from threshold loosening until physical confirmation closes |
| final_fault boundary | confirmed operator-facing verdict | should move last, not first |
| EWS local precursor | causal precursor candidate | one axis only; no direct promotion |
| site-event context | external/common-cause marker | context/suppressor until official/current bridge exists |
| prefault_B template | conservative review heuristic | needs subtype-conditioned calibration before threshold patch |
| audit/report outputs | traceability surface | use for navigation and shadow evidence without changing semantics |

## Evidence Gaps
| gap | priority | blocks |
| --- | --- | --- |
| fault subtype truth | `P0` | operator-facing subtype label or performance claim |
| episode ground truth | `P0` | precursor onset threshold patch |
| independent physical confirmation | `P0` | voltage-axis threshold loosening |
| official/current common-cause bridge | `P0` | common-cause semantic loosening |
| threshold calibration | `P1` | threshold update |
| AE role boundary | `P1` | AE-based root-cause claim |
| monolithic engine maintainability | `P2` | large refactor mixed with semantics |

## Ordered Next Path
1. Freeze current algorithm layers as the baseline map. This branch implements it.
2. Build `panel_day_engine_subtype_truth_expansion_backlog_v1`.
3. Build `panel_day_engine_episode_truth_map_v1`.
4. Run `panel_day_engine_subtype_threshold_replay_v1`.
5. Run the BR-076 3-gate prepatch runbook before direct engine review.
6. Shadow-apply exactly one selected rule candidate before any production patch.

## Decision
- Treat BR-079 as the current algorithm-evolution map.
- Do not claim performance improvement from current changes without truth-label evaluation.
- Do not use AE/EWS alone as root-cause or operator-facing promotion evidence.
- Do not loosen voltage/common-cause semantics until their P0 gaps close.
- The next safest implementation is subtype-truth backlog construction, not direct `panel_day_engine.py` edits.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_algorithm_evolution_map_v1.py research/prognostics/smoke_test_panel_day_engine_algorithm_evolution_map_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_algorithm_evolution_map_v1.py
python3 research/prognostics/build_panel_day_engine_algorithm_evolution_map_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_algorithm_evolution_map_br079_check
```

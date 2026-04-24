<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_092_VOLTAGE_PRESERVED_POSITIVE_SEARCH_V1

## Purpose
- Implement the next safe step after BR-091: search outside the 6 durable holds for voltage-low/current-preserved precursor-like candidates.
- Keep one best candidate per panel hard episode so repeated onset dates do not inflate the count.
- Mark BR-089 known positive/negative/hold overlaps before any row is used as truth or threshold evidence.
- Keep this branch evidence/search-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_v1.csv` | BR-089 known positive/negative/hold review rows |
| `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv` | BR-091 hold-resolution safety input |
| `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv` | tri-site panel-day core metrics |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_v1.json`

## Real Result
- candidate rows: `96`
- summary rows: `10`
- new search candidates: `94`
- manual review ready rows: `86`
- known positive seed rediscovered: `1`
- known negative overlap rows: `1`
- known deferred hold overlap rows: `0`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Candidate Tier Counts
| candidate tier | rows |
| --- | ---: |
| `strong_b089_like` | 80 |
| `voltage_preserved_10d` | 8 |
| `voltage_preserved_2d_review` | 8 |

## Site And Role Summary
| site | tier | role | action | rows | unique panels | manual review ready |
| --- | --- | --- | --- | ---: | ---: | ---: |
| `gangui` | `strong_b089_like` | `new_search_candidate` | `review_new_candidate_before_truth_use` | 49 | 9 | 49 |
| `ktc_ess` | `strong_b089_like` | `new_search_candidate` | `review_new_candidate_before_truth_use` | 18 | 2 | 18 |
| `conalog` | `strong_b089_like` | `new_search_candidate` | `review_new_candidate_before_truth_use` | 12 | 2 | 12 |
| `conalog` | `strong_b089_like` | `known_positive_seed` | `sanity_check_known_positive_seed` | 1 | 1 | 0 |
| `conalog` | `voltage_preserved_10d` | `new_search_candidate` | `review_new_candidate_before_truth_use` | 4 | 2 | 4 |
| `gangui` | `voltage_preserved_10d` | `known_negative_counterexample` | `block_known_negative_counterexample_overlap` | 1 | 1 | 0 |
| `gangui` | `voltage_preserved_10d` | `new_search_candidate` | `review_new_candidate_before_truth_use` | 3 | 2 | 3 |
| `ktc_ess` | `voltage_preserved_2d_review` | `new_search_candidate` | `hold_low_support_search_hit` | 3 | 3 | 0 |
| `conalog` | `voltage_preserved_2d_review` | `new_search_candidate` | `hold_low_support_search_hit` | 2 | 2 | 0 |
| `gangui` | `voltage_preserved_2d_review` | `new_search_candidate` | `hold_low_support_search_hit` | 3 | 3 | 0 |

## Known Reviewed Overlaps
| row | site | panel | anchor | onset | gap | tier | role | action |
| --- | --- | --- | --- | --- | ---: | --- | --- | --- |
| `BR092-VPPS-070` | `conalog` | `7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0` | `2024-11-26` | `2024-11-06` | 20 | `strong_b089_like` | `known_positive_seed` | `sanity_check_known_positive_seed` |
| `BR092-VPPS-083` | `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.9` | `2025-10-27` | `2025-07-07` | 112 | `voltage_preserved_10d` | `known_negative_counterexample` | `block_known_negative_counterexample_overlap` |

## Interpretation
- The search successfully rediscovers the one BR-089 positive seed, so the scanner can find the intended voltage-preserved morphology.
- The same search family also overlaps one reviewed negative counterexample. That is a useful warning: voltage-preserved core-shape search hits are review candidates, not truth labels.
- None of the 6 BR-091 durable holds appears as a voltage-preserved positive candidate, preserving the BR-091 conclusion.
- The large `new_search_candidate` pool is a candidate reservoir. It needs confirmation and de-duplication before becoming truth support.
- BR-092 therefore increases the positive-evidence search space, but does not improve runtime performance or change outputs by itself.

## Safety Boundary
- BR-092 is search/evidence only.
- Search hits are not positive truth labels.
- Known negative overlap blocks direct thresholding from this search pattern alone.
- Runtime and operator-facing outputs are unchanged.
- Direct `panel_day_engine.py` edits remain blocked behind confirmed truth support, replay, and the BR-076 3-gate prepatch runbook.

## Ordered Next Path
1. Build a confirmation packet for the `manual_review_ready=1` new candidates.
2. Deduplicate repeated anchors by panel/root/date family before expanding truth rows.
3. Require independent source, physical inspection, maintenance, or raw waveform confirmation before promoting any candidate to positive truth.
4. Re-run BR-090 only after at least 3 independent positive truth rows are confirmed.
5. Keep current-limited/current-axis morphology as a separate subtype backlog.

## Decision
- Accept BR-092 as a positive-truth candidate reservoir.
- Do not use BR-092 as threshold approval.
- Use the known negative overlap as a regression/counterexample warning for future voltage-preserved rules.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

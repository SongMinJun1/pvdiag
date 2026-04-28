<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_091_DURABLE_HOLD_RAW_SHAPE_REVIEW_V1

## Purpose
- Implement the next safe step after BR-090: inspect the 6 deferred durable holds with selected raw-day waveform proxy metrics.
- Separate hold rows into voltage-preserved, current-limited, mixed-axis, weak/sparse, and no-low-shape categories.
- Keep this branch evidence-only:
  - no positive truth labels
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_durable_hold_raw_shape_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_v1.csv` | BR-089 shape review rows |
| `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv` | site panel-day core metrics |
| `/Users/b9gc/pvdiag/data/<site>/raw/*.csv` | selected raw-day waveform proxy source |

## Outputs
- `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_summary_v1.csv`
- `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_days_v1.csv`
- `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_note_v1.md`
- `/private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check/panel_day_engine_durable_hold_raw_shape_review_v1.json`

## Real Result
- hold summary rows: `6`
- selected raw day rows: `48`
- positive truth candidates: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Decision Counts
| raw shape decision | rows |
| --- | ---: |
| `stay_hold_current_limited_shape` | 2 |
| `stay_hold_no_low_shape_on_selected_raw_days` | 3 |
| `stay_hold_weak_or_sparse_shape` | 1 |

## Hold Summary
| raw hold row | shape row | packet row | site | gap | decision | raw low-mid days | raw voltage-low/current-ok days | raw current-low/voltage-ok days | positive candidate |
| --- | --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| `BR091-DHR-001` | `BR089-DSR-011` | `BR082-EPR-011` | `conalog` | 54 | `stay_hold_no_low_shape_on_selected_raw_days` | 0 | 0 | 0 | 0 |
| `BR091-DHR-002` | `BR089-DSR-012` | `BR082-EPR-012` | `conalog` | 75 | `stay_hold_no_low_shape_on_selected_raw_days` | 0 | 0 | 0 | 0 |
| `BR091-DHR-003` | `BR089-DSR-013` | `BR082-EPR-013` | `ktc_ess` | 108 | `stay_hold_no_low_shape_on_selected_raw_days` | 0 | 0 | 1 | 0 |
| `BR091-DHR-004` | `BR089-DSR-014` | `BR082-EPR-014` | `ktc_ess` | 49 | `stay_hold_weak_or_sparse_shape` | 1 | 0 | 1 | 0 |
| `BR091-DHR-005` | `BR089-DSR-015` | `BR082-EPR-015` | `ktc_ess` | 49 | `stay_hold_current_limited_shape` | 2 | 0 | 2 | 0 |
| `BR091-DHR-006` | `BR089-DSR-016` | `BR082-EPR-016` | `ktc_ess` | 49 | `stay_hold_current_limited_shape` | 3 | 0 | 3 | 0 |

## Interpretation
- None of the 6 deferred durable holds provides repeated voltage-low/current-preserved raw support.
- The two `conalog` holds remain AE/recovery context without repeated raw low-shape support on selected days.
- `BR089-DSR-013` has broad signal context but still lacks repeated raw low-shape support.
- `BR089-DSR-014` has only sparse/weak low-shape support and cannot support positive truth.
- `BR089-DSR-015` and `BR089-DSR-016` are better read as current-limited/current-axis holds, not voltage-preserved precursor positives.
- Therefore BR-091 does not add positive truth rows and does not reopen threshold tuning.

## Safety Boundary
- BR-091 is a raw-shape evidence review only.
- It does not convert holds into positives or negatives.
- It does not approve threshold tuning.
- It does not approve direct `panel_day_engine.py` edits.
- Runtime and operator-facing outputs are unchanged.

## Ordered Next Path
1. Keep these 6 rows as holds, not positive replay rows.
2. Search for additional positive voltage-preserved durable precursor truth outside these holds.
3. Track current-limited/current-axis morphology as a separate subtype backlog, not as the BR-090 voltage-preserved threshold lane.
4. Re-run BR-090 only after additional independent positive truth rows exist.
5. Keep direct engine edits blocked until replay evidence and BR-076 prepatch gates both pass.

## Decision
- Accept BR-091 as closing the immediate “can we salvage the 6 holds as voltage-preserved positives?” question with answer `no`.
- Preserve current-limited morphology as a separate evidence lane.
- Continue positive truth expansion elsewhere before any threshold tuning discussion.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_durable_hold_raw_shape_review_v1.py research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py
python3 research/prognostics/build_panel_day_engine_durable_hold_raw_shape_review_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/panel_day_engine_durable_hold_raw_shape_review_br091_check
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

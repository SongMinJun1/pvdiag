<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_089_EPISODE_TRUTH_DURABLE_SHAPE_REVIEW_V1

## Purpose
- Implement the next safe step after BR-088: inspect the 7 deferred durable precursor rows with panel-day shape evidence.
- Carry forward BR-088 source-backed negative counterexamples.
- Add a positive precursor truth label only where the durable window has strong, repeatable, voltage-low/current-preserved morphology plus a hard anchor and no common-cause overlap.
- Keep this branch truth-input/evidence-only:
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_v1.csv` | BR-088 conservative adjudication |
| `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv` | panel-day shape metrics for durable windows |
| `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.csv` | BR-082 packet consumed by BR-084 rebuild |
| `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.json` | BR-083 direction guard consumed by BR-084 rebuild |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_review_input_mixed_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_v1.json`
- BR-084 mixed rebuild check:
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv`
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check/panel_day_engine_reviewed_episode_truth_rows_summary_v1.csv`
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check/panel_day_engine_reviewed_episode_truth_rows_v1.json`

## Positive Fill Criteria
| criterion | threshold | reason |
| --- | ---: | --- |
| `window_day_rows` | `>=14` | avoid one-day episode promotion |
| `event_A_days` | `>=10` | require repeated abnormal days |
| `low_mid_days` | `>=10` | require persistent output-ratio depression |
| `voltage_low_current_ok_days` | `>=10` | require voltage-axis morphology rather than generic low production |
| `hard_anchor_days` | `>=1` | tie the precursor window to a later strict/current fault anchor |
| `common_cause_days` | `0` | block panel-local promotion when subgroup/common-cause overlap exists |
| `data_bad_days` | `<= max(1, 5% of window)` | avoid data-quality artifacts |
| `median_signal_mid_v_ratio` | `<0.75` | confirm the voltage-low shape on signal days |
| `median_signal_mid_i_ratio` | `>=0.85` | confirm current is preserved enough for the voltage-axis family |

## Real Result
- durable shape review rows: `16`
- mixed review input rows: `16`
- carried-forward negative counterexamples: `9`
- filled positive precursor truth rows: `1`
- deferred durable shape holds: `6`
- threshold replay input candidate rows: `10`
- threshold tuning approved: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Decision Counts
| shape review decision | rows |
| --- | ---: |
| `carry_forward_negative_counterexample` | 9 |
| `defer_durable_shape_hold` | 6 |
| `fill_positive_durable_voltage_precursor` | 1 |

## Positive Seed
| shape row | truth row | packet row | site | panel | gap | event_A | low_mid | voltage_low_current_ok | hard_anchor | common_cause | data_bad | median_v | median_i |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `BR089-DSR-010` | `BR084-RTR-010` | `BR082-EPR-010` | `conalog` | `7f7dd654-2760-4eb2-a197-3ebb72b85cda.2.0` | 20 | 21 | 21 | 20 | 1 | 0 | 1 | 0.649982 | 0.976792 |

## Durable Holds
| shape row | truth row | packet row | site | panel | gap | event_A | low_mid | voltage_low_current_ok | hard_anchor | common_cause | hold reason |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `BR089-DSR-011` | `BR084-RTR-011` | `BR082-EPR-011` | `conalog` | `45dfa600-79b7-428e-95d3-22345a068986.1.0` | 54 | 5 | 0 | 0 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |
| `BR089-DSR-012` | `BR084-RTR-012` | `BR082-EPR-012` | `conalog` | `45dfa600-79b7-428e-95d3-22345a068986.1.1` | 75 | 4 | 0 | 0 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |
| `BR089-DSR-013` | `BR084-RTR-013` | `BR082-EPR-013` | `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.0.17` | 108 | 5 | 0 | 1 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |
| `BR089-DSR-014` | `BR084-RTR-014` | `BR082-EPR-014` | `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.12` | 49 | 4 | 2 | 0 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |
| `BR089-DSR-015` | `BR084-RTR-015` | `BR082-EPR-015` | `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.13` | 49 | 3 | 2 | 0 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |
| `BR089-DSR-016` | `BR084-RTR-016` | `BR082-EPR-016` | `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9.1.16` | 49 | 6 | 3 | 0 | 1 | 0 | durable evidence exists, but it does not meet the strong voltage-preserved rule |

## BR-084 Mixed Rebuild Check
- Rebuilding BR-084 with `panel_day_engine_episode_truth_review_input_mixed_v1.csv` produced:
  - reviewed truth rows: `16`
  - `reviewed_negative`: `9`
  - `reviewed_positive`: `1`
  - `needs_evidence`: `6`
  - `negative_counterexample`: `9`
  - `positive_precursor_truth`: `1`
  - `unassigned`: `6`
  - reviewer truth labels assigned: `10`
  - threshold replay ready rows: `10`
  - BR-083 fail count: `0`
  - BR-083 P0 fail count: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`

## Interpretation
- `BR082-EPR-010` is the only BR-089 positive seed because it has repeated event days, persistent low `mid_ratio`, voltage-low/current-preserved shape, a later hard anchor, no common-cause overlap, and low data-bad count.
- The two remaining `conalog` durable holds have AE/re-drop context, but not enough low-mid or voltage-low/current-preserved days under this rule.
- The four `ktc_ess` durable holds have hard-anchor context, but their durable window is not yet a repeatable voltage-preserved precursor shape under this rule.
- Therefore BR-089 creates a pilot mixed truth input, not a production threshold patch.

## Safety Boundary
- BR-089 has positive and negative replay candidates, but support is still tiny and pilot-only.
- Threshold tuning remains `0` because one positive seed cannot justify generalized subtype thresholds.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.
- Runtime and operator-facing outputs are unchanged.

## Ordered Next Path
1. Use the mixed BR-089 review input to run a pilot subtype-threshold replay review.
2. Treat the pilot replay as evidence quality assessment only.
3. Inspect the 6 durable holds with raw waveform or independent family-shape evidence before adding more positives.
4. Keep direct engine edits blocked until replay evidence and BR-076 prepatch gates both pass.

## Decision
- Accept the 1 shape-backed positive precursor truth seed.
- Carry forward the 9 BR-088 source-backed negative counterexamples.
- Keep the remaining 6 durable rows as evidence holds.
- Do not approve threshold tuning or direct runtime changes from BR-089 alone.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check
python3 research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check --review-input /private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_review_input_mixed_v1.csv
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

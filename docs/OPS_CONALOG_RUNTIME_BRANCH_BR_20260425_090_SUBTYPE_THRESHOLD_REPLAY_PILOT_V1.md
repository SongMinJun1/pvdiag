<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_090_SUBTYPE_THRESHOLD_REPLAY_PILOT_V1

## Purpose
- Implement the next safe step after BR-089: replay fixed subtype-threshold candidates against the mixed truth input.
- Evaluate two things separately:
  - labeled performance on 1 positive + 9 negative replay rows
  - deferred-hold pressure on 6 still-unassigned durable rows
- Keep this branch pilot/evidence-only:
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_subtype_threshold_replay_pilot_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_subtype_threshold_replay_pilot_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_durable_shape_review_br089_check/panel_day_engine_episode_truth_durable_shape_review_v1.csv` | BR-089 shape review and truth-candidate metrics |
| `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br089_mixed_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv` | BR-084 mixed reviewed truth rows |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_THRESHOLD_CANDIDATE_V1.csv` | BR-017 threshold candidate axes for provenance |

## Outputs
- `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_cases_v1.csv`
- `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_summary_v1.csv`
- `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_note_v1.md`
- `/private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check/panel_day_engine_subtype_threshold_replay_pilot_v1.json`

## Real Result
- replay case rows: `112`
- summary rows: `7`
- positive truth rows: `1`
- negative truth rows: `9`
- deferred hold rows: `6`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Rule Replay Summary
| rule_id | axis | TP | FP | FN | hold hits | positive hit rate | negative hit rate | hold pressure | pilot decision |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `duration_gap_any_signal_2d` | `duration+gap` | 1 | 0 | 0 | 6 | 1.0 | 0.0 | 1.0 | `blocked_hold_pressure_and_insufficient_support` |
| `duration_gap_eventA_2d` | `duration+gap` | 1 | 0 | 0 | 6 | 1.0 | 0.0 | 1.0 | `blocked_hold_pressure_and_insufficient_support` |
| `severity_gap_low_mid_2d` | `severity+gap` | 1 | 0 | 0 | 3 | 1.0 | 0.0 | 0.5 | `blocked_hold_pressure_and_insufficient_support` |
| `severity_gap_low_mid_10d` | `severity+gap` | 1 | 0 | 0 | 0 | 1.0 | 0.0 | 0.0 | `pilot_candidate_collect_more_positive_truth` |
| `voltage_preserved_gap_vlow_iok_2d` | `voltage-preserved-shape` | 1 | 0 | 0 | 0 | 1.0 | 0.0 | 0.0 | `pilot_candidate_collect_more_positive_truth` |
| `voltage_preserved_gap_vlow_iok_10d` | `voltage-preserved-shape` | 1 | 0 | 0 | 0 | 1.0 | 0.0 | 0.0 | `pilot_candidate_collect_more_positive_truth` |
| `br089_strong_voltage_seed_rule` | `voltage-preserved-shape` | 1 | 0 | 0 | 0 | 1.0 | 0.0 | 0.0 | `pilot_candidate_collect_more_positive_truth` |

## Interpretation
- Labeled-only metrics are not enough here because the labeled set has only `1` positive row.
- Broad duration/event rules look clean on labeled rows, but they trigger all `6` deferred durable holds. That is exactly the ambiguity we wanted the replay to expose.
- The `severity_gap_low_mid_2d` rule is also too broad because it triggers `3` deferred `ktc_ess` holds.
- The clean pilot candidates are:
  - `severity_gap_low_mid_10d`
  - `voltage_preserved_gap_vlow_iok_2d`
  - `voltage_preserved_gap_vlow_iok_10d`
  - `br089_strong_voltage_seed_rule`
- These clean candidates are not approved thresholds. They only identify where to collect more positive truth.
- Among the clean candidates, the voltage-preserved family is the better next evidence direction because it is more physically specific than generic low-mid severity.

## Safety Boundary
- BR-090 does not approve threshold tuning.
- One positive truth row cannot support generalized subtype thresholds.
- Deferred hold hits are treated as ambiguity pressure, not as hidden positives.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.
- Runtime and operator-facing outputs are unchanged.

## Ordered Next Path
1. Collect or adjudicate more positive durable precursor truth for voltage-preserved candidates.
2. Inspect the 6 deferred durable holds with raw waveform or independent family-shape evidence.
3. Keep duration/event-only threshold candidates blocked until hold pressure is resolved.
4. Re-run this pilot when positive support reaches at least 3 independent rows.
5. Keep direct engine edits blocked until replay evidence and BR-076 prepatch gates both pass.

## Decision
- Reject broad duration/event-only threshold movement for now because of hold pressure.
- Keep voltage-preserved and stricter severity candidates as evidence-collection targets only.
- Do not approve threshold tuning or direct runtime changes from BR-090.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_subtype_threshold_replay_pilot_v1.py research/prognostics/smoke_test_panel_day_engine_subtype_threshold_replay_pilot_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_subtype_threshold_replay_pilot_v1.py
python3 research/prognostics/build_panel_day_engine_subtype_threshold_replay_pilot_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_subtype_threshold_replay_pilot_br090_check
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

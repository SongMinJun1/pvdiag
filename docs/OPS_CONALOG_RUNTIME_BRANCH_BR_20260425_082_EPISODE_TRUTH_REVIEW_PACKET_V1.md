<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_082_EPISODE_TRUTH_REVIEW_PACKET_V1

## Purpose
- Implement the BR-081 next action: build `panel_day_engine_episode_truth_review_packet_v1`.
- Convert the BR-081 episode truth map into a smaller reviewer packet.
- Start with the highest-risk interpretive buckets:
  - `long_gap_backdating_hold`
  - `strict_anchor_sudden_review`
  - `durable_precursor_candidate_review`
- Collapse duplicate source lenses so reviewers handle one episode once while still seeing all source ids.
- Keep this branch review-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_review_packet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_v1.csv` | BR-081 episode truth map |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.json`

## Real Result
- input episode map rows: `244`
- selected source lens rows: `22`
- review packet rows: `16`
- summary rows: `3`
- action rows: `5`
- collapsed duplicate lens rows: `6`
- reviewer truth labels assigned: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Review Track Summary
| review track | priority | packet rows | source lens rows | duplicate lens collapsed | reading |
| --- | --- | ---: | ---: | ---: | --- |
| `long_gap_backdating_review` | `P0` | 6 | 12 | 6 | ktc_ess long-gap/G1 rows; decide real precursor vs over-backdated sparse episode |
| `strict_sudden_prior_episode_review` | `P0` | 3 | 3 | 0 | gangui strict-trigger rows; look for defensible prior episode |
| `durable_precursor_review` | `P1` | 7 | 7 | 0 | conalog/ktc_ess recurrent or durable candidates; review before any promotion |

## Important Read
- BR-082 does not assign truth labels. `reviewer_truth_label` is intentionally blank for all rows.
- The G1 duplicate lens is collapsed from 12 source rows to 6 review rows, while `source_artifacts`, `source_case_ids`, and `episode_truth_case_ids` preserve traceability.
- Positive review decisions become threshold replay inputs only.
- Negative review decisions become counterexamples or hold evidence.
- Common-cause and recovery/recurrence buckets remain held outside this first packet.

## Ordered Next Path
1. Fill review evidence for the 16 BR-082 rows.
2. Convert reviewed labels into `panel_day_engine_reviewed_episode_truth_rows_v1`.
3. Build separate common-cause and recovery/recurrence packets if needed.
4. Run subtype-conditioned threshold replay only after reviewed episode truth rows exist.
5. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-082 as the current review packet for precursor-vs-abrupt/backdating interpretation.
- Use BR-082 before changing thresholds or event semantics.
- The next safest implementation is `panel_day_engine_reviewed_episode_truth_rows_v1`, or a manual evidence-fill pass over BR-082 if field/source evidence is available.
- BR-082 does not approve threshold tuning, semantic loosening, operator-facing precursor promotion, or direct engine edits.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_review_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_review_packet_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_review_packet_br082_check
```

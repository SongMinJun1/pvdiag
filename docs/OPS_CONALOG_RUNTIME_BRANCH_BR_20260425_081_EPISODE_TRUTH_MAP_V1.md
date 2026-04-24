<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_081_EPISODE_TRUTH_MAP_V1

## Purpose
- Implement the BR-080 next action: build `panel_day_engine_episode_truth_map_v1`.
- Convert scattered day/panel candidate evidence into an episode-level truth review map.
- Separate durable precursor candidates from one-day episodes, long-gap backdating, strict-sudden anchors, recovery-only observations, and common-cause/group episodes.
- Keep this branch truth-review-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_map_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_map_v1.py`

## Inputs
| input | role |
| --- | --- |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv` | episode shadow row universe |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv` | dedicated G1 long-gap/backdating lens |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_023_BLOCKER_DETAIL_REVIEW_PACKET_V1.csv` | blocker/common-cause detail packet |
| `/private/tmp/local_morphology_family_shape_review_check/panel_day_engine_local_morphology_family_shape_review_v1.csv` | local morphology shape context |
| `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br080_check/panel_day_engine_subtype_truth_expansion_backlog_v1.csv` | subtype truth requirements from BR-080 |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_map_br081_check/panel_day_engine_episode_truth_map_v1.json`

## Real Result
- episode truth map rows: `244`
- summary rows: `10`
- action rows: `5`
- truth status: `truth_pending=244`
- missing optional inputs: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Bucket Summary
| episode truth bucket | rows | reading |
| --- | ---: | --- |
| `common_cause_or_group_episode_hold` | 205 | site/root/group synchrony or blocker context; do not read as panel-local precursor |
| `recovery_recurrence_observation` | 12 | recurrence/recovery morphology; observation until tied to a fault-family truth row |
| `long_gap_backdating_hold` | 12 | G1 long-gap/backdating review rows; keep as hold unless prior signal chain is proven |
| `durable_precursor_candidate_review` | 7 | plausible precursor candidates, but still manual review before promotion |
| `episode_truth_requirement` | 5 | subtype truth requirements that need episode evidence before threshold replay |
| `strict_anchor_sudden_review` | 3 | strict-trigger anchored cases; no precursor promotion without prior episode proof |

## Source Summary
| source | rows | important read |
| --- | ---: | --- |
| `br017_episode_shadow` | 145 | main episode shadow universe |
| `br017_g1_longgap_cases` | 7 | dedicated G1 lens; 6 long-gap rows plus 1 common-cause hold row |
| `br023_blocker_detail_packet` | 77 | common-cause/blocker review packet |
| `br065_local_shape_review` | 10 | local morphology rows, mostly recovery/recurrence observation |
| `br080_subtype_truth_backlog` | 5 | subtype rows requiring episode truth before threshold replay |

## Important Read
- `episode_truth_status` is `truth_pending` for every row.
- `long_gap_backdating_hold` does not prove there was no precursor; it preserves rows where the current fallback may be over-reading a distant or displaced episode.
- `durable_precursor_candidate_review` does not promote a precursor; it creates the row universe where duration, recurrence, family shape, and common-cause exclusion can be reviewed.
- The dedicated G1 input is intentionally kept as a separate duplicate lens. This avoids losing the historical backdating question inside the broader BR-017 episode table.
- Common-cause and strict-proximal flags remain explicit columns even when a row is placed in the long-gap bucket.

## Ordered Next Path
1. Build `panel_day_engine_episode_truth_review_packet_v1` from the BR-081 map.
2. Review long-gap/backdating and strict-sudden rows first.
3. Review durable precursor candidates only after common-cause and recovery-only holds are separated.
4. Build common-cause and recovery/recurrence review packets for held buckets.
5. Only after reviewed episode truth rows exist, open subtype-conditioned threshold replay.
6. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-081 as the current episode truth map.
- Use it as the entry point before asking whether a row was a real precursor, a one-day episode, a long-gap backdating artifact, strict-sudden, or common-cause displacement.
- The next safest implementation is `panel_day_engine_episode_truth_review_packet_v1`.
- BR-081 does not approve threshold tuning, semantic loosening, or direct engine edits.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_map_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_map_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_map_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_map_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_map_br081_check
```

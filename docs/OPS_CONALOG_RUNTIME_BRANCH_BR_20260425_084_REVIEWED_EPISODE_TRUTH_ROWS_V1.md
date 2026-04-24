<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_084_REVIEWED_EPISODE_TRUTH_ROWS_V1

## Purpose
- Implement the next safe step after BR-083: build `panel_day_engine_reviewed_episode_truth_rows_v1`.
- Convert BR-082 review packet rows into a reviewed-truth-row intake table.
- Require BR-083 direction guard to be green before building.
- Keep rows without reviewer evidence as `needs_evidence`; do not invent truth labels.
- Keep this branch truth-intake-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold patch
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.csv` | BR-082 review packet |
| `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.json` | BR-083 green guard |
| optional `--review-input` CSV | manual reviewer labels/evidence paths, absent in this branch run |

## Outputs
- `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv`
- `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_summary_v1.csv`
- `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_note_v1.md`
- `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_v1.json`

## Real Result
- input review packet rows: `16`
- reviewed truth rows: `16`
- review status: `needs_evidence=16`
- truth role: `unassigned=16`
- reviewer truth labels assigned: `0`
- threshold replay ready rows: `0`
- BR-083 fail count: `0`
- BR-083 P0 fail count: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Track Summary
| review track | rows | status | truth role | replay ready |
| --- | ---: | --- | --- | ---: |
| `long_gap_backdating_review` | 6 | `needs_evidence` | `unassigned` | 0 |
| `strict_sudden_prior_episode_review` | 3 | `needs_evidence` | `unassigned` | 0 |
| `durable_precursor_review` | 7 | `needs_evidence` | `unassigned` | 0 |

## Important Read
- BR-084 is progress because it turns the review packet into a structured truth-intake table.
- BR-084 is not evidence completion. There are still no reviewer labels and no replay-ready rows.
- A row only becomes replay-ready when:
  - `reviewer_truth_label` is an accepted positive/negative label, and
  - `reviewer_evidence_path` is present.
- Hold labels and insufficient-evidence labels do not become replay inputs.
- Threshold replay input is still not production authorization.

## Ordered Next Path
1. Attach reviewer evidence paths and labels to BR-084 rows.
2. Rebuild BR-084 with `--review-input`.
3. If positive and negative replay-ready rows exist, build `panel_day_engine_subtype_threshold_replay_v1`.
4. Keep common-cause and insufficient-evidence rows out of replay labels.
5. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-084 as the current reviewed-truth intake table.
- The next safe implementation is evidence attachment, not threshold replay yet.
- BR-084 does not approve threshold tuning, semantic loosening, operator-facing precursor promotion, or direct engine edits.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py research/prognostics/smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py
python3 research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check
```

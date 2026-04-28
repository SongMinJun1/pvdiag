<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_088_EPISODE_TRUTH_CONSERVATIVE_ADJUDICATION_V1

## Purpose
- Implement the next safe step after BR-087: fill only conservative negative counterexample labels that are source-backed.
- Leave possible durable precursor rows unfilled until family-shape continuity and common-cause rejection are proven.
- Rebuild BR-084 with the conservative review input to verify the real truth-row effect.
- Keep this branch negative-adjudication-only:
  - no positive precursor labels
  - no threshold tuning
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_v1.csv` | BR-087 adjudication worksheet |
| `/private/tmp/panel_day_engine_episode_truth_review_packet_br082_check/panel_day_engine_episode_truth_review_packet_v1.csv` | BR-082 packet consumed by BR-084 rebuild |
| `/private/tmp/panel_day_engine_direction_assumption_audit_br083_check/panel_day_engine_direction_assumption_audit_v1.json` | BR-083 direction guard consumed by BR-084 rebuild |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_review_input_conservative_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_conservative_adjudication_v1.json`
- BR-084 rebuild check:
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br088_conservative_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv`
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br088_conservative_check/panel_day_engine_reviewed_episode_truth_rows_summary_v1.csv`
  - `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br088_conservative_check/panel_day_engine_reviewed_episode_truth_rows_v1.json`

## Conservative Fill Criteria
| source group | criteria | filled label |
| --- | --- | --- |
| long-gap backdating | `review_track=long_gap_backdating_review`, `block_precursor_backdating`, `long_gap_one_day_episode_hold`, source gap `>=120d`, evidence card present | `episode_only_or_backdating` |
| strict sudden | `review_track=strict_sudden_prior_episode_review`, `no_precursor_promotion`, `sudden_fault_strict_anchor`, source gap `0d`, `signal_day_count=0`, evidence card present | `strict_sudden_no_precursor` |
| durable precursor | possible precursor rows with no BR-088 family-shape proof | left blank |

## Real Result
- adjudication rows: `16`
- conservative review input rows: `16`
- filled negative labels: `9`
- filled positive labels: `0`
- deferred rows: `7`
- threshold replay input candidate rows from negative labels: `9`
- threshold tuning approved: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Decision Counts
| conservative decision | rows |
| --- | ---: |
| `fill_conservative_negative_long_gap_backdating` | 6 |
| `fill_conservative_negative_strict_sudden` | 3 |
| `defer_positive_or_hold_review` | 7 |

## BR-084 Rebuild Check
- Rebuilding BR-084 with `panel_day_engine_episode_truth_review_input_conservative_v1.csv` produced:
  - reviewed truth rows: `16`
  - `reviewed_negative`: `9`
  - `needs_evidence`: `7`
  - `negative_counterexample`: `9`
  - `unassigned`: `7`
  - reviewer truth labels assigned: `9`
  - threshold replay ready rows: `9`
  - reviewed positive rows: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`
- Important: BR-084 can mark negative rows replay-ready, but BR-088 does not open threshold replay because positive replay rows are still `0`.

## Track And Site Summary
| review track | site | rows | negative labels | positive labels | deferred |
| --- | --- | ---: | ---: | ---: | ---: |
| `long_gap_backdating_review` | `ktc_ess` | 6 | 6 | 0 | 0 |
| `strict_sudden_prior_episode_review` | `gangui` | 3 | 3 | 0 | 0 |
| `durable_precursor_review` | `conalog` | 3 | 0 | 0 | 3 |
| `durable_precursor_review` | `ktc_ess` | 4 | 0 | 0 | 4 |

## Safety Boundary
- BR-088 is a conservative negative-label pass, not a full truth completion.
- Negative-only replay candidates are useful counterexamples, but they are not enough for threshold tuning.
- The 7 durable precursor rows still need family-shape match, same-panel continuity, later strict/current anchor relation, and common-cause rejection before any positive label.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Ordered Next Path
1. Inspect the 7 deferred durable precursor rows at raw/shape level.
2. Attach positive labels only if family-shape, continuity, anchor relation, and common-cause rejection are defensible.
3. Rebuild BR-084 again with a mixed positive/negative review input.
4. Open subtype-conditioned threshold replay only after BR-084 has both positive and negative replay-ready rows.
5. Keep direct engine edits blocked until replay evidence and BR-076 prepatch gates both pass.

## Decision
- Accept the 9 negative rows as source-backed conservative counterexamples for BR-084 review input.
- Do not treat negative-only replay-ready rows as threshold tuning approval.
- Keep the 7 durable rows out of replay until positive evidence is explicitly attached.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check
python3 research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_reviewed_episode_truth_rows_br088_conservative_check --review-input /private/tmp/panel_day_engine_episode_truth_conservative_adjudication_br088_check/panel_day_engine_episode_truth_review_input_conservative_v1.csv
```

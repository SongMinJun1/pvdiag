<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_087_EPISODE_TRUTH_ADJUDICATION_WORKSHEET_V1

## Purpose
- Implement the next safe step after BR-086: compress trace-ready source rows into a human adjudication worksheet.
- Give the reviewer a direction for each packet without assigning `reviewer_truth_label`.
- Keep BR-084 threshold replay blocked until a human fills labels and evidence paths.
- Keep this branch worksheet-only:
  - no truth label assignment
  - no BR-084 replay-ready row creation
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold replay

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_v1.csv` | BR-086 source trace rows |
| `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_index_v1.csv` | BR-085 evidence card/template index |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_review_input_draft_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_adjudication_worksheet_v1.json`

## Real Result
- source trace rows compressed: `22 -> 16`
- worksheet rows: `16`
- draft review input rows: `16`
- trace-ready worksheet rows: `16`
- reviewer truth labels assigned: `0`
- reviewer evidence paths filled: `0`
- threshold replay ready rows: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Suggested Direction Counts
| suggested direction | rows | intended read |
| --- | ---: | --- |
| `negative_or_hold_candidate` | 6 | long-gap one-day backdating cases need negative/hold review before any positive label |
| `strict_sudden_negative_candidate` | 3 | strict sudden anchor cases need prior-episode proof before any positive label |
| `manual_positive_or_hold_candidate` | 7 | durable precursor cases may be positive, but only after same-family continuity and common-cause rejection are proven |

## Track And Site Summary
| review track | site | worksheet rows | source refs | trace-ready rows | direction |
| --- | --- | ---: | ---: | ---: | --- |
| `durable_precursor_review` | `conalog` | 3 | 3 | 3 | `manual_positive_or_hold_candidate` |
| `durable_precursor_review` | `ktc_ess` | 4 | 4 | 4 | `manual_positive_or_hold_candidate` |
| `long_gap_backdating_review` | `ktc_ess` | 6 | 12 | 6 | `negative_or_hold_candidate` |
| `strict_sudden_prior_episode_review` | `gangui` | 3 | 3 | 3 | `strict_sudden_negative_candidate` |

## BR-084 Reverse Check
- The BR-087 draft review input was intentionally left blank.
- Rebuilding BR-084 with that unfilled draft produced:
  - reviewed truth rows: `16`
  - review status counts: `needs_evidence=16`
  - truth role counts: `unassigned=16`
  - reviewer truth labels assigned: `0`
  - threshold replay ready rows: `0`
  - operator-facing change allowed sum: `0`
  - engine patch allowed sum: `0`
  - threshold patch allowed sum: `0`
- This confirms BR-087 guidance alone does not become replay input.

## Safety Boundary
- `suggested_review_direction` is not a truth label.
- The draft input intentionally leaves `reviewer_truth_label`, `reviewer_evidence_path`, and `reviewer_notes` blank.
- `negative_or_hold_candidate` means the row is likely a counterexample/hold candidate, not an automatically assigned negative label.
- `manual_positive_or_hold_candidate` means the row is worth human review, not a positive precursor label.
- Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Ordered Next Path
1. Manually inspect the 16 worksheet rows with the BR-085 evidence cards and BR-086 trace rows.
2. Fill a copy of `panel_day_engine_episode_truth_review_input_draft_v1.csv` only where the label and evidence path are defensible.
3. Rebuild BR-084 with the filled review input.
4. Open subtype-conditioned threshold replay only after BR-084 has positive and negative replay-ready rows.
5. Keep hold/common-cause/insufficient-evidence rows out of replay labels.

## Decision
- Treat BR-087 as the current adjudication worksheet over the BR-085/BR-086 evidence stack.
- Do not use BR-087 suggested directions as automatic truth labels.
- Do not open threshold replay from BR-087 alone.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check
python3 research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_reviewed_episode_truth_rows_br087_unfilled_draft_check --review-input /private/tmp/panel_day_engine_episode_truth_adjudication_worksheet_br087_check/panel_day_engine_episode_truth_review_input_draft_v1.csv
```

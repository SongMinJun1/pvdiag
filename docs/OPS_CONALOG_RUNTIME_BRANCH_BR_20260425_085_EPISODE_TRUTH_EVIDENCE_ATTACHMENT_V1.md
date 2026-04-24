<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_085_EPISODE_TRUTH_EVIDENCE_ATTACHMENT_V1

## Purpose
- Implement the next safe step after BR-084: package each `needs_evidence` truth row into a reviewer-facing evidence card.
- Produce a BR-084-compatible review input template.
- Keep labels and evidence paths intentionally blank until a reviewer fills them.
- Keep this branch evidence-packaging-only:
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold replay
  - no release regeneration

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_reviewed_episode_truth_rows_br084_check/panel_day_engine_reviewed_episode_truth_rows_v1.csv` | BR-084 reviewed truth-row intake table |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_index_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_review_input_template_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_v1.json`
- `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_cards_v1/`

## Real Result
- input rows: `16`
- evidence cards: `16`
- review input template rows: `16`
- summary rows: `4`
- reviewer truth labels assigned: `0`
- reviewer evidence paths filled: `0`
- threshold replay ready rows: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Track And Site Summary
| review track | site | rows | cards | template rows |
| --- | --- | ---: | ---: | ---: |
| `durable_precursor_review` | `conalog` | 3 | 3 | 3 |
| `durable_precursor_review` | `ktc_ess` | 4 | 4 | 4 |
| `long_gap_backdating_review` | `ktc_ess` | 6 | 6 | 6 |
| `strict_sudden_prior_episode_review` | `gangui` | 3 | 3 | 3 |

## Safety Boundary
- `reviewer_truth_label` is intentionally blank in the generated review input template.
- `reviewer_evidence_path` is intentionally blank in the generated review input template.
- The generated evidence card path is a review aid, not automatic proof.
- Passing the unfilled template back into BR-084 must not create replay-ready rows.
- Threshold replay remains blocked until a reviewer explicitly fills accepted positive/negative labels plus evidence paths.

## Important Read
- BR-085 is progress because the 16 review cases now have one evidence card each.
- BR-085 is not truth completion.
- BR-085 is not performance evidence.
- BR-085 is not algorithm authorization.
- The card is designed to reduce confusion: it puts the review question, prove axes, reject axes, source case references, and allowed labels in one place.

## Ordered Next Path
1. Review the 16 BR-085 evidence cards.
2. Fill `panel_day_engine_episode_truth_review_input_template_v1.csv` only where a label is defensible.
3. Use a real evidence path, not just a convenient placeholder, when filling `reviewer_evidence_path`.
4. Rebuild BR-084 with `--review-input`.
5. If BR-084 then has both positive and negative replay-ready rows, open subtype-conditioned threshold replay.
6. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-085 as the current evidence attachment packet for BR-084 rows.
- Do not open threshold replay from BR-085 alone.
- Do not treat card creation as truth-label creation.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_086_EPISODE_TRUTH_SOURCE_TRACE_AUDIT_V1

## Purpose
- Implement the next safe step after BR-085: verify that each evidence card/template row can trace back to concrete source artifact rows.
- Resolve `source_case_ids` such as `br017_episode_shadow:121` to actual CSV rows.
- Confirm source-row identity against site, panel, episode anchor date, and strict trigger date.
- Keep this branch source-trace-only:
  - no truth label assignment
  - no BR-084 replay-ready row creation
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion
  - no threshold replay

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_evidence_attachment_index_v1.csv` | BR-085 card/template index |
| `/private/tmp/panel_day_engine_episode_truth_evidence_attachment_br085_check/panel_day_engine_episode_truth_review_input_template_v1.csv` | BR-085 blank review input template |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_EPISODE_SHADOW_PANEL_V1.csv` | source rows for `br017_episode_shadow:*` |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260423_017_G1_LONGGAP_CASES_V1.csv` | source rows for `br017_g1_longgap_cases:*` |

## Outputs
- `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_note_v1.md`
- `/private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check/panel_day_engine_episode_truth_source_trace_audit_v1.json`

## Real Result
- review rows: `16`
- source references: `22`
- source files existing: `22`
- source rows resolved: `22`
- source identity matches: `22`
- source identity mismatches: `0`
- trace-ready references: `22`
- reviewer truth labels assigned: `0`
- reviewer evidence paths filled: `0`
- threshold replay ready rows: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Track And Site Summary
| review track | site | review rows | source refs | trace-ready refs |
| --- | --- | ---: | ---: | ---: |
| `durable_precursor_review` | `conalog` | 3 | 3 | 3 |
| `durable_precursor_review` | `ktc_ess` | 4 | 4 | 4 |
| `long_gap_backdating_review` | `ktc_ess` | 6 | 12 | 12 |
| `strict_sudden_prior_episode_review` | `gangui` | 3 | 3 | 3 |

## Safety Boundary
- Source trace readiness means the referenced rows are available and identity-matched.
- It does not mean a row is a confirmed real precursor.
- It does not mean a row is a confirmed negative counterexample.
- It does not make BR-084 replay-ready.
- A reviewer must still inspect the trace rows and explicitly fill label/evidence fields before BR-084 can create positive/negative replay rows.

## Important Read
- BR-086 reduces a real risk: label review no longer depends on vague memory of where source rows came from.
- All current BR-085 rows can be traced to source rows, so the next step can be evidence adjudication rather than artifact recovery.
- The safe next artifact is a filled review input template, not a threshold replay.

## Ordered Next Path
1. Inspect the BR-086 trace audit rows together with the BR-085 evidence cards.
2. For each row, decide whether prove/reject axes are actually satisfied.
3. Fill BR-085 review template only for defensible labels and include a real evidence path.
4. Rebuild BR-084 with `--review-input`.
5. Open subtype-conditioned threshold replay only after BR-084 has both positive and negative replay-ready rows.
6. Direct `panel_day_engine.py` algorithm review still requires the BR-076 3-gate prepatch runbook first.

## Decision
- Treat BR-086 as the current source-trace guard for BR-085 evidence attachment.
- Do not use source trace readiness alone as a truth label.
- Do not open threshold replay from BR-086 alone.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py research/prognostics/smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py
python3 research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_episode_truth_source_trace_audit_br086_check
```

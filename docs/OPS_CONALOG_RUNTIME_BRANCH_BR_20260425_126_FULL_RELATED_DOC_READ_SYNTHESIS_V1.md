<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SYNTHESIS_V1

## Purpose
- Record that the related project documents were read as a full corpus, not sampled by memory or a few filenames.
- Connect the numbered BR roadmap with the older project-level design documents.
- Clarify what the full read changes in the current roadmap interpretation.

## Read Scope
| item | count |
| --- | ---: |
| total related files read | `495` |
| markdown files | `427` |
| csv files | `60` |
| json files | `8` |
| total lines read | `41375` |
| total bytes read | `2593150` |
| BR artifacts read | `191` |
| decision logs read | `76` |
| gate docs read | `13` |
| project-level design docs read | `9` |

The full read index is:

- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_INDEX_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.json`

## Main Correction From Full Read
The roadmap cannot be reconstructed from `BR-001..BR-125` alone.

The project already had a separate design spine before and around the runtime BR work:

| design spine | role |
| --- | --- |
| `OPS_PANEL_DAY_ENGINE_PROJECT_EVAL_MATRIX_V1.md` | separates structural coverage, true case metrics, and retrospective proxy metrics |
| `OPS_PANEL_DAY_ENGINE_PROJECT_EVAL_RELIABILITY_AUDIT_V1.md` | prevents small-support perfect F1 from being over-frozen |
| `OPS_PANEL_DAY_ENGINE_PROJECT_EVAL_SUPPORT_GAP_AUDIT_V1.md` | turns weak metric rows into support 5/10 and current-artifact feasibility questions |
| `OPS_PANEL_DAY_ENGINE_PROJECT_TRUTH_EXPANSION_PLAN_V1.md` | converts weak evaluation scopes into concrete collection action classes |
| `OPS_PANEL_DAY_ENGINE_PROJECT_TRUTH_ACQUISITION_BACKLOG_V1.md` | deduplicates truth needs into real collection units |
| `OPS_PANEL_DAY_ENGINE_ALGORITHM_ROLE_GAP_PACK_V1.md` | separates main event-type, kernel-log symptom naming, and GPV reference roles |
| `OPS_PANEL_DAY_ENGINE_PROJECT_HANDOFF_PACK_V1.md` | locks benchmark reset, c429 interpretation split, and support counts |
| `OPS_PANEL_DAY_EVIDENCE_MATRIX_V1.md` | defines row-preserving panel-day evidence foundation |

BR-126 therefore treats these project-level docs as part of the active roadmap evidence base.

## Current Roadmap Interpretation After Full Read
| layer | status after full read |
| --- | --- |
| algorithm/runtime semantics | not algorithm-complete; one narrow G1 raw-only semantics patch exists, most later work is shadow/evidence/gate |
| evaluation method | already designed; metrics must be separated into structural coverage, true case-level metrics, and retrospective proxy metrics |
| reliability/freeze | already designed; small support and proxy rows cannot be treated as stable performance proof |
| truth expansion | already designed; next data need is not vague, it is fault_case / panel_case / site_event / workflow_observation collection |
| MLPE field trial | capture/truth-intake plumbing exists through BR-125, but real reviewed KTC ESS rows remain `0` |
| diagnosis role split | already designed; main algorithm is event-type, kernel-log is symptom/cause-family naming, GPV is external reference |
| production patch readiness | not open from this read alone; engine/threshold/operator approvals remain gated |

## Weak Axes Confirmed By Full Read
The weak axes from BR-126 are still right, but the full read sharpens them:

1. `truth_label_and_episode_ground_truth`
   - This is not just a missing-label problem. It is a collection-unit problem.
   - Use `fault_case`, `panel_case`, `site_event`, and `workflow_observation` units rather than counting target rows repeatedly.

2. `performance_claim_and_result_delta`
   - The project already says not every row should get precision/recall/F1.
   - Any future claim must first say which metric kind it belongs to.

3. `subtype_granularity_and_threshold_calibration`
   - The role-gap pack says final physical root-cause naming is not owned by the main event-type axis alone.
   - Subtype thresholds need truth plus role separation, not only better scoring.

4. `common_cause_vs_panel_local_separation`
   - Existing common-cause docs and BR gates are extensive.
   - This remains a first-class blocker, not a side note.

5. `MLPE_control_vs_panel_physical_fault`
   - MLPE field-trial taxonomy is aligned with the older role-gap principle.
   - Do not collapse optimizer/control, telemetry, and panel physics into one fault family.

6. `handoff_navigation_and_artifact_sprawl`
   - This was not imagined. The read found 495 related docs and 76 decision logs.
   - A full read index is now required for roadmap claims.

## Decision
- Treat BR-126 as a full related-doc read checkpoint, not only a BR-number checkpoint.
- Future answers about "where are we" must start from:
  1. active branch register,
  2. BR-126 full related doc read index,
  3. BR-126 project design corpus,
  4. project eval/reliability/support-gap/truth acquisition docs.
- Do not describe BR-150 as total completion.
- BR-150 should mean the pre-label field-trial runway is ready enough to accept real KTC ESS capture/labels without collapsing truth, common-cause, MLPE-control, and panel-physical meanings.

## Repro Commands
Before read:

```bash
git status --short --branch
find docs -maxdepth 3 -type f \\( -name '*.md' -o -name '*.csv' -o -name '*.json' \\) | sort | wc -l
```

Full read/index command:

```bash
python3 - <<'PY'
# Reads every related docs/root/release markdown/csv/json file and writes:
# docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_INDEX_V1.csv
# docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.csv
# docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FULL_RELATED_DOC_READ_SUMMARY_V1.json
PY
```

After read:

```bash
git diff --check
python3 -m py_compile pv_ae/panel_day_engine.py
```

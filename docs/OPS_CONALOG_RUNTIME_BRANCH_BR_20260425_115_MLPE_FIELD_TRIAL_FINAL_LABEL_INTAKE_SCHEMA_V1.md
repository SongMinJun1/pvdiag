<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_115_MLPE_FIELD_TRIAL_FINAL_LABEL_INTAKE_SCHEMA_V1

## Purpose
- Define the schema for external final labels after BR-114 adjudication packet rows exist.
- Keep reviewer label collection separate from truth intake, threshold tuning, and engine patching.
- Keep this branch schema-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_final_label_intake_schema_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_final_label_intake_schema_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_v1.csv` | BR-114 adjudication packet rows |

## Outputs
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_note_v1.md`
- `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.json`

## Real Result
- template rows: `0`
- schema rows: `16`
- allowed-value rows: `20`
- reviewer-label-attached rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Result
- With one synthetic BR-114 packet row:
  - template rows: `1`
  - reviewer-label-attached rows: `0`
  - truth/threshold/engine approval sums: `0`

## Interpretation
- Current real state has no adjudication packet rows, so no final-label template rows should exist yet.
- The schema is ready for future labels without treating labels as truth automatically.
- Reviewer final fault family/subtype/confidence/clearance fields remain external-review inputs.

## Safety Boundary
- Label intake is not truth intake.
- Filled reviewer labels must pass a later validator and truth gate.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Wait for BR-114 packet rows before collecting labels.
2. When label rows exist, validate required fields and allowed values in BR-116.
3. Only after validation should a separate truth-intake gate consider labels.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_final_label_intake_schema_v1.py research/prognostics/smoke_test_mlpe_field_trial_final_label_intake_schema_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_final_label_intake_schema_v1.py
python3 research/prognostics/build_mlpe_field_trial_final_label_intake_schema_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --packet /private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_v1.csv --output-dir /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check
```

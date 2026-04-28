<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_116_MLPE_FIELD_TRIAL_FINAL_LABEL_VALIDATOR_V1

## Purpose
- Validate filled BR-115 reviewer labels before any truth-intake gate.
- Separate label validity from truth promotion, threshold tuning, and engine patching.
- Keep this branch validator-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv` | reviewer label input/template |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv` | required field/edit-policy schema |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv` | allowed values for reviewer label fields and approval locks |

## Outputs
- `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_note_v1.md`
- `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_v1.json`

## Real Result
- label rows: `0`
- valid label rows: `0`
- validation-failed rows: `0`
- truth-gate candidate rows: `0`
- issue rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke cases:
  - valid reviewer label
  - missing required reviewer subtype
  - invalid allowed value
  - approval flag violation
- Result:
  - label rows: `4`
  - valid label rows: `1`
  - validation-failed rows: `3`
  - truth-gate candidate rows: `1`
  - truth/threshold/engine approval sums: `0`

## Interpretation
- Current real state has no BR-114 adjudication packet rows, so there are no reviewer label rows to validate yet.
- The validator is not over-blocking: a complete reviewer label becomes a truth-gate candidate in smoke.
- The validator is not under-blocking: missing fields, invalid controlled values, and nonzero approval flags all fail.

## Safety Boundary
- `truth_gate_candidate_flag=1` is not truth intake.
- Reviewer labels cannot self-authorize `truth_intake_allowed`, `threshold_patch_allowed`, or `engine_patch_allowed`.
- Valid labels must pass BR-117 truth-intake gating before any replay or algorithm discussion.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep current label validation rows at `0` until BR-114 packet rows exist and external labels are supplied.
2. Use BR-116 whenever a filled BR-115 label CSV arrives.
3. Send only `label_valid_truth_gate_required` rows to BR-117.
4. Keep blocked label rows out of truth, threshold replay, and engine patch workflows.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py
python3 research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --label-input /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv --schema /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv --allowed-values /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv --output-dir /private/tmp/mlpe_field_trial_final_label_validator_br116_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_122_MLPE_FIELD_TRIAL_TRUTH_SEED_REVIEWER_DECISION_VALIDATOR_V1

## Purpose
- Validate filled BR-121 reviewer decision rows before any future truth-intake candidate package.
- Separate three roles that must not be confused:
  - reviewer decision completeness
  - future truth-intake candidate eligibility
  - canonical truth / threshold / engine write authorization
- Keep this branch validator-only:
  - no canonical truth writes
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_template_v1.csv` | BR-121 reviewer decision template |
| `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv` | BR-121 required-field schema |
| `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv` | BR-121 allowed-value schema |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.json`

## Real Result
- decision rows: `0`
- valid decision rows: `0`
- validation-failed rows: `0`
- future truth-intake candidate rows: `0`
- issue rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Synthetic decision rows: `7`
- Valid decision rows: `3`
- Validation-failed rows: `4`
- Future truth-intake candidate rows: `1`
- Issue rows: `5`
- canonical truth/truth intake/threshold/engine approval sums: `0`

## Interpretation
- Current real state still has no filled KTC ESS reviewer decisions, so no truth-intake candidate is produced.
- The smoke matrix proves both sides of the gate:
  - a fully confirmed `approve_for_future_truth_intake` row can become a sidecar candidate
  - weak approval, missing reviewer, bad allowed value, and write-approval flag violations fail closed
- `issue_rows` can be larger than `validation_failed_rows`, because a single failed decision row can violate more than one policy. In the smoke matrix, the bad approval row violates both the allowed-value schema and the explicit no-write approval guard.

## Safety Boundary
- A validated future truth-intake candidate is still not canonical truth.
- All write/approval fields remain locked to `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-122 as the validator for any filled BR-121 reviewer decision sheet.
2. When real KTC ESS reviewer decisions exist, run BR-122 first and inspect validation issues.
3. Only validated `approve_for_future_truth_intake` rows may enter a later sidecar truth-intake candidate package.
4. The next package must still be sidecar-only and must not write canonical truth directly.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --decision-input /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_template_v1.csv --schema /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv --allowed-values /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check
```

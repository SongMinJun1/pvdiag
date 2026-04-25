<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_125_MLPE_FIELD_TRIAL_TRUTH_INTAKE_PREFLIGHT_REVIEW_VALIDATOR_V1

## Purpose
- Validate reviewed BR-124 truth-intake preflight checklist rows.
- Require all six required checklist items to be present and passed before a row can become a later materialization-precheck candidate.
- Keep this branch validator-only:
  - no canonical truth writes
  - no truth-intake write approval
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_v1.csv` | BR-124 preflight rows |
| `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_checklist_v1.csv` | reviewed BR-124 checklist rows |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_validation_v1.json`

## Real Result
- reviewed preflight rows: `0`
- all-checks-passed rows: `0`
- future truth materialization precheck candidate rows: `0`
- validation-failed rows: `0`
- issue rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Synthetic reviewed preflight rows: `4`
- All-checks-passed rows: `1`
- Future truth materialization precheck candidate rows: `1`
- Validation-failed rows: `3`
- Issue rows: `3`
- canonical truth/truth intake/threshold/engine approval sums: `0`

## Validation Contract
- A row passes only when all six BR-124 required checks are present and passed:
  - `BR124-CHECK-001` exact source trace confirmed
  - `BR124-CHECK-002` independent evidence attached
  - `BR124-CHECK-003` common-cause final clearance confirmed
  - `BR124-CHECK-004` measurement-artifact final clearance confirmed
  - `BR124-CHECK-005` counterexample final clearance confirmed
  - `BR124-CHECK-006` truth write boundary reviewed
- Missing checks, duplicate checks, invalid statuses, failed/unchecked checks, invalid source preflight status, and nonzero source write flags fail closed.
- `future_truth_materialization_precheck_candidate_flag=1` is still not canonical truth approval.

## Interpretation
- Current real state still has no KTC ESS reviewed preflight rows, so no materialization-precheck candidate rows are produced.
- The smoke matrix proves this validator narrows the path:
  - one complete reviewed checklist passes
  - one missing-check row fails
  - one failed-check row fails
  - one source write-flag violation fails
- Passing BR-125 means only “eligible for a later explicit materialization precheck,” not “write to truth.”

## Safety Boundary
- Validation output rows are not canonical truth rows.
- All write/approval fields remain locked to `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-125 as the validator for reviewed BR-124 preflight checklist input.
2. When real checklist rows exist, run BR-124, then BR-125.
3. If BR-125 emits materialization-precheck candidates, build the next branch as a source/evidence materialization precheck package.
4. Keep final canonical truth materialization blocked until a separate branch proves source trace, evidence files, reviewer sign-off, and write boundary again.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --preflight /private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_v1.csv --reviewed-checklist /private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_checklist_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check
```

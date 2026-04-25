<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_123_MLPE_FIELD_TRIAL_FUTURE_TRUTH_INTAKE_CANDIDATE_PACKAGE_V1

## Purpose
- Package only BR-122 validated reviewer approvals into a sidecar future truth-intake candidate table.
- Keep failed, rejected, deferred, incomplete, and write-flag-violating decision rows out of the candidate package.
- Keep this branch package-only:
  - no canonical truth writes
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.csv` | BR-122 reviewer decision validation output |
| `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_issues_v1.csv` | BR-122 validation issue table |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_blocked_rows_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.json`

## Real Result
- source decision rows: `0`
- source valid decision rows: `0`
- source validation-failed rows: `0`
- source future truth-intake candidate rows: `0`
- candidate package rows: `0`
- blocked before candidate package rows: `0`
- source issue rows: `0`
- source write-flag violation rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Synthetic source decision rows: `5`
- Source valid decision rows: `4`
- Source validation-failed rows: `1`
- Source future truth-intake candidate rows: `2`
- Candidate package rows: `1`
- Blocked before candidate package rows: `4`
- Source issue rows: `2`
- Source write-flag violation rows: `1`
- canonical truth/truth intake/threshold/engine approval sums: `0`

## Interpretation
- Current real state still has no filled KTC ESS reviewer decisions, so no future truth-intake candidate package rows are produced.
- The smoke matrix proves that BR-123 is a narrowing package, not a new decision maker:
  - one fully validated `approve_for_future_truth_intake` row enters the package
  - reject, defer, validation failure, and source write-flag violation rows are blocked
- BR-123 defensively rechecks source write flags even though BR-122 should already block them. This keeps the package safe if a malformed validation table is supplied.

## Safety Boundary
- Candidate package rows are not canonical truth rows.
- Candidate package rows do not authorize threshold replay or engine patches.
- All write/approval fields remain locked to `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-123 as the sidecar candidate package builder for any validated BR-122 reviewer decisions.
2. When real KTC ESS reviewer decisions exist, run BR-122 first, then BR-123.
3. If BR-123 produces candidate rows, build the next branch as an explicit truth-intake preflight/checklist, not a canonical truth writer.
4. Keep final canonical truth materialization blocked until a separate branch proves exact source trace, evidence clearance, and approval boundaries.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --validation /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_v1.csv --issues /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_validator_br122_check/mlpe_field_trial_truth_seed_reviewer_decision_validation_issues_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check
```

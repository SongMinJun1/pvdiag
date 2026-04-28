<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_127_SOURCE_EVIDENCE_MATERIALIZATION_PREFLIGHT_V1

## Purpose
- Build the source/evidence materialization precheck after BR-125 reviewed-preflight validation.
- Require source trace, independent evidence, common-cause clearance, measurement-artifact clearance, counterexample clearance, and write-boundary evidence before a row can enter a later sidecar truth package.
- Keep this branch precheck-only:
  - no canonical truth writes
  - no truth-intake write approval
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_materialization_precheck_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_materialization_precheck_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_validation_v1.csv` | BR-125 reviewed-preflight validation rows |
| `/private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_issues_v1.csv` | BR-125 reviewed-preflight issues |
| optional materialization evidence manifest | source/evidence/clearance/write-boundary materialization evidence; required once BR-125 candidate rows exist |

## Evidence Manifest Contract
Required columns:

- `trial_event_id`
- `evidence_group`
- `evidence_path`
- `materialization_required_flag`
- `evidence_exists_flag`
- `reviewer_signed_flag`
- `evidence_note`

Required groups for each candidate:

- `source_trace`
- `independent_evidence`
- `common_cause_clearance`
- `measurement_artifact_clearance`
- `counterexample_clearance`
- `write_boundary_review`

Each required group must have at least one row with:

- `evidence_path` non-empty
- `materialization_required_flag = 1`
- `evidence_exists_flag = 1`
- `reviewer_signed_flag = 1`

## Outputs
- `/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check/mlpe_field_trial_truth_materialization_precheck_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check/mlpe_field_trial_truth_materialization_precheck_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check/mlpe_field_trial_truth_materialization_precheck_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check/mlpe_field_trial_truth_materialization_precheck_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check/mlpe_field_trial_truth_materialization_precheck_v1.json`

## Real Result
- source review validation rows: `0`
- materialization precheck passed rows: `0`
- future sidecar truth package candidate rows: `0`
- blocked rows: `0`
- issue rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Synthetic source review validation rows: `4`
- Materialization precheck passed rows: `1`
- Future sidecar truth package candidate rows: `1`
- Blocked rows: `3`
- Issue rows: `3`
- canonical truth/truth intake/threshold/engine approval sums: `0`

## Interpretation
- Current real state still has no BR-125 materialization-precheck candidate rows, so no sidecar truth package candidates are produced.
- The smoke matrix proves this branch narrows the path:
  - one fully reviewed and fully materialized evidence row passes as sidecar-package candidate only
  - one missing-evidence row fails
  - one failed BR-125 source row fails
  - one source write-flag violation fails
- Passing BR-127 means only “eligible for a later sidecar truth package,” not “write to truth.”

## Safety Boundary
- Precheck rows are not canonical truth rows.
- Evidence manifest rows are not approval rows unless every required group is present, existing, and reviewer signed.
- All write/approval fields remain locked to `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-127 as the source/evidence materialization precheck.
2. When real reviewed preflight rows and evidence manifest rows exist, run BR-125, then BR-127.
3. If BR-127 emits sidecar-package candidates, build the next branch as a sidecar truth package, not a canonical truth writer.
4. Keep final canonical truth materialization blocked until a separate write-boundary branch proves no conflicts and receives explicit approval.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_materialization_precheck_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_materialization_precheck_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_materialization_precheck_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_materialization_precheck_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --review-validation /private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_validation_v1.csv --review-issues /private/tmp/mlpe_field_trial_truth_intake_preflight_review_validator_br125_check/mlpe_field_trial_truth_intake_preflight_review_issues_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_materialization_precheck_br127_check
```

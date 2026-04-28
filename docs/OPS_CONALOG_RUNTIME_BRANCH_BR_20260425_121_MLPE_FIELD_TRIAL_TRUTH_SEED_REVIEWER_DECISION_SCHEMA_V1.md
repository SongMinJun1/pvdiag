<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_121_MLPE_FIELD_TRIAL_TRUTH_SEED_REVIEWER_DECISION_SCHEMA_V1

## Purpose
- Define the reviewer decision schema for BR-120 sidecar truth-seed review packet rows.
- Require explicit reviewer fields before any future truth-intake discussion:
  - reviewer decision
  - reviewer confidence
  - independent evidence status
  - common-cause final clearance
  - measurement-artifact final clearance
  - counterexample check status
  - reviewer identity and timestamp
- Keep this branch schema-only:
  - no canonical truth writes
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_v1.csv` | BR-120 sidecar truth-seed review packet |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_template_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_allowed_values_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check/mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.json`

## Real Result
- template rows: `0`
- schema rows: `25`
- allowed-value rows: `27`
- reviewer decision attached rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke chain:
  - BR-119 synthetic label intake
  - BR-120 sidecar packet generation
  - BR-121 reviewer decision schema generation
- Result:
  - template rows: `2`
  - schema rows: `25`
  - allowed-value rows: `27`
  - reviewer decision attached rows: `0`
  - canonical truth/truth intake/threshold/engine approval sums: `0`

## Interpretation
- Current real state still has no real KTC ESS sidecar packet rows, so the real decision template is empty.
- The schema is ready for future packet rows and separates reviewer decision values from any write authorization.
- Even `approve_for_future_truth_intake` is not a canonical truth write. It only prepares a later explicit truth-intake branch.

## Safety Boundary
- Reviewer decisions are controlled values, not direct writes.
- `canonical_truth_write_allowed`, `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-121 as the reviewer decision template/schema for future BR-120 packet rows.
2. When real KTC ESS packet rows exist, fill the BR-121 template with reviewer decisions.
3. Build the next branch as a reviewer decision validator, not a canonical truth writer.
4. Only after validated reviewer decisions exist should a separate sidecar truth-intake candidate package be considered.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --packet /private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_seed_reviewer_decision_schema_br121_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_124_MLPE_FIELD_TRIAL_TRUTH_INTAKE_PREFLIGHT_CHECKLIST_V1

## Purpose
- Create unchecked truth-intake preflight checklist rows for BR-123 sidecar candidate package rows.
- Keep malformed candidate rows and BR-123 blocked carryover rows out of preflight.
- Keep this branch checklist-only:
  - no canonical truth writes
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_checklist_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.csv` | BR-123 sidecar candidate package |
| `/private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_blocked_rows_v1.csv` | BR-123 blocked rows |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_checklist_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_blocked_carryover_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check/mlpe_field_trial_truth_intake_preflight_v1.json`

## Real Result
- source candidate package rows: `0`
- source blocked rows: `0`
- truth-intake preflight rows: `0`
- preflight checklist rows: `0`
- preflight unchecked rows: `0`
- truth-intake preflight ready rows: `0`
- blocked before preflight rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Synthetic candidate package rows: `2`
- Synthetic BR-123 blocked rows: `1`
- Truth-intake preflight rows: `1`
- Preflight checklist rows: `6`
- Preflight unchecked rows: `6`
- Truth-intake preflight ready rows: `0`
- Blocked before preflight rows: `2`
- canonical truth/truth intake/threshold/engine approval sums: `0`

## Checklist Contract
- Each eligible candidate receives 6 unchecked required checks:
  - exact source trace confirmed
  - independent evidence attached
  - common-cause final clearance confirmed
  - measurement-artifact final clearance confirmed
  - counterexample final clearance confirmed
  - truth write boundary reviewed
- `unchecked` means blocked. It is not treated as partial approval.
- BR-124 intentionally does not fill or pass checklist rows. Filling must happen in a later reviewed input branch.

## Interpretation
- Current real state still has no KTC ESS future truth-intake candidate rows, so no preflight checklist rows are produced.
- The smoke matrix proves the branch narrows candidate rows further:
  - a safe candidate row receives preflight/checklist rows
  - a candidate row with nonzero source write flag is blocked
  - BR-123 blocked carryover remains blocked

## Safety Boundary
- Preflight rows are not canonical truth rows.
- Checklist rows are not approval rows.
- All write/approval fields remain locked to `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-124 as the generator for unchecked truth-intake preflight checklists.
2. When real candidate rows exist, run BR-123, then BR-124.
3. If BR-124 emits checklist rows, build the next branch as a reviewed preflight input validator, not a canonical truth writer.
4. Keep final canonical truth materialization blocked until every required preflight check is reviewed and independently validated.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_checklist_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_checklist_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py --repo-root "$(pwd)" --candidate-package /private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.csv --blocked /private/tmp/mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_br123_check/mlpe_field_trial_truth_seed_future_truth_intake_blocked_rows_v1.csv --output-dir /private/tmp/mlpe_field_trial_truth_intake_preflight_checklist_br124_check
```

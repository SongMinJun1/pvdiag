<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_119_MLPE_FIELD_TRIAL_REAL_LABEL_INTAKE_RUNBOOK_V1

## Purpose
- Chain the real-label intake path that will be used when KTC ESS field-trial CSV labels arrive.
- Execute the pre-truth safety sequence in one reproducible run:
  - BR-118 fixture contract check
  - BR-116 final label validation
  - BR-117 label-to-truth gate
  - truth-seed write boundary lock
- Keep this branch runbook-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_real_label_intake_runbook_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv` | current real-label placeholder / future filled KTC ESS label CSV |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv` | BR-115 required-field schema |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv` | BR-115 allowed values and approval locks |

## Outputs
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/mlpe_field_trial_real_label_intake_runbook_v1.csv`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/mlpe_field_trial_real_label_intake_runbook_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/mlpe_field_trial_real_label_intake_runbook_note_v1.md`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/mlpe_field_trial_real_label_intake_runbook_v1.json`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/br118_fixture_contract/`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/br116_real_label_validation/`
- `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/br117_label_to_truth_gate/`

## Real Result
- fixture mismatch rows: `0`
- label rows: `0`
- valid label rows: `0`
- validation-blocked rows: `0`
- truth-gate-ready rows: `0`
- truth-gate-blocked rows: `0`
- truth-seed review candidate rows: `0`
- hard-stop rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke fixture:
  - one confirmed-observed positive with clearances
  - one negative control with clearances
  - one probable label with clearances
- Result:
  - fixture mismatch rows: `0`
  - label rows: `3`
  - valid label rows: `3`
  - validation-blocked rows: `0`
  - truth-gate-ready rows: `2`
  - truth-gate-blocked rows: `1`
  - truth-seed review candidate rows: `2`
  - truth/threshold/engine approval sums: `0`

## Interpretation
- Current real state is still waiting for real KTC ESS label CSV rows.
- The runbook now proves the chain is executable before those labels arrive.
- In smoke, valid labels do not automatically become truth:
  - confirmed positive and negative-control rows become sidecar review candidates
  - probable rows remain blocked by BR-117
- A sidecar review candidate is still not canonical truth, threshold approval, or engine approval.

## Safety Boundary
- `truth_seed_review_candidate_rows` means the row may enter a later sidecar review branch.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-119 as the one-command intake runbook for future KTC ESS label CSVs.
2. When labels arrive, rerun BR-119 with `--label-input <filled_csv>`.
3. Split rows by BR-119 stage output:
   - BR-116 invalid rows go back to label correction
   - BR-117 blocked rows go to blocker resolution
   - BR-117 ready rows go to sidecar truth-seed review only
4. Build the next branch as a truth-seed review packet, not a canonical truth writer.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py research/prognostics/smoke_test_mlpe_field_trial_real_label_intake_runbook_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_real_label_intake_runbook_v1.py
python3 research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py --repo-root "$(pwd)" --label-input /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv --schema /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_schema_v1.csv --allowed-values /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_allowed_values_v1.csv --output-dir /private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check
```

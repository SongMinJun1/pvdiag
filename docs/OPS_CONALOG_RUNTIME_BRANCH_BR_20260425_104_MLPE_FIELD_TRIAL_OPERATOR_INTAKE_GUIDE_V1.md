<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_104_MLPE_FIELD_TRIAL_OPERATOR_INTAKE_GUIDE_V1

## Purpose
- Convert the BR-102 capture template and BR-103 readiness packet into an operator-facing intake guide.
- Make the field-trial team collect the metadata/evidence needed for later adjudication before any final labels exist.
- Keep this branch intake-guide-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_operator_intake_guide_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv` | BR-102 planned capture template |
| `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv` | BR-103 readiness buckets |

## Outputs
- `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_checklist_v1.csv`
- `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_field_guide_v1.csv`
- `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_runbook_v1.md`
- `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_guide_v1.json`

## Real Result
- checklist rows: `14`
- field guide rows: `26`
- planning rows: `14`
- capture cleanup rows: `0`
- adjudication-ready rows: `0`
- truth intake allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Why This Exists
- BR-102 tells us which fields exist.
- BR-103 tells us whether a row is ready.
- BR-104 tells operators what to fill so rows can move from `planned_waiting_for_capture` to `capture_ready_label_pending`.
- This closes a practical gap: without an intake guide, planned rows can be structurally valid but still unclear to field operators.

## Operator Collection Rule
- Fill exact `site`, `root_id`, `panel_id`, `mlpe_device_id`, `start_ts`, `end_ts`, and `injection_strength`.
- Attach `raw_data_path`, `peer_data_path`, and `waveform_slice_path`.
- Attach `weather_data_path` when available.
- Re-check `timestamp_quality` and `communication_quality`; `unchecked` is treated as still needing operator confirmation.
- Leave `final_fault_family`, `final_fault_subtype`, and `final_truth_confidence` blank until final adjudication.

## Safety Boundary
- The checklist is not a truth table.
- `capture_ready_label_pending` is still not a final truth label.
- `truth_intake_allowed`, `operator_promotion_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use BR-104 checklist during MLPE field-trial capture.
2. Re-run BR-103 after capture rows are filled.
3. Only rows that become `capture_ready_label_pending` should move to final adjudication.
4. Do not build final truth rows until actual labels are supplied.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py research/prognostics/smoke_test_mlpe_field_trial_operator_intake_guide_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_operator_intake_guide_v1.py
python3 research/prognostics/build_mlpe_field_trial_operator_intake_guide_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --capture-input /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --readiness-input /private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv --output-dir /private/tmp/mlpe_field_trial_operator_intake_br104_check
```

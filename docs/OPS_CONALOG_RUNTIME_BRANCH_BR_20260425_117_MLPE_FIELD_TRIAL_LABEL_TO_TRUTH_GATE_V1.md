<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_117_MLPE_FIELD_TRIAL_LABEL_TO_TRUTH_GATE_V1

## Purpose
- Gate BR-116-valid reviewer labels before truth intake.
- Require more than a valid label row:
  - confirmed or negative-control truth confidence
  - panel-local common-cause clearance
  - physical/measurement-artifact clearance
- Keep this branch gate-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_label_to_truth_gate_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv` | reviewer label input/template |
| `/private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_v1.csv` | BR-116 label validation output |

## Outputs
- `/private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check/mlpe_field_trial_label_to_truth_gate_v1.csv`
- `/private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check/mlpe_field_trial_label_to_truth_gate_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check/mlpe_field_trial_label_to_truth_gate_note_v1.md`
- `/private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check/mlpe_field_trial_label_to_truth_gate_v1.json`

## Real Result
- label rows: `0`
- truth-gate-ready rows: `0`
- truth-gate-blocked rows: `0`
- positive truth candidate rows: `0`
- negative truth candidate rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke cases:
  - confirmed injected with clearances
  - negative control with clearances
  - probable confidence
  - common-cause not cleared
  - measurement artifact not cleared
  - BR-116 validation failed
- Result:
  - label rows: `6`
  - truth-gate-ready rows: `2`
  - truth-gate-blocked rows: `4`
  - positive truth candidate rows: `1`
  - negative truth candidate rows: `1`
  - truth/threshold/engine approval sums: `0`

## Interpretation
- Current real state has no label rows, so no truth gate candidates exist yet.
- The gate is not over-blocking: confirmed positive and negative-control labels with clearances can pass as candidates.
- The gate is not under-blocking: probable/ambiguous-like confidence, common-cause risk, measurement-artifact risk, and BR-116 validation failures remain blocked.

## Safety Boundary
- `truth_gate_ready_flag=1` is not final truth promotion.
- Ready rows are candidates for the next truth-intake review, not automatic truth seeds.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-117 at 0 rows until BR-114/115/116 produce valid labels.
2. When labels exist, send only `truth_gate_ready_for_truth_intake_review` rows forward.
3. BR-118 should build a synthetic truth-gate fixture/failure matrix before any real truth seed promotion.
4. Keep blocked rows out of replay and algorithm patch workflows.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py research/prognostics/smoke_test_mlpe_field_trial_label_to_truth_gate_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_label_to_truth_gate_v1.py
python3 research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py --repo-root "$(pwd)" --label-input /private/tmp/mlpe_field_trial_final_label_intake_schema_br115_check/mlpe_field_trial_final_label_intake_template_v1.csv --label-validation /private/tmp/mlpe_field_trial_final_label_validator_br116_check/mlpe_field_trial_final_label_validation_v1.csv --output-dir /private/tmp/mlpe_field_trial_label_to_truth_gate_br117_check
```

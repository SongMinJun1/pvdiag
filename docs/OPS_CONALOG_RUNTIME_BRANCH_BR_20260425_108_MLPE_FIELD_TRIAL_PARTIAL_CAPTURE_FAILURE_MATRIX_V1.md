<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_108_MLPE_FIELD_TRIAL_PARTIAL_CAPTURE_FAILURE_MATRIX_V1

## Purpose
- Build a synthetic partial-capture failure matrix for BR-103 readiness and BR-106 handoff guard.
- Confirm that incomplete capture rows block adjudication, complete label-pending rows can hand off, and label-attached rows still require a separate truth gate.
- Keep this branch failure-matrix-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_partial_capture_failure_matrix_v1.py`

## Outputs
- `/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check/mlpe_field_trial_partial_capture_failure_matrix_input_v1.csv`
- `/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check/mlpe_field_trial_partial_capture_expected_buckets_v1.csv`
- `/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check/readiness/mlpe_field_trial_capture_readiness_packet_v1.csv`
- `/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check/guard/mlpe_field_trial_adjudication_handoff_guard_v1.csv`

## Real Result
- scenario rows: `6`
- evidence rows: `25`
- evidence missing rows: `1`
- label-attached rows: `1`
- readiness bucket rows:
  - `planned_waiting_for_capture`: `1`
  - `capture_ready_label_pending`: `1`
  - `capture_metadata_incomplete`: `1`
  - `evidence_paths_missing`: `1`
  - `evidence_files_not_found`: `1`
  - `label_attached_truth_gate_required`: `1`
- guard bucket rows:
  - `blocked_planned_capture`: `1`
  - `adjudication_handoff_ready`: `1`
  - `blocked_readiness_incomplete`: `3`
  - `truth_gate_required_after_label`: `1`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Interpretation
- BR-107 proved the gates can open for complete capture.
- BR-108 proves the gates fail closed for the expected partial-capture failure modes.
- The `label_attached_truth_gate` scenario verifies that labels do not auto-promote to truth intake.

## Safety Boundary
- Synthetic scenarios are plumbing tests, not field truth.
- `truth_gate_required_after_label` still requires a separate truth-intake branch.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-107/108 as paired positive and negative plumbing regression fixtures.
2. Use these fixtures before accepting real capture rows into adjudication.
3. Do not open truth intake until final labels are supplied externally.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py research/prognostics/smoke_test_mlpe_field_trial_partial_capture_failure_matrix_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_partial_capture_failure_matrix_v1.py
python3 research/prognostics/build_mlpe_field_trial_partial_capture_failure_matrix_v1.py --repo-root "$(pwd)" --capture-input /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --output-dir /private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check
```

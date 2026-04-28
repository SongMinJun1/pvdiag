<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_118_MLPE_FIELD_TRIAL_TRUTH_GATE_FIXTURE_MATRIX_V1

## Purpose
- Lock a synthetic pass/fail matrix around the BR-117 label-to-truth gate before any real truth seed promotion.
- Make the gate contract explicit:
  - confirmed injected/observed positive labels can pass only with panel-local and physical clearances
  - negative controls can pass only with the same clearances
  - probable/ambiguous labels, common-cause risk, measurement-artifact risk, BR-116 validation failure, and missing validation all fail closed
- Keep this branch fixture-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_gate_fixture_matrix_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_gate_fixture_matrix_v1.py`

## Outputs
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_labels_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/br117_gate_outputs/mlpe_field_trial_label_to_truth_gate_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_matrix_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_matrix_mismatches_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_matrix_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_matrix_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check/mlpe_field_trial_truth_gate_fixture_matrix_v1.json`

## Fixture Result
- fixture rows: `16`
- case-pass rows: `16`
- mismatch rows: `0`
- expected ready rows: `3`
- actual ready rows: `3`
- expected blocked rows: `13`
- actual blocked rows: `13`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Fixture Groups
| group | rows | ready | blocked | mismatches |
| --- | ---: | ---: | ---: | ---: |
| `pass_ready_candidate` | 3 | 3 | 0 | 0 |
| `block_truth_confidence` | 3 | 0 | 3 | 0 |
| `block_common_cause_clearance` | 3 | 0 | 3 | 0 |
| `block_measurement_artifact_clearance` | 3 | 0 | 3 | 0 |
| `block_label_validation` | 3 | 0 | 3 | 0 |
| `block_missing_validation` | 1 | 0 | 1 | 0 |

## Interpretation
- The BR-117 gate contract is stable on the synthetic matrix.
- The gate is not over-blocking: confirmed positives and negative controls with both clearances pass into truth-intake review candidate state.
- The gate is not under-blocking: uncertain truth confidence, common-cause risk, artifact risk, validation failures, and missing validation fail closed.
- This does not create field truth. It only proves the pre-truth gate behaves as specified before real KTC ESS labels arrive.

## Safety Boundary
- `case_pass_flag=1` means expected gate behavior matched actual gate behavior.
- `truth_gate_ready_flag=1` still means candidate for the next truth-intake review, not final truth seed promotion.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-118 as the regression fixture for BR-117 gate behavior.
2. When real KTC ESS field-trial CSV labels arrive, run BR-115/116/117 and compare against BR-118 fixture expectations.
3. Only rows that pass BR-117 and survive the next truth-intake review can be considered for sidecar truth seed preparation.
4. Keep threshold replay and engine patches blocked until labeled evidence and regression pressure packets both pass.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_gate_fixture_matrix_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_gate_fixture_matrix_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_gate_fixture_matrix_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_gate_fixture_matrix_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --output-dir /private/tmp/mlpe_field_trial_truth_gate_fixture_matrix_br118_check
```

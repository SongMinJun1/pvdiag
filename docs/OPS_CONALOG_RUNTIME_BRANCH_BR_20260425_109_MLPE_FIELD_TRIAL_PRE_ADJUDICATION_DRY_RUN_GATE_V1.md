<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_109_MLPE_FIELD_TRIAL_PRE_ADJUDICATION_DRY_RUN_GATE_V1

## Purpose
- Bundle BR-107 positive plumbing and BR-108 failure-mode plumbing into one pre-adjudication dry-run gate.
- Require the gate to pass before real filled capture rows are accepted for final adjudication workflow.
- Keep this branch dry-run-gate-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- checker:
  - `research/prognostics/check_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check` | positive complete-capture plumbing fixture |
| `/private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check` | partial-capture failure matrix |

## Outputs
- `/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_v1.csv`
- `/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_note_v1.md`
- `/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_v1.json`

## Real Result
- gate rows: `8`
- passed rows: `8`
- failed rows: `0`
- overall passed flag: `1`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Gate Coverage
- BR-107 fixture row count is `14`.
- BR-107 readiness buckets are all `capture_ready_label_pending`.
- BR-107 handoff allowed rows are `14`.
- BR-107 truth intake remains `0`.
- BR-108 expected readiness and guard buckets match.
- BR-108 handoff allowed rows are exactly `1`.
- BR-108 truth intake remains `0`.

## Safety Boundary
- Passing this gate means capture/readiness/handoff plumbing is healthy.
- Passing this gate does not create truth rows.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-109 as the pre-adjudication plumbing gate.
2. Run this gate before real field-capture rows enter final adjudication.
3. Open truth intake only after external final labels are supplied.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/check_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py research/prognostics/smoke_test_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py
python3 research/prognostics/check_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py --repo-root "$(pwd)" --br107-root /private/tmp/mlpe_field_trial_filled_capture_fixture_br107_check --br108-root /private/tmp/mlpe_field_trial_partial_capture_failure_matrix_br108_check --output-dir /private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check
```

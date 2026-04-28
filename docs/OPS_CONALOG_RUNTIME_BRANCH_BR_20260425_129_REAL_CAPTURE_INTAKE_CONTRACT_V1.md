<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_129_REAL_CAPTURE_INTAKE_CONTRACT_V1

## Purpose
- Build the real KTC ESS capture CSV intake contract before the CSV exists.
- Reuse the BR-102 capture schema and controlled vocabulary.
- Keep this branch intake-contract-only:
  - no final labels
  - no truth intake write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_real_capture_intake_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_contract_v1.py`

## Inputs
| input | role |
| --- | --- |
| optional `--capture-input` CSV | real KTC ESS capture rows when supplied |
| BR-102 capture schema module | field list, controlled values, subtype/family rules, and approval-boundary rules |

## Outputs
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_note_v1.md`
- `/private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check/mlpe_field_trial_real_capture_intake_contract_v1.json`

## Real Result
- capture rows: `1`
- intake-ready rows: `0`
- blocked rows: `1`
- issue rows: `1`
- status: `blocked_missing_capture_csv`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected because the real KTC ESS capture CSV has not been supplied yet.

## Smoke Matrix Result
- Missing CSV dry run blocks closed.
- One complete synthetic captured row becomes intake-ready.
- One bad synthetic row is blocked by missing path, approval flag violation, and too-early label attachment.
- All canonical/truth/threshold/engine approval sums remain `0`.

## Intake Rules
- `capture_status=planned` is not intake-ready.
- Once `capture_status` leaves `planned`, BR-102 required capture fields must be filled.
- `raw_data_path`, `peer_data_path`, and `waveform_slice_path` must be non-empty.
- `--require-existing-paths` can additionally require those paths to exist.
- `label_status=label_pending` is expected at BR-129.
- Final label fields and final label attached flags must not be used to bypass later label gates.
- `operator_promotion_allowed`, `engine_patch_allowed`, and `threshold_patch_allowed` must remain `0`.

## Safety Boundary
- Intake-ready rows are not truth rows.
- This branch does not materialize canonical truth.
- This branch does not authorize threshold, engine, or operator-facing changes.
- BR-130 may run only after a real capture CSV is supplied and passes this intake contract.

## Ordered Next Path
1. Wait for real KTC ESS capture CSV/capture bundle.
2. Run BR-129 with `--capture-input`.
3. If intake-ready rows exist, open BR-130 real capture intake run.
4. If blocked rows exist, fix capture metadata before BR-130.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_real_capture_intake_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_real_capture_intake_contract_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --output-dir /private/tmp/mlpe_field_trial_real_capture_intake_contract_br129_check
```

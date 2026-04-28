<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_111_MLPE_FIELD_TRIAL_CAPTURE_RETURN_VALIDATOR_V1

## Purpose
- Add a validator for real field-capture rows returned after the BR-110 watchlist.
- Separate three states that can be confused during 실증 handoff:
  - still waiting for real capture
  - returned but incomplete or invalid
  - returned and ready for the next readiness/handoff rerun
- Keep this branch validation-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_return_validator_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_v1.csv` | BR-110 real-capture waiting list |
| `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv` | current returned-capture placeholder; still planned |

## Outputs
- `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_note_v1.md`
- `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.json`

## Real Result
- rows: `14`
- returned-row-found rows: `14`
- still-waiting rows: `14`
- returned-ready rows: `0`
- validation-failed rows: `0`
- label-attached rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Fixture Result
- The smoke test checks both expected paths.
- Planned BR-102 template:
  - rows: `14`
  - still-waiting rows: `14`
  - returned-ready rows: `0`
  - validation-failed rows: `0`
- Synthetic filled BR-107 fixture:
  - rows: `14`
  - still-waiting rows: `0`
  - returned-ready rows: `14`
  - validation-failed rows: `0`
- The synthetic filled fixture proves the validator can open when capture metadata and evidence files exist, but it is still not field truth.

## Interpretation
- Current real project state has not received actual capture rows yet.
- That is not a failure; it is an explicit waiting state.
- Once real capture rows are returned, this validator catches missing metadata, missing evidence paths, missing evidence files, duplicate event IDs, and rows not present in the BR-110 watchlist before adjudication.

## Safety Boundary
- Return validation is not truth intake.
- `returned_capture_ready_label_pending` only means the row may proceed to BR-103/BR-106 reruns and final adjudication.
- Label-attached rows are routed to a separate truth-intake gate.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use this validator whenever a real returned-capture CSV arrives.
2. If rows are `returned_capture_ready_label_pending`, rerun BR-103 readiness and BR-106 handoff guard on those rows.
3. Keep final labels and truth intake separate until 실증 labels are externally supplied.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py research/prognostics/smoke_test_mlpe_field_trial_capture_return_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_validator_v1.py
python3 research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py --repo-root "$(pwd)" --watchlist /private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_v1.csv --returned-capture /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --output-dir /private/tmp/mlpe_field_trial_capture_return_validator_br111_check
```

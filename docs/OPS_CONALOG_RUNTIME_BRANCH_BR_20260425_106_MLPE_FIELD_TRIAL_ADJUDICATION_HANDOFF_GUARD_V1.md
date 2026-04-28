<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_106_MLPE_FIELD_TRIAL_ADJUDICATION_HANDOFF_GUARD_V1

## Purpose
- Decide whether MLPE field-trial rows may be handed to final adjudication.
- Convert the BR-103 readiness state and BR-105 manifest state into an explicit handoff guard.
- Keep this branch handoff-guard-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_adjudication_handoff_guard_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv` | readiness buckets |
| `/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_summary_v1.csv` | package artifact completeness |

## Outputs
- `/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_v1.csv`
- `/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_note_v1.md`
- `/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_v1.json`

## Real Result
- rows: `14`
- `blocked_planned_capture` rows: `14`
- adjudication handoff allowed rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Interpretation
- This is the expected result before field capture.
- The guard blocks handoff because all rows are still `capture_status=planned`.
- The manifest completeness blocker is clear: `manifest_required_missing_rows=0`.
- The next actual dependency is filled capture metadata/evidence, not algorithm work.

## Safety Boundary
- Adjudication handoff readiness is not truth readiness.
- Label-attached rows still require a separate truth-intake gate.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Fill BR-104 operator checklist rows during field capture.
2. Re-run BR-103 readiness.
3. Re-run BR-106 handoff guard.
4. If rows become `adjudication_handoff_ready`, move to final human adjudication.
5. Open a separate truth-intake branch only after final labels are supplied.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py research/prognostics/smoke_test_mlpe_field_trial_adjudication_handoff_guard_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_adjudication_handoff_guard_v1.py
python3 research/prognostics/build_mlpe_field_trial_adjudication_handoff_guard_v1.py --repo-root "$(pwd)" --readiness-input /private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv --manifest-summary-input /private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_summary_v1.csv --output-dir /private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check
```

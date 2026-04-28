<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_105_MLPE_FIELD_TRIAL_PACKAGE_MANIFEST_V1

## Purpose
- Keep the BR-101 through BR-104 MLPE field-trial artifacts discoverable from one manifest.
- Prevent the capture schema, readiness packet, and operator intake guide from becoming another scattered evidence stack.
- Keep this branch manifest-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_package_manifest_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_package_manifest_v1.py`

## Inputs
| input | role |
| --- | --- |
| `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_101_MLPE_FIELD_TRIAL_FAULT_TAXONOMY_V1.md` | taxonomy contract |
| `/private/tmp/mlpe_field_trial_capture_schema_br102_check` | BR-102 capture schema artifacts |
| `/private/tmp/mlpe_field_trial_capture_readiness_br103_check` | BR-103 readiness artifacts |
| `/private/tmp/mlpe_field_trial_operator_intake_br104_check` | BR-104 operator intake artifacts |

## Outputs
- `/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_v1.csv`
- `/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_note_v1.md`
- `/private/tmp/mlpe_field_trial_package_manifest_br105_check/mlpe_field_trial_package_manifest_v1.json`

## Real Result
- manifest rows: `13`
- required rows: `13`
- required missing rows: `0`
- stage rows:
  - taxonomy: `1`
  - capture schema: `4`
  - readiness: `3`
  - operator intake: `4`
  - handoff: `1`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Why This Exists
- We already had enough small safe branches to become hard to navigate.
- BR-105 makes the current field-trial lane restartable from one file.
- This is deliberately a navigation layer, not an evidence adjudication layer.

## Safety Boundary
- Missing required artifact rows must block field-trial handoff.
- Existing artifacts do not imply truth readiness.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use the manifest as the field-trial entry point.
2. Fill the BR-104 operator checklist during field capture.
3. Re-run BR-103 readiness against the filled capture CSV.
4. Only after final labels are supplied should a separate truth-intake branch be opened.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_package_manifest_v1.py research/prognostics/smoke_test_mlpe_field_trial_package_manifest_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_package_manifest_v1.py
python3 research/prognostics/build_mlpe_field_trial_package_manifest_v1.py --repo-root "$(pwd)" --schema-dir /private/tmp/mlpe_field_trial_capture_schema_br102_check --readiness-dir /private/tmp/mlpe_field_trial_capture_readiness_br103_check --intake-dir /private/tmp/mlpe_field_trial_operator_intake_br104_check --output-dir /private/tmp/mlpe_field_trial_package_manifest_br105_check
```

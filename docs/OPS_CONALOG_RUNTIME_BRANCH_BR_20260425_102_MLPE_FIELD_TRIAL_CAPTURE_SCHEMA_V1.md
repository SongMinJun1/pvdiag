<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_102_MLPE_FIELD_TRIAL_CAPTURE_SCHEMA_V1

## Purpose
- Turn BR-101 taxonomy into a label-ready capture schema before final labels exist.
- Make 실증 fault injection metadata collectable without prematurely creating truth labels.
- Keep planned/injection metadata separate from final adjudicated labels.
- Keep this branch capture/schema-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder/checker:
  - `research/prognostics/build_mlpe_field_trial_capture_schema_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_schema_v1.py`

## Outputs
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_schema_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_allowed_values_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_check_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_check_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_schema_note_v1.md`
- `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_schema_v1.json`

## Real Result
- template rows: `14`
- schema fields: `36`
- allowed-value rows: `139`
- check errors: `0`
- check warnings: `0`
- check passed: `1`
- final label fields are intentionally blank in template rows.
- `operator_promotion_allowed`, `engine_patch_allowed`, and `threshold_patch_allowed` are locked to `0`.

## Template Coverage
| priority | template case |
| --- | --- |
| P0 | `normal_clear_day_baseline` |
| P0 | `partial_shading_panel_local` |
| P0 | `uniform_soiling_or_cover` |
| P0 | `high_contact_resistance_or_series_resistance` |
| P0 | `partial_open_or_full_open` |
| P0 | `bypass_diode_or_substring_loss` |
| P0 | `optimizer_current_limit_or_clipping` |
| P0 | `telemetry_dropout_or_stuck_value` |
| P0 | `group_or_inverter_curtailment` |
| P0 | `site_or_root_common_cause_event` |
| P1 | `mppt_tracking_anomaly` |
| P1 | `rapid_shutdown_or_safety_state` |
| P1 | `degradation_emulation` |
| P2 | `compound_fault` |

## Checker Rules
- Template/planned rows may leave capture metadata blank while `capture_status=planned`.
- Once `capture_status` leaves `planned`, required capture fields such as `site`, `panel_id`, `mlpe_device_id`, `start_ts`, `end_ts`, raw paths, peer paths, waveform paths, timestamp quality, and communication quality are required.
- `label_status=label_pending` requires final label fields to stay blank.
- `label_status=label_attached` requires final family, subtype, and truth confidence, but still does not allow operator/engine/threshold approval.
- Planned and final subtypes must match the allowed subtype list for their family.
- `planned_measurement_artifact_flag=1` requires `planned_fault_family=measurement_or_communication_artifact`.
- `planned_panel_local_flag=1` and `planned_common_cause_flag=1` cannot both be true.
- Approval flags must remain `0`.

## Safety Boundary
- BR-102 creates a capture contract, not truth labels.
- Final labels will be supplied later after 실증/adjudication.
- A filled capture CSV must pass this checker before any truth-intake, threshold replay, or direct engine patch review.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use the generated template when planning field-trial injections.
2. Fill capture metadata and evidence paths during 실증.
3. Keep all final label fields blank until final adjudication.
4. Build a BR-103 intake/readiness packet that checks filled capture rows against raw/peer/waveform availability.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_capture_schema_v1.py research/prognostics/smoke_test_mlpe_field_trial_capture_schema_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_schema_v1.py
python3 research/prognostics/build_mlpe_field_trial_capture_schema_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_capture_schema_br102_check
```

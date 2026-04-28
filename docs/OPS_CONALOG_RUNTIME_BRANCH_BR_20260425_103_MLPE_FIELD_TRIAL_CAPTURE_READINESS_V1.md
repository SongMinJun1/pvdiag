<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_103_MLPE_FIELD_TRIAL_CAPTURE_READINESS_V1

## Purpose
- Read BR-102 capture rows and classify whether each 실증 event is ready for later adjudication.
- Separate planned rows, incomplete captured rows, missing evidence paths, existing evidence files, and label-pending ready rows.
- Keep readiness separate from truth labels:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_readiness_packet_v1.py`

## Input
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv` | BR-102 label-pending capture template |

## Outputs
- `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_missing_evidence_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_note_v1.md`
- `/private/tmp/mlpe_field_trial_capture_readiness_br103_check/mlpe_field_trial_capture_readiness_packet_v1.json`

## Real Result
- rows: `14`
- metadata-ready rows: `0`
- evidence-paths-filled rows: `0`
- evidence-files-exist rows: `0`
- capture-ready label-pending rows: `0`
- label-attached rows: `0`
- truth intake allowed sum: `0`
- engine patch allowed sum: `0`

## Current Interpretation
- All 14 rows are still `planned_waiting_for_capture`, which is expected before 실증 metadata is filled.
- Missing evidence output uses `planned_required_later_metadata` and `planned_required_later_evidence_path` for planned rows, so these are not current defects.
- Readiness will become meaningful after site/panel/MLPE/timestamp/raw/peer/waveform fields are filled during 실증.

## Readiness Buckets
| bucket | meaning |
| --- | --- |
| `planned_waiting_for_capture` | setup row; fill metadata during 실증 |
| `capture_metadata_incomplete` | capture started but required metadata is still missing |
| `evidence_paths_missing` | required raw/peer/waveform path fields are blank |
| `evidence_files_not_found` | path fields are filled but files are absent |
| `capture_ready_label_pending` | capture/evidence exist; ready for final adjudication, not truth intake |
| `label_attached_truth_gate_required` | final label exists, but a separate truth-intake gate is still required |

## Safety Boundary
- Readiness is not a final label.
- Label-attached rows still require a separate truth-intake gate.
- Missing raw/peer/waveform evidence must be resolved before adjudication.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.

## Ordered Next Path
1. During 실증, fill BR-102 capture rows with site, panel, MLPE, time window, intensity, and evidence paths.
2. Re-run BR-103 on the filled capture file.
3. Resolve `capture_metadata_incomplete`, `evidence_paths_missing`, and `evidence_files_not_found` rows.
4. Only rows in `capture_ready_label_pending` should move to final adjudication.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py research/prognostics/smoke_test_mlpe_field_trial_capture_readiness_packet_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_readiness_packet_v1.py
python3 research/prognostics/build_mlpe_field_trial_capture_readiness_packet_v1.py --repo-root "$(pwd)" --capture-input /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --output-dir /private/tmp/mlpe_field_trial_capture_readiness_br103_check
```

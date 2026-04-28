<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_112_MLPE_FIELD_TRIAL_CAPTURE_RETURN_EVIDENCE_RESOLVER_V1

## Purpose
- Add an evidence resolver after BR-111 capture-return validation.
- Expand each returned capture row into evidence attachment checks:
  - raw
  - peer
  - weather
  - waveform
- Keep waiting rows separate from evidence failures, so planned rows do not create false alarms before 실증 data returns.
- Keep this branch attachment-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv` | BR-111 return validation state |
| `/private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv` | current returned-capture placeholder; still planned |

## Outputs
- `/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_note_v1.md`
- `/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_v1.json`

## Real Result
- events: `14`
- waiting events: `14`
- returned-ready events: `0`
- evidence rows: `56`
- required evidence rows: `42`
- evidence-path-filled rows: `0`
- evidence-file-exists rows: `0`
- required evidence problem rows: `0`
- evidence file size total bytes: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Fixture Result
- Planned BR-102 template:
  - waiting events: `14`
  - returned-ready events: `0`
  - evidence rows: `56`
  - evidence-file-exists rows: `0`
  - required evidence problem rows: `0`
- Synthetic filled BR-107 fixture:
  - waiting events: `0`
  - returned-ready events: `14`
  - evidence rows: `56`
  - evidence-file-exists rows: `56`
  - required evidence problem rows: `0`
- The synthetic fixture proves the resolver opens when evidence files exist, but it remains fixture-only and does not create truth labels.

## Interpretation
- The current project state is still waiting for real capture.
- Missing paths on waiting rows are not evidence defects.
- After real capture is returned, this resolver becomes the file-level attachment check before rerunning readiness and handoff gates.

## Safety Boundary
- Evidence resolution is not truth intake.
- Resolved files are attachments, not independent physical confirmation.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use BR-111 to validate returned rows.
2. Use BR-112 to resolve returned evidence files and sizes.
3. Rerun BR-103 and BR-106 only after returned rows and required evidence resolve cleanly.
4. Keep final labels external until 실증/final review supplies them.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py
python3 research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py --repo-root "$(pwd)" --validation /private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv --returned-capture /private/tmp/mlpe_field_trial_capture_schema_br102_check/mlpe_field_trial_capture_template_v1.csv --output-dir /private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check
```

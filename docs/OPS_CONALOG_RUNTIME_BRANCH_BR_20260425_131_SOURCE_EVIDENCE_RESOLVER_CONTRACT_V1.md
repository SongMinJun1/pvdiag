<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_131_SOURCE_EVIDENCE_RESOLVER_CONTRACT_V1

## Purpose
- Build the source/evidence resolver contract before BR-132 real-row execution.
- Define exactly which source/evidence groups must resolve after BR-129 intake-ready rows exist.
- Keep this branch resolver-contract-only:
  - no truth intake write
  - no canonical truth write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_source_evidence_resolver_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_source_evidence_resolver_contract_v1.py`

## Contract Groups
| evidence group | required | role |
| --- | ---: | --- |
| `capture_validation_row` | 1 | BR-129 validation/source trace |
| `capture_row` | 1 | matching real capture CSV row |
| `raw_data_slice` | 1 | exact-panel raw signal slice |
| `peer_context_slice` | 1 | peer/common-cause context slice |
| `waveform_slice` | 1 | morphology/physical-invariant review slice |
| `weather_context` | 0 | optional external context |

## Outputs
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolver_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolution_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolver_contract_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolver_contract_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolver_contract_note_v1.md`
- `/private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check/mlpe_field_trial_source_evidence_resolver_contract_v1.json`

## Real Result
- contract rows: `6`
- events: `0`
- source/evidence-ready events: `0`
- resolution rows: `1`
- required resolution rows: `1`
- source/evidence resolved rows: `0`
- source/evidence blocked rows: `1`
- path-exists rows: `0`
- issue rows: `1`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. BR-130 real capture intake remains blocked because the real KTC ESS capture CSV has not been supplied yet.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `6`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - events: `2`
  - resolution rows: `12`
  - source/evidence-ready events: `1`
  - approval sums: `0`
- Synthetic bad fixture:
  - source/evidence-ready events: `0`
  - detects both `blocked_required_path_missing` and `blocked_file_not_found`

## Safety Boundary
- BR-131 resolved files are attachments, not labels.
- Resolved files are not independent physical confirmation by themselves.
- BR-132 may run only after BR-130 creates real intake rows.
- Approval/write fields remain locked to `0`.

## Ordered Next Path
1. Keep BR-130 blocked until the user supplies the real KTC ESS capture CSV/capture bundle.
2. Use BR-131 as the source/evidence resolver contract.
3. Once real intake rows exist, run BR-132 with BR-129 validation rows plus real capture CSV paths.
4. If BR-132 resolves all required source/evidence groups, proceed to BR-133/134 common-cause clearance.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_source_evidence_resolver_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_source_evidence_resolver_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_source_evidence_resolver_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_source_evidence_resolver_contract_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_source_evidence_resolver_contract_br131_check
```

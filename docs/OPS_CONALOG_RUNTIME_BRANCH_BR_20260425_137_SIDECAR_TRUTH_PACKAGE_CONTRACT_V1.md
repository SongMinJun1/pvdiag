<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_137_SIDECAR_TRUTH_PACKAGE_CONTRACT_V1

## Purpose
- Build the sidecar truth package contract before BR-138 real package execution.
- Require BR-127 materialization readiness, common-cause clearance, artifact/MLPE-control clearance, stable sidecar payload identity, truth-label payload, provenance attachment, write-boundary lock, and reviewer approval note.
- Keep this branch package-contract-only:
  - no truth intake write
  - no canonical truth write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_sidecar_truth_package_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_sidecar_truth_package_contract_v1.py`

## Contract Groups
| package group | required | role |
| --- | ---: | --- |
| `materialization_precheck_ready` | 1 | BR-127 must mark the event as a future sidecar truth package candidate |
| `common_cause_clearance_ready` | 1 | common-cause blockers must be cleared before panel-local truth packaging |
| `artifact_mlpe_control_clearance_ready` | 1 | artifact/MLPE-control blockers must be cleared before physical-panel truth packaging |
| `sidecar_payload_identity` | 1 | sidecar package id plus site/root/panel/date identity must be stable |
| `sidecar_truth_label_payload` | 1 | sidecar truth label, fault family, event type, and at least one event date must be present |
| `source_evidence_provenance_attached` | 1 | package row must point back to materialization and clearance evidence |
| `write_boundary_locked` | 1 | source and package write/approval flags must remain `0` |
| `reviewer_package_approval_note` | 1 | reviewer approval flag and note must be present |

## Outputs
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_contract_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_contract_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_contract_note_v1.md`
- `/private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check/mlpe_field_trial_sidecar_truth_package_contract_v1.json`

## Real Result
- contract rows: `8`
- events: `0`
- sidecar-truth-package-ready events: `0`
- package rows: `0`
- package passed rows: `0`
- package blocked rows: `0`
- issue rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. The BR-127 materialization precheck output exists but has no real package candidate rows, so BR-138 real sidecar package execution remains blocked.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `8`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - events: `2`
  - package rows: `16`
  - sidecar-truth-package-ready events: `1`
  - approval sums: `0`
- Synthetic bad fixture:
  - sidecar-truth-package-ready events: `0`
  - detects common-cause, artifact/MLPE-control, identity, truth-label payload, provenance, write-boundary, and reviewer-approval blockers

## Safety Boundary
- Passing this contract only means a row is eligible for a sidecar truth package dry-run.
- It does not create canonical truth labels.
- It does not authorize threshold replay or panel-engine changes.
- Sidecar package rows remain review material until a later replay/evaluation branch proves result impact.
- Approval/write fields remain locked to `0`.

## Ordered Next Path
1. Keep BR-130/132/134/136/138 blocked until real KTC ESS capture, source/evidence rows, clearance rows, and package candidate rows exist.
2. Use BR-137 as the sidecar truth package contract.
3. Once BR-134 and BR-136 clearance rows exist, run BR-138 with a row-level sidecar package input.
4. If sidecar truth package rows exist, continue to BR-139 truth replay scorecard contract before any performance or threshold claim.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_sidecar_truth_package_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_sidecar_truth_package_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_sidecar_truth_package_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_sidecar_truth_package_contract_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_sidecar_truth_package_contract_br137_check
```

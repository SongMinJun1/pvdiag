<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_135_ARTIFACT_MLPE_CONTROL_CLEARANCE_CONTRACT_V1

## Purpose
- Build the measurement-artifact and MLPE-control clearance contract before BR-136 real-row execution.
- Require source/evidence readiness plus timestamp, communication, telemetry-artifact, MLPE-control-state, panel-physical-separation, and reviewer clearance.
- Keep this branch clearance-contract-only:
  - no truth intake write
  - no canonical truth write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py`

## Contract Groups
| clearance group | required | role |
| --- | ---: | --- |
| `source_evidence_ready` | 1 | BR-131/132 source-evidence row must be ready first |
| `timestamp_quality_clearance` | 1 | timestamp alignment, duplicate-time, and clock drift blockers must be cleared |
| `communication_quality_clearance` | 1 | dropout, stale packet, and missing telemetry blockers must be cleared |
| `telemetry_artifact_clearance` | 1 | impossible value, stuck value, scaling, and sensor-feedback blockers must be cleared |
| `mlpe_control_state_clearance` | 1 | optimizer state, rapid-shutdown/control mode, clipping, and MLPE-device blockers must be cleared |
| `panel_physical_separation_clearance` | 1 | panel-local physical evidence must be separated from artifact/control evidence |
| `reviewer_clearance_note` | 1 | reviewer must leave an explicit artifact/MLPE-control clearance note |

## Outputs
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_contract_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_contract_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_contract_note_v1.md`
- `/private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check/mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.json`

## Real Result
- contract rows: `7`
- events: `0`
- artifact/MLPE-control-clearance-ready events: `0`
- clearance rows: `1`
- clearance passed rows: `0`
- clearance blocked rows: `1`
- issue rows: `1`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. BR-136 real artifact/MLPE-control clearance remains blocked until BR-132 source/evidence rows and returned telemetry/clearance rows exist.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `7`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - events: `2`
  - clearance rows: `14`
  - artifact/MLPE-control-clearance-ready events: `1`
  - approval sums: `0`
- Synthetic bad fixture:
  - artifact/MLPE-control-clearance-ready events: `0`
  - detects timestamp, communication, telemetry-artifact, MLPE-control, panel-physical-separation, and reviewer-clearance blockers

## Safety Boundary
- Passing this contract only clears artifact/MLPE-control blockers for a later sidecar flow.
- It does not create truth labels, threshold approval, or panel-local promotion.
- Telemetry artifact and MLPE-control rows remain blocker/regression material unless explicitly cleared.
- MLPE/control behavior must not be collapsed into a panel physical fault.
- Approval/write fields remain locked to `0`.

## Ordered Next Path
1. Keep BR-130/132/134/136 blocked until real KTC ESS capture, source/evidence rows, and returned telemetry rows exist.
2. Use BR-135 as the artifact/MLPE-control clearance contract.
3. Once BR-132 source/evidence rows exist, run BR-136 with row-level artifact/MLPE-control clearance input.
4. If common-cause and artifact/MLPE-control blockers are cleared, continue to BR-137 sidecar truth package contract.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_artifact_mlpe_control_clearance_contract_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --output-dir /private/tmp/mlpe_field_trial_artifact_mlpe_control_clearance_contract_br135_check
```

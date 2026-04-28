<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_133_COMMON_CAUSE_CLEARANCE_CONTRACT_V1

## Purpose
- Build the common-cause clearance contract before BR-134 real-row execution.
- Require source/evidence readiness plus peer, site breadth, root/group breadth, temporal synchrony, and reviewer clearance.
- Keep this branch clearance-contract-only:
  - no truth intake write
  - no canonical truth write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_common_cause_clearance_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_common_cause_clearance_contract_v1.py`

## Contract Groups
| clearance group | required | role |
| --- | ---: | --- |
| `source_evidence_ready` | 1 | BR-131/132 source-evidence row must be ready first |
| `peer_context_clearance` | 1 | peer/reference context must exist and be cleared |
| `site_breadth_clearance` | 1 | site-wide/bulk screen must be cleared |
| `root_group_breadth_clearance` | 1 | root/group-side breadth must be cleared |
| `temporal_synchrony_clearance` | 1 | same-day site/group synchrony must be cleared |
| `reviewer_clearance_note` | 1 | reviewer must leave an explicit clearance note |

## Outputs
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_contract_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_contract_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_contract_note_v1.md`
- `/private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check/mlpe_field_trial_common_cause_clearance_contract_v1.json`

## Real Result
- contract rows: `6`
- events: `0`
- common-cause-clearance-ready events: `0`
- clearance rows: `1`
- clearance passed rows: `0`
- clearance blocked rows: `1`
- issue rows: `1`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. BR-134 real common-cause clearance remains blocked until BR-132 source/evidence rows exist.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `6`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - events: `2`
  - clearance rows: `12`
  - common-cause-clearance-ready events: `1`
  - approval sums: `0`
- Synthetic bad fixture:
  - common-cause-clearance-ready events: `0`
  - detects `blocked_peer_context_not_cleared`, `blocked_temporal_synchrony_not_cleared`, and `blocked_reviewer_clearance_missing`

## Safety Boundary
- Passing this contract only clears common-cause blockers for a later sidecar flow.
- It does not create truth labels, threshold approval, or panel-local promotion.
- Common-cause rows remain blocker/regression material unless explicitly cleared.
- Approval/write fields remain locked to `0`.

## Ordered Next Path
1. Keep BR-130/132/134 blocked until real KTC ESS capture and source/evidence rows exist.
2. Use BR-133 as the common-cause clearance contract.
3. Once BR-132 source/evidence rows exist, run BR-134 with a row-level common-cause clearance input.
4. If common-cause is cleared, continue to BR-135/136 artifact and MLPE-control clearance.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_common_cause_clearance_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_common_cause_clearance_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_common_cause_clearance_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_common_cause_clearance_contract_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_common_cause_clearance_contract_br133_check
```

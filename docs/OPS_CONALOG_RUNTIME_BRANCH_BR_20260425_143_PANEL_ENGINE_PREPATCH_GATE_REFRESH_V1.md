<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_143_PANEL_ENGINE_PREPATCH_GATE_REFRESH_V1

## Purpose
- Refresh the panel-engine prepatch gate before any BR-144 semantic patch discussion.
- Keep this branch gate-only and fail-closed:
  - no `pv_ae/panel_day_engine.py` patch
  - no canonical truth write
  - no truth intake write
  - no threshold patch
  - no operator-facing behavior change
  - no performance improvement claim

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py`

## Contract Groups
| gate group | required | role |
| --- | ---: | --- |
| `selected_rule_candidate_ready` | 1 | exactly one shadow rule/semantic candidate must be selected before BR-144 |
| `truth_replay_support_ready` | 1 | candidate discussion requires truth replay with positive and negative support |
| `shadow_apply_result_ready` | 1 | shadow application must show intended-only result delta |
| `three_gate_prepatch_runbook_ready` | 1 | BR-076 panel-engine, fault-family, and common-cause gates must pass |
| `source_package_mirror_plan_ready` | 1 | source/package sync plan must be explicit before an engine patch |
| `public_behavior_docs_plan_ready` | 1 | public behavior docs must be planned when behavior may change |
| `validation_commands_plan_ready` | 1 | py_compile, full runtime smoke, and result-delta compare must be planned |
| `result_delta_acceptance_plan_ready` | 1 | intended-only delta acceptance criteria must be non-empty |
| `large_data_exclusion_locked` | 1 | data/raw/out and other large data paths must stay outside patch scope |
| `reviewer_prepatch_approval_note` | 1 | reviewer prepatch approval note must be present |
| `write_boundary_locked` | 1 | BR-143 must authorize no truth, threshold, or engine writes |
| `engine_patch_authorization_blocked_until_br144` | 1 | engine patch approval must remain `0` in this branch |

## Outputs
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_note_v1.md`
- `/private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check/mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.json`

## Real Result
- contract rows: `12`
- patch candidates: `0`
- prepatch-ready candidates: `0`
- gate rows: `1`
- gate passed rows: `0`
- gate blocked rows: `1`
- issue rows: `1`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. No selected rule candidate, truth replay support, or shadow application row exists yet, so the gate blocks direct panel-engine patch work.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `12`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - patch candidates: `1`
  - prepatch-ready candidates: `1`
  - gate rows: `12`
  - blocked rows: `0`
  - engine patch allowed sum: `0`
- Synthetic bad fixture:
  - prepatch-ready candidates: `0`
  - detects missing selected rule, replay support, shadow result, 3-gate runbook, source/package plan, docs plan, result-delta plan, large data leak, reviewer note, write-boundary violation, and engine-patch authorization leak

## Safety Boundary
- Passing BR-143 means only that a candidate is ready for BR-144 review.
- BR-143 does not authorize `pv_ae/panel_day_engine.py` edits.
- BR-143 does not authorize canonical truth, truth intake, threshold, or engine writes.
- BR-143 does not replace BR-140 truth replay, BR-141 candidate selection, or BR-142 shadow application.
- BR-144 remains blocked until the selected rule candidate, replay support, shadow output, and prepatch runbook are all attached.

## Ordered Next Path
1. Keep BR-144 blocked because the real state has no selected rule candidate and no truth replay/shadow row.
2. When real KTC ESS capture/label material arrives, resume the blocked real-data branches: BR-130, BR-132, BR-134, BR-136, BR-138, and BR-140.
3. Only after BR-140 replay support can BR-141 choose one rule candidate and BR-142 shadow-apply it.
4. Use BR-143 again as the final prepatch gate check immediately before any BR-144 engine patch.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py research/prognostics/smoke_test_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py
python3 research/prognostics/build_mlpe_field_trial_panel_engine_prepatch_gate_refresh_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_panel_engine_prepatch_gate_refresh_br143_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_229_LATEST_HANDOFF_MANIFEST_REPRO_REFRESH_PLAN_V1

## Summary
- This patch builds a branch-level refresh plan for the latest evidence handoff manifest repro commands.
- It does not rewrite the generated latest-handoff literals yet.
- It does not move artifacts, change runtime semantics, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-228 showed that `41` generated repro literals belong to the current latest handoff manifest.
- Editing those literals one by one would be fragile and would mix input dependencies, output destinations, and one stale checkout root.
- The safer next move is to classify the handoff rows first, then refresh the generator as one unit in a later dry-run branch.

## Observed Result
- `branch_spec_rows`: `14`
- `refresh_required_branch_rows`: `12`
- `repo_doc_no_refresh_branch_rows`: `2`
- `latest_handoff_repro_literal_rows_from_br228`: `41`
- `planned_repro_temp_literal_rows`: `41`
- `temp_input_literal_rows`: `28`
- `temp_output_literal_rows`: `12`
- `temp_repo_root_literal_rows`: `1`
- `manifest_input_required_branch_rows`: `12`
- `output_parameterization_required_branch_rows`: `12`
- `repo_root_refresh_required_branch_rows`: `1`
- `manual_literal_edit_allowed_rows`: `0`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`
- `latest_literal_count_match`: `1`
- `refresh_plan_complete`: `1`

## Boundary
- Do not edit latest handoff repro literals one by one.
- Treat input literals as manifestized or explicit CLI inputs in the refreshed generator.
- Treat output literals as parameterized output destinations, not evidence dependencies.
- Replace the stale repo-root literal through generated current-checkout repro text in the next branch.
- Keep this separate from runtime semantics and panel-engine code.

## Files
- `research/prognostics/build_latest_handoff_manifest_repro_refresh_plan_v1.py`
- `research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_plan_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_229_LATEST_HANDOFF_MANIFEST_REPRO_REFRESH_PLAN_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_latest_handoff_manifest_repro_refresh_plan_v1.py \
  research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_plan_v1.py
python3 research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_plan_v1.py
python3 research/prognostics/build_latest_handoff_manifest_repro_refresh_plan_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/latest_handoff_manifest_repro_refresh_plan_br229_check"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Expected Result
- The plan should report `branch_spec_rows=14`.
- The plan should report `planned_repro_temp_literal_rows=41`.
- The plan should report `latest_handoff_repro_literal_rows_from_br228=41`.
- The plan should report `temp_input_literal_rows=28`.
- The plan should report `temp_output_literal_rows=12`.
- The plan should report `temp_repo_root_literal_rows=1`.
- The plan should report `manual_literal_edit_allowed_rows=0`.
- The plan should report `refresh_plan_complete=1`.

## Next Decision
- Build the next branch as `latest_handoff_manifest_repro_refresh_dry_run`.
- The next branch may generate replacement repro commands, but should first compare old/new rows and keep runtime/operator-facing behavior unchanged.

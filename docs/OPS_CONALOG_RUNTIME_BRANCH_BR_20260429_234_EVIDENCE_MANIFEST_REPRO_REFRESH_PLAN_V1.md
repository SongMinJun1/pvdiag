<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_234_EVIDENCE_MANIFEST_REPRO_REFRESH_PLAN_V1

## Summary
- This patch plans the evidence manifest repro-command refresh for the remaining generated handoff lane from BR-233.
- It maps the `7` hard-coded evidence-manifest `/private/tmp` repro literals into a single `${EVIDENCE_MANIFEST_OUTPUT_ROOT}` replacement shape.
- It does not edit `build_panel_day_engine_evidence_manifest_v1.py`, execute production jobs, change runtime semantics, change operator-facing outputs, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-233 confirmed the latest handoff lane is closed and left only `9` generated handoff/repro literals:
  - evidence manifest repro rows: `7`
  - episode note repro rows: `1`
  - validation output literal rows: `1`
- The `7` evidence manifest rows are generated from `build_panel_day_engine_evidence_manifest_v1.py` command constants.
- Before rewriting that builder, the replacement contract needs to be explicit and smoke-tested so the next branch does not hand-edit literals one by one.

## Observed Result
- `plan_literal_rows`: `7`
- `command_group_rows`: `4`
- `artifact_specs_rows`: `23`
- `runtime_artifact_specs_rows`: `14`
- `builder_artifact_specs_rows`: `6`
- `manual_oneoff_artifact_specs_rows`: `3`
- `manual_oneoff_command_rows_preserved`: `2`
- `old_private_tmp_literal_rows`: `7`
- `proposed_private_tmp_literal_rows`: `0`
- `runtime_output_root_literal_rows`: `1`
- `sidecar_result_root_literal_rows`: `3`
- `sidecar_output_dir_literal_rows`: `3`
- `manual_literal_edit_allowed_rows`: `0`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`
- `plan_complete`: `1`

## Replacement Contract
- Runtime output root becomes `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/runtime`.
- Builder sidecars read the shared result root from `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/runtime/result`.
- Builder sidecars write to `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/report_entry_friction_axis_sidecar`, `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/recovery_recurrence_axis_sidecar`, and `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/common_cause_synchrony_axis_sidecar`.
- `manual_oneoff` repro rows remain documented manual scans and are not converted in this branch.

## Boundary
- This is a plan-only branch.
- No source builder replacement is applied yet.
- No manual generated-output rewrite is allowed.
- The next branch should generate a dry-run source patch from this plan, then compare old/proposed manifest rows before applying the builder change.

## Files
- `research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py`
- `research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_234_EVIDENCE_MANIFEST_REPRO_REFRESH_PLAN_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py \
  research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py
python3 research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py
python3 research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/evidence_manifest_repro_refresh_plan_br234_check"
python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py \
  --data-root data \
  --output-root "${TMPDIR:-/tmp}/br234_conalog_runtime_smoke" \
  --sites conalog \
  --workspace-retention result-only
git diff --check
```

## Expected Result
- The plan should report `plan_literal_rows=7`.
- The plan should report `command_group_rows=4`.
- The plan should report `old_private_tmp_literal_rows=7`.
- The plan should report `proposed_private_tmp_literal_rows=0`.
- The plan should report `plan_complete=1`.
- The conalog runtime validation should complete and write `result/` plus `workspace_cleanup_v1.json`.

## Next Decision
- Build the next branch as `evidence_manifest_repro_refresh_dry_run`.
- Keep episode note repro deferred and validation output literal preserved unless those lanes are explicitly reopened.

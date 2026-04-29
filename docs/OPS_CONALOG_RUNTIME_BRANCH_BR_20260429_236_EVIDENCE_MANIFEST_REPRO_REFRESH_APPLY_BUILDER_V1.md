<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_236_EVIDENCE_MANIFEST_REPRO_REFRESH_APPLY_BUILDER_V1

## Summary
- This patch applies the BR-234/235 evidence manifest repro-command refresh to `build_panel_day_engine_evidence_manifest_v1.py`.
- It replaces only the four repro command constants and leaves `ARTIFACT_SPECS` rows to inherit those constants.
- It keeps `manual_oneoff` repro commands unchanged and does not change runtime semantics, operator-facing outputs, or `pv_ae/panel_day_engine.py`.

## Why
- BR-235 proved the source patch target is exactly four constants while generated artifact-spec rows inherit the change automatically.
- Leaving `/private/tmp` in evidence manifest repro commands made regenerated handoff/evidence material look tied to stale local temp roots.
- The safe fix is command-constant parameterization, not row-by-row generated-output editing.

## Applied Source Boundary
- Changed:
  - `RUNTIME_REPRO_COMMAND`
  - `REPORT_ENTRY_REPRO_COMMAND`
  - `RECOVERY_REPRO_COMMAND`
  - `COMMON_CAUSE_REPRO_COMMAND`
- Preserved:
  - `GROUP_OFF_REPRO_COMMAND`
  - `OPPORTUNITY_REPRO_COMMAND`
- Replacement root:
  - `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/runtime`
  - `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/runtime/result`
  - `${EVIDENCE_MANIFEST_OUTPUT_ROOT}/<axis_sidecar>`

## Observed Result
- BR-234 plan after apply:
  - `old_private_tmp_literal_rows`: `0`
  - `proposed_private_tmp_literal_rows`: `0`
  - `already_applied_literal_rows`: `7`
  - `plan_complete`: `1`
  - `closure_complete`: `1`
- BR-235 dry-run after apply:
  - `changed_artifact_spec_rows`: `0`
  - `source_patch_required_command_rows`: `0`
  - `source_patch_already_applied_command_rows`: `4`
  - `artifact_row_old_private_tmp_literal_rows`: `0`
  - `artifact_row_proposed_private_tmp_literal_rows`: `0`
  - `closure_complete`: `1`
- Generated handoff literal rescan after apply:
  - `post_br232_generated_handoff_repro_literal_rows`: `2`
  - `latest_handoff_manifest_repro_rows`: `0`
  - `evidence_manifest_repro_rows`: `0`
  - `episode_note_repro_rows`: `1`
  - `validation_output_literal_rows`: `1`
  - `evidence_manifest_closed_after_br236`: `1`
  - `residual_rescan_complete`: `1`

## Files
- `research/prognostics/build_panel_day_engine_evidence_manifest_v1.py`
- `research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py`
- `research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py`
- `research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py`
- `research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py`
- `research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py`
- `research/prognostics/build_generated_handoff_repro_literal_post_br232_rescan_v1.py`
- `research/prognostics/smoke_test_generated_handoff_repro_literal_post_br232_rescan_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_236_EVIDENCE_MANIFEST_REPRO_REFRESH_APPLY_BUILDER_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_evidence_manifest_v1.py \
  research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py \
  research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py \
  research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py \
  research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py \
  research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py \
  research/prognostics/build_generated_handoff_repro_literal_post_br232_rescan_v1.py \
  research/prognostics/smoke_test_generated_handoff_repro_literal_post_br232_rescan_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py
python3 research/prognostics/smoke_test_evidence_manifest_repro_refresh_plan_v1.py
python3 research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py
python3 research/prognostics/smoke_test_generated_handoff_repro_literal_post_br232_rescan_v1.py
python3 research/prognostics/build_generated_handoff_repro_literal_post_br232_rescan_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/generated_handoff_repro_literal_post_br232_rescan_br236_check"
python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py \
  --data-root "${PVDIAG_DATA_ROOT:-data}" \
  --output-root "${TMPDIR:-/tmp}/br236_conalog_runtime_smoke" \
  --sites conalog \
  --workspace-retention result-only
git diff --check
```

## Expected Result
- Evidence manifest smoke should prove generated repro commands have no `/private/tmp/` and use `${EVIDENCE_MANIFEST_OUTPUT_ROOT}`.
- Plan and dry-run smokes should report closure complete.
- Generated handoff rescan should report `evidence_manifest_repro_rows=0`.
- The conalog runtime validation should complete and write `result/` plus `workspace_cleanup_v1.json`.

## Next Decision
- Keep episode note repro deferred until `build_panel_day_engine_episode_truth_map_v1.py` is touched.
- Preserve the validation output literal as an explicit output destination.
- If continuing portability cleanup, the next branch should target only the deferred episode note repro row.

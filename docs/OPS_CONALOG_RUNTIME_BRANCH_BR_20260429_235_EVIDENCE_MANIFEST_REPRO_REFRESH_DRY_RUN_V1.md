<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_235_EVIDENCE_MANIFEST_REPRO_REFRESH_DRY_RUN_V1

## Summary
- This patch dry-runs the BR-234 evidence manifest repro-command replacement plan.
- It compares every `ARTIFACT_SPECS` repro row before applying a source builder patch.
- It does not edit `build_panel_day_engine_evidence_manifest_v1.py`, execute production jobs as part of the dry-run, change runtime semantics, change operator-facing outputs, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-234 proved there are `7` unique hard-coded `/private/tmp` repro literals across `4` evidence manifest command constants.
- The generated manifest repeats those command constants across artifact rows, so the output-table impact must be checked separately from the source literal count.
- A dry-run comparison prevents the next branch from accidentally rewriting `ARTIFACT_SPECS` rows one by one or changing manual one-off repro rows.

## Observed Result
- `artifact_spec_rows`: `23`
- `changed_artifact_spec_rows`: `20`
- `unchanged_artifact_spec_rows`: `3`
- `runtime_artifact_spec_rows`: `14`
- `builder_artifact_spec_rows`: `6`
- `manual_oneoff_artifact_spec_rows`: `3`
- `placeholder_root_used_artifact_rows`: `20`
- `unique_source_command_rows`: `4`
- `source_patch_required_command_rows`: `4`
- `artifact_row_old_private_tmp_literal_rows`: `26`
- `artifact_row_proposed_private_tmp_literal_rows`: `0`
- `unique_command_old_private_tmp_literal_rows`: `7`
- `unique_command_proposed_private_tmp_literal_rows`: `0`
- `manual_literal_edit_allowed_rows`: `0`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`
- `dry_run_complete`: `1`

## Source Patch Boundary
- Patch only the four repro command constants:
  - `RUNTIME_REPRO_COMMAND`
  - `REPORT_ENTRY_REPRO_COMMAND`
  - `RECOVERY_REPRO_COMMAND`
  - `COMMON_CAUSE_REPRO_COMMAND`
- Do not rewrite `ARTIFACT_SPECS` rows individually; they inherit the updated constants.
- Preserve `GROUP_OFF_REPRO_COMMAND` and `OPPORTUNITY_REPRO_COMMAND` as documented `manual_oneoff` repro rows.

## Files
- `research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py`
- `research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_235_EVIDENCE_MANIFEST_REPRO_REFRESH_DRY_RUN_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_evidence_manifest_repro_refresh_plan_v1.py \
  research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py \
  research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py
python3 research/prognostics/smoke_test_evidence_manifest_repro_refresh_dry_run_v1.py
python3 research/prognostics/build_evidence_manifest_repro_refresh_dry_run_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/evidence_manifest_repro_refresh_dry_run_br235_check"
python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py \
  --data-root "${PVDIAG_DATA_ROOT:-data}" \
  --output-root "${TMPDIR:-/tmp}/br235_conalog_runtime_smoke" \
  --sites conalog \
  --workspace-retention result-only
git diff --check
```

## Expected Result
- The dry-run should report `artifact_spec_rows=23`.
- The dry-run should report `changed_artifact_spec_rows=20`.
- The dry-run should report `artifact_row_old_private_tmp_literal_rows=26`.
- The dry-run should report `artifact_row_proposed_private_tmp_literal_rows=0`.
- The dry-run should report `source_patch_required_command_rows=4`.
- The dry-run should report `dry_run_complete=1`.
- The conalog runtime validation should complete and write `result/` plus `workspace_cleanup_v1.json`.

## Next Decision
- Build the next branch as `evidence_manifest_repro_refresh_apply_builder`.
- After applying the builder patch, regenerate the evidence manifest and re-run the generated handoff literal rescan.

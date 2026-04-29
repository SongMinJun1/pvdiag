<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_230_LATEST_HANDOFF_MANIFEST_REPRO_REFRESH_DRY_RUN_V1

## Summary
- This patch generates old/new repro command comparisons for the latest evidence handoff manifest.
- It does not edit `research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py` yet.
- It does not move artifacts, change runtime semantics, change operator-facing outputs, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-229 proved that the latest handoff manifest has `41` current repro temp literals across `12` refresh-required rows.
- A single global input manifest would be unsafe because shared keys can mean different artifacts in different scripts.
- The dry-run therefore uses one branch-local input manifest per refreshed handoff row and one parameterized output root placeholder.

## Observed Result
- `branch_spec_rows`: `14`
- `refresh_required_branch_rows`: `12`
- `repo_doc_unchanged_branch_rows`: `2`
- `manual_review_branch_rows`: `0`
- `old_private_tmp_literal_rows`: `41`
- `proposed_private_tmp_literal_rows`: `0`
- `input_manifest_added_rows`: `12`
- `input_flags_removed_rows`: `28`
- `output_root_parameterized_rows`: `12`
- `output_literals_replaced_rows`: `12`
- `repo_root_replaced_with_pwd_rows`: `1`
- `repo_root_literals_replaced_rows`: `1`
- `script_supports_input_manifest_rows`: `12`
- `global_manifest_key_conflict_rows`: `1`
- `branch_manifest_key_collision_rows`: `0`
- `plan_repro_temp_literal_rows_from_br229`: `41`
- `plan_refresh_required_branch_rows_from_br229`: `12`
- `plan_count_match`: `1`
- `dry_run_complete`: `1`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`

## Boundary
- Do not apply these command replacements directly in this branch.
- Do not collapse branch-local manifests into one global manifest unless the key conflict is resolved explicitly.
- The next branch may patch the latest handoff generator, but it must compare regenerated old/new manifest rows before merge.
- Keep this separate from runtime semantics and panel-engine code.

## Files
- `research/prognostics/build_latest_handoff_manifest_repro_refresh_dry_run_v1.py`
- `research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_dry_run_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_230_LATEST_HANDOFF_MANIFEST_REPRO_REFRESH_DRY_RUN_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_latest_handoff_manifest_repro_refresh_dry_run_v1.py \
  research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_dry_run_v1.py
python3 research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_dry_run_v1.py
python3 research/prognostics/build_latest_handoff_manifest_repro_refresh_dry_run_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/latest_handoff_manifest_repro_refresh_dry_run_br230_check"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Expected Result
- The dry-run should report `branch_spec_rows=14`.
- The dry-run should report `old_private_tmp_literal_rows=41`.
- The dry-run should report `proposed_private_tmp_literal_rows=0`.
- The dry-run should report `input_manifest_added_rows=12`.
- The dry-run should report `global_manifest_key_conflict_rows=1`.
- The dry-run should report `plan_count_match=1`.
- The dry-run should report `dry_run_complete=1`.

## Next Decision
- Build the next branch as `latest_handoff_manifest_repro_refresh_apply_generator`.
- Patch the latest handoff generator only after regenerating and comparing the manifest rows against this dry-run.

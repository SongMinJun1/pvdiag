<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_231_LATEST_HANDOFF_MANIFEST_REPRO_APPLY_GENERATOR_V1

## Summary
- This patch applies the BR-230 dry-run result to `research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py`.
- It replaces stale generated `/private/tmp` repro text with portable branch-local input-manifest placeholders and a caller-provided output-root placeholder.
- It does not execute evidence builders, change runtime semantics, change threshold semantics, change operator-facing outputs, or touch `pv_ae/panel_day_engine.py`.

## Why
- BR-229 found `41` stale repro temp literals in the generated latest handoff manifest.
- BR-230 proved the safe replacement shape: `12` refresh-required rows should use branch-local input manifests, while `2` repo-doc rows should remain unchanged.
- A single global input manifest remains unsafe because at least one key conflict exists across branch contexts; branch-local manifests preserve handoff lineage without pretending the artifacts already live in repo.

## Applied Shape
- `LATEST_HANDOFF_MANIFEST_DIR` is the caller-provided directory containing per-branch input manifests.
- `LATEST_HANDOFF_OUTPUT_ROOT` is the caller-provided root where regenerated evidence outputs should be written.
- BR-064 through BR-076 generated repro commands now use `--input-manifest "${LATEST_HANDOFF_MANIFEST_DIR}/..._input_manifest.json"` where the target builder supports manifestized inputs.
- BR-064 through BR-076 generated artifact paths now point under `${LATEST_HANDOFF_OUTPUT_ROOT}/...`.
- BR-076 now uses `--repo-root "$(pwd)"` instead of a stale checkout path.
- BR-066 and BR-077 repo-doc rows are intentionally preserved as repo-local documentation artifacts.

## Observed Result
- `branch_spec_rows`: `14`
- `applied_manifestized_repro_rows`: `12`
- `repo_doc_preserved_rows`: `2`
- `manual_review_rows`: `0`
- `repro_private_tmp_literal_rows`: `0`
- `artifact_private_tmp_literal_rows`: `0`
- `br230_old_repro_temp_literal_rows`: `41`
- `applied_repro_temp_literal_drop_rows`: `41`
- `input_manifest_command_rows`: `12`
- `manifest_dir_placeholder_rows`: `12`
- `output_root_placeholder_rows`: `12`
- `repo_root_pwd_rows`: `1`
- `parameterized_artifact_rows`: `12`
- `repo_artifact_rows`: `2`
- `operator_promotion_allowed_sum`: `0`
- `engine_patch_allowed_sum`: `0`
- `threshold_patch_allowed_sum`: `0`
- `br230_expectation_match`: `1`
- `apply_check_complete`: `1`

## Boundary
- Do not treat `${LATEST_HANDOFF_OUTPUT_ROOT}` artifacts as existing repo artifacts.
- Do not collapse branch-local input manifests into a single global manifest without a separate collision-resolution patch.
- Do not promote this handoff text into runtime behavior; it is documentation/repro portability only.
- The next branch should run a broader generated latest-handoff portability closure audit against the emitted manifest files.

## Files
- `research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py`
- `research/prognostics/smoke_test_panel_day_engine_latest_evidence_handoff_manifest_v1.py`
- `research/prognostics/check_latest_handoff_manifest_repro_refresh_apply_v1.py`
- `research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_apply_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_231_LATEST_HANDOFF_MANIFEST_REPRO_APPLY_GENERATOR_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_latest_evidence_handoff_manifest_v1.py \
  research/prognostics/smoke_test_panel_day_engine_latest_evidence_handoff_manifest_v1.py \
  research/prognostics/check_latest_handoff_manifest_repro_refresh_apply_v1.py \
  research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_apply_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_latest_evidence_handoff_manifest_v1.py
python3 research/prognostics/smoke_test_latest_handoff_manifest_repro_refresh_apply_v1.py
python3 research/prognostics/check_latest_handoff_manifest_repro_refresh_apply_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/latest_handoff_manifest_repro_apply_br231_check"
git diff --check
```

## Expected Result
- The latest handoff manifest smoke should pass.
- The BR-231 apply check should report `branch_spec_rows=14`.
- The BR-231 apply check should report `applied_manifestized_repro_rows=12`.
- The BR-231 apply check should report `repo_doc_preserved_rows=2`.
- The BR-231 apply check should report `repro_private_tmp_literal_rows=0`.
- The BR-231 apply check should report `artifact_private_tmp_literal_rows=0`.
- The BR-231 apply check should report `applied_repro_temp_literal_drop_rows=41`.
- The BR-231 apply check should report `apply_check_complete=1`.

## Next Decision
- Build the next branch as `latest_handoff_manifest_portability_closure_audit`.
- Regenerate latest handoff manifest outputs and audit that parameterized repro commands are readable, portable, and still separated from runtime behavior.

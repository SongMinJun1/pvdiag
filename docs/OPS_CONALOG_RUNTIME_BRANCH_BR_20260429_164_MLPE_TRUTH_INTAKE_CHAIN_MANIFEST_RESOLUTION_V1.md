<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_164_MLPE_TRUTH_INTAKE_CHAIN_MANIFEST_RESOLUTION_V1

## Purpose
- BR-163 reduced the MLPE generated dependency review from `31` rows to `13` rows.
- `12/13` remaining rows belonged to the truth-intake chain.
- BR-164 replaces those truth-intake hardcoded temp input defaults with a tracked manifest/resolver path.

## Boundary
- No `pv_ae/panel_day_engine.py` semantic edit.
- No truth intake, threshold patch, engine patch, or canonical truth write approval.
- No generated upstream artifact is converted into a static evidence file.
- Existing explicit CLI inputs are preserved and take precedence over manifest resolution.
- User-filled inputs remain guarded; BR-164 does not weaken the reviewed-checklist/reviewer-decision fail-closed checks.

## New Contract/Resolver
- Manifest: `research/prognostics/contracts/mlpe_field_trial_v1/truth_intake_chain/mlpe_field_trial_truth_intake_chain_manifest_v1.csv`
- Resolver helper extension: `research/prognostics/mlpe_field_trial_chain_manifest_v1.py`
- Smoke: `research/prognostics/smoke_test_mlpe_field_trial_truth_intake_chain_manifest_v1.py`

## Changed Consumers
- `build_mlpe_field_trial_truth_seed_review_packet_v1.py`
- `build_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py`
- `build_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py`
- `build_mlpe_field_trial_truth_intake_preflight_checklist_v1.py`
- `build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py`
- `build_mlpe_field_trial_truth_materialization_precheck_v1.py`
- `build_mlpe_field_trial_sidecar_truth_package_contract_v1.py`

## Evidence
- Generated dependency review rows changed:
  - before BR-164: `13`
  - after BR-164: `1`
- Remaining generated dependency rows:
  - `mlpe_truth_replay_chain_manifest = 1`
  - `mlpe_truth_intake_chain_manifest = 0`
  - `mlpe_capture_chain_manifest = 0`
- Path portability dependency contracts now report:
  - `mlpe_upstream_generated_artifact_input = 1`
  - `mlpe_user_filled_input = 7`
  - `mlpe_chain_directory_bundle_input = 0`
- Safe static repo-contract replacement candidates remain `0`.

## Validation
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/mlpe_field_trial_chain_manifest_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_truth_intake_chain_manifest_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_chain_manifest_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_review_packet_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_future_truth_intake_candidate_package_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_checklist_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_materialization_precheck_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_sidecar_truth_package_contract_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_truth_intake_chain_manifest_path_audit_br164_check"
python3 research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_truth_intake_chain_manifest_dependency_review_br164_check"
```

## Decision
- BR-164 is ready for review.
- The next cleanup lane should be BR-165 replay-chain manifest resolution for the final `1` generated dependency row.
- Keep replay separate because it sits downstream of sidecar package/replay-scorecard semantics.

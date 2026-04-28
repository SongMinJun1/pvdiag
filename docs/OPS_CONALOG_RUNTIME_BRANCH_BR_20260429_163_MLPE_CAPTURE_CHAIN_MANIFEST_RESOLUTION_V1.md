<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_163_MLPE_CAPTURE_CHAIN_MANIFEST_RESOLUTION_V1

## Purpose
- BR-162 showed `31` remaining MLPE generated/chain defaults after static template/schema cleanup.
- `18/31` belonged to the capture-chain lane.
- BR-163 replaces those capture-chain hardcoded temp input defaults with a tracked manifest/resolver path.

## Boundary
- No `pv_ae/panel_day_engine.py` semantic edit.
- No truth intake, threshold patch, engine patch, or canonical truth write approval.
- No generated upstream artifact is converted into a static evidence file.
- Existing explicit CLI inputs are preserved and take precedence over manifest resolution.

## New Contract/Resolver
- Manifest: `research/prognostics/contracts/mlpe_field_trial_v1/capture_chain/mlpe_field_trial_capture_chain_manifest_v1.csv`
- Resolver helper: `research/prognostics/mlpe_field_trial_chain_manifest_v1.py`
- Smoke: `research/prognostics/smoke_test_mlpe_field_trial_capture_chain_manifest_v1.py`

## Changed Consumers
- `build_mlpe_field_trial_operator_intake_guide_v1.py`
- `build_mlpe_field_trial_package_manifest_v1.py`
- `build_mlpe_field_trial_adjudication_handoff_guard_v1.py`
- `check_mlpe_field_trial_pre_adjudication_dry_run_gate_v1.py`
- `build_mlpe_field_trial_real_capture_intake_watchlist_v1.py`
- `build_mlpe_field_trial_capture_return_validator_v1.py`
- `build_mlpe_field_trial_capture_return_evidence_resolver_v1.py`
- `build_mlpe_field_trial_capture_return_rerun_preflight_v1.py`
- `build_mlpe_field_trial_returned_capture_adjudication_packet_v1.py`
- `build_mlpe_field_trial_final_label_intake_schema_v1.py`
- `build_mlpe_field_trial_label_to_truth_gate_v1.py`

## Evidence
- Path portability dependency rows changed:
  - before BR-163: `31`
  - after BR-163: `13`
- Remaining rows:
  - `mlpe_upstream_generated_artifact_input = 12`
  - `mlpe_chain_directory_bundle_input = 1`
  - `mlpe_user_filled_input = 7`
- Capture-chain lane remaining count: `0`
- Generated dependency review now reports:
  - `mlpe_truth_intake_chain_manifest = 12`
  - `mlpe_truth_replay_chain_manifest = 1`
- Safe static repo-contract replacement candidates remain `0`.

## Validation
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/mlpe_field_trial_chain_manifest_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_capture_chain_manifest_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_capture_chain_manifest_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_capture_chain_manifest_path_audit_br163_check"
python3 research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_capture_chain_manifest_dependency_review_br163_check"
```

## Decision
- BR-163 is ready for review.
- The next cleanup lane should be BR-164 truth-intake chain manifest resolution for the remaining `12` truth-intake rows.
- The final replay row should remain separate because it depends on downstream replay/scorecard semantics.

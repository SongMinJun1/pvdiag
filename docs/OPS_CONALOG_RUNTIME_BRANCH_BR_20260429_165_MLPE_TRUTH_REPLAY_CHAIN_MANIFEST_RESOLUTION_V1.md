<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_165_MLPE_TRUTH_REPLAY_CHAIN_MANIFEST_RESOLUTION_V1

## Purpose
- BR-164 reduced the MLPE generated dependency review from `13` rows to `1` row.
- The final row belonged to the truth-replay scorecard handoff from BR-137 sidecar package output.
- BR-165 replaces that hardcoded temp input default with a tracked manifest/resolver path.

## Boundary
- No `pv_ae/panel_day_engine.py` semantic edit.
- No truth intake, threshold patch, engine patch, canonical truth write, or performance-improvement claim approval.
- No generated upstream artifact is converted into a static evidence file.
- Existing explicit CLI inputs are preserved and take precedence over manifest resolution.

## New Contract/Resolver
- Manifest: `research/prognostics/contracts/mlpe_field_trial_v1/truth_replay_chain/mlpe_field_trial_truth_replay_chain_manifest_v1.csv`
- Resolver helper extension: `research/prognostics/mlpe_field_trial_chain_manifest_v1.py`
- Smoke: `research/prognostics/smoke_test_mlpe_field_trial_truth_replay_chain_manifest_v1.py`

## Changed Consumer
- `build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py`

## Evidence
- Generated dependency review rows changed:
  - before BR-165: `1`
  - after BR-165: `0`
- Remaining generated dependency rows:
  - `mlpe_capture_chain_manifest = 0`
  - `mlpe_truth_intake_chain_manifest = 0`
  - `mlpe_truth_replay_chain_manifest = 0`
- Path portability dependency contracts now report:
  - `mlpe_upstream_generated_artifact_input = 0`
  - `mlpe_chain_directory_bundle_input = 0`
  - `mlpe_user_filled_input = 7`

## Validation
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/mlpe_field_trial_chain_manifest_v1.py \
  research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_truth_replay_chain_manifest_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_truth_replay_chain_manifest_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_replay_scorecard_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_truth_replay_chain_manifest_path_audit_br165_check"
python3 research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_truth_replay_chain_manifest_dependency_review_br165_check"
```

## Decision
- BR-165 is ready for review.
- The generated/chain input dependency cleanup lane is closed at `0` remaining rows.
- Remaining portability work should not reopen this lane unless new generated input defaults are added; next cleanup choices are user-filled guarded defaults, output defaults, or unrelated live temp references.

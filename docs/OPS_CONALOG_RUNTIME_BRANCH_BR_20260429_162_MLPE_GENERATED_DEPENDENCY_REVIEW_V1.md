<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_162_MLPE_GENERATED_DEPENDENCY_REVIEW_V1

## Purpose
- BR-160 closed user-filled default risk.
- BR-161 moved static MLPE template/schema defaults into repo-tracked contract artifacts.
- BR-162 reviews the remaining MLPE default references that still point at generated upstream artifacts or chain directory bundles.
- This branch intentionally does not replace those defaults yet. The goal is to prevent an unsafe static-file rewrite where the dependency is actually a generated chain output.

## Boundary
- No `pv_ae/panel_day_engine.py` edits.
- No runtime diagnosis semantic change.
- No truth intake, threshold patch, engine patch, or canonical truth write approval.
- No static repo-contract replacement for generated artifact rows.

## New Artifacts
- Builder: `research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py`
- Smoke: `research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py`
- Detail output: `mlpe_field_trial_generated_dependency_review_v1.csv`
- Summary output: `mlpe_field_trial_generated_dependency_review_summary_v1.csv`
- Note output: `mlpe_field_trial_generated_dependency_review_note_v1.md`
- JSON output: `mlpe_field_trial_generated_dependency_review_v1.json`

## Evidence Summary
- Reviewed dependency rows: `31`
- `mlpe_upstream_generated_artifact_input`: `27`
- `mlpe_chain_directory_bundle_input`: `4`
- Next patch lane split:
  - `mlpe_capture_chain_manifest`: `18`
  - `mlpe_truth_intake_chain_manifest`: `12`
  - `mlpe_truth_replay_chain_manifest`: `1`
- Safe static repo-contract replacement candidates: `0`
- Rows requiring upstream generation: `31`
- Rows requiring explicit input or manifest resolution: `31`
- Runtime semantic change allowed rows: `0`

## Decision
- These remaining MLPE defaults are not equivalent to BR-161 static template/schema contracts.
- They should not be converted directly into tracked static files.
- The safe next patch is to introduce a bounded chain-manifest or explicit-upstream-input resolution path, starting with the capture-chain segment because it contains the largest share (`18/31`) and stays upstream of truth intake.

## Reproduction
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py

python3 research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_field_trial_generated_dependency_review_br162_check"

python3 research/prognostics/smoke_test_mlpe_field_trial_generated_dependency_review_v1.py
```

## Next Branch Candidate
- `BR-20260429-163`: capture-chain manifest resolution.
- Proposed scope:
  - Keep generated artifacts generated.
  - Avoid static contract substitution.
  - Add a chain manifest or resolver for capture-chain defaults only.
  - Preserve current explicit CLI override behavior.
  - Keep approval/write sums at `0`.

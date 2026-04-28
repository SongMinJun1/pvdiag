<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_168_MLPE_OUTPUT_DEFAULT_REVIEW_V1

## Purpose
- BR-166 separated MLPE output defaults from generated/input dependency cleanup.
- BR-167 improved the remaining user-filled input guard UX without loosening fail-closed behavior.
- BR-168 reviews MLPE output defaults as a write-location lane, not an input-evidence lane.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not rewrite all `/private/tmp` output defaults in bulk.
- Do not treat output defaults as generated artifact inputs or user-filled evidence inputs.
- Do not claim diagnosis, truth, threshold, or performance improvement.

## Review Method
- Read the path portability audit rows.
- Filter:
  - `workflow_lane = mlpe_field_trial`
  - `match_role = research_temp_output_default_reference`
- Emit a dedicated review artifact with:
  - source script,
  - default variable,
  - default output directory,
  - CLI `--output-dir` override flag,
  - input/generation/runtime semantic flags,
  - recommended resolution.

## Expected Interpretation
- These rows are output destinations, so they are lower risk than input defaults.
- They can still create local clutter if defaults are used repeatedly.
- Reproducible, reviewer-facing, and packaged runs should pass an explicit `--output-dir`.
- A future shared output-root policy can clean them more elegantly than a bulk path rewrite.

## Expected Counts
- MLPE output default rows: `36`
- CLI `--output-dir` override rows: `36`
- missing CLI override rows: `0`
- input dependency rows: `0`
- generated dependency rows: `0`
- runtime semantic change allowed rows: `0`
- mass rewrite recommended rows: `0`

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_output_default_review_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_output_default_review_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_output_default_review_v1.py

python3 research/prognostics/build_mlpe_field_trial_output_default_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_field_trial_output_default_review_br168_check"

python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_output_default_review_br168_path_audit_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/mlpe_field_trial_output_default_review_br168_check`
- `/private/tmp/mlpe_output_default_review_br168_path_audit_check`

## Decision
- BR-168 closes MLPE output defaults as non-blocking for dependency cleanup.
- Keep local dev output defaults for now, but require explicit `--output-dir` in reproducible/reviewer-facing commands.
- Next cleanup can inspect the broader `p1_live_temp_reference` rows or non-MLPE output defaults without reopening MLPE generated/input dependency closure.

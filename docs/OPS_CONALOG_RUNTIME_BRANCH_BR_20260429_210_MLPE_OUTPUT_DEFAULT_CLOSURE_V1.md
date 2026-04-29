# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_210_MLPE_OUTPUT_DEFAULT_CLOSURE_V1

## Summary
- This patch closes the MLPE field-trial output-default lane as a static, non-semantic cleanup check.
- It verifies that current MLPE output defaults are write destinations with explicit `--output-dir` override support.
- It does not change diagnosis, truth, threshold, engine, runtime packaging, or operator-facing behavior.

## Why This Patch Exists
- BR-168 separated output defaults from input/generated dependency cleanup and found 36 write-destination defaults.
- BR-209 later added one closure builder with its own output default, so the current repository count is 37.
- Without this closure audit, that drift would be easy to misread as a new unresolved input dependency.

## Closure Contract
- Expected output default rows: `37`
- Distinct source files: `37`
- Required checks per row:
  - `cli_output_dir_override_flag = 1`
  - `writes_only_default_flag = 1`
  - `input_dependency_flag = 0`
  - `generated_dependency_flag = 0`
  - `runtime_semantic_change_allowed_flag = 0`
  - `mass_rewrite_recommended_flag = 0`
  - `recommended_resolution = keep_dev_temp_default_but_require_explicit_output_dir_for_reproducible_runs`

## Scope Boundary
- Changed:
  - `research/prognostics/build_mlpe_field_trial_output_default_closure_v1.py`
  - `research/prognostics/smoke_test_mlpe_field_trial_output_default_closure_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - MLPE input manifest resolution logic
  - generated dependency logic
  - truth, threshold, engine, or operator-facing runtime semantics
  - packaged runtime outputs

## Self-Count Guard
- BR-210 itself requires `--output-dir`.
- It intentionally does not define a default output directory.
- That keeps the closure script from adding a 38th output-default row.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_output_default_closure_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_output_default_closure_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_output_default_closure_v1.py

python3 research/prognostics/build_mlpe_field_trial_output_default_closure_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_field_trial_output_default_closure_br210_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `output_default_rows=37`
- `distinct_source_file_count=37`
- `closure_pass_count=37`
- `closure_fail_count=0`
- `missing_cli_output_dir_override_rows=0`
- `input_dependency_rows=0`
- `generated_dependency_rows=0`
- `runtime_semantic_change_allowed_rows=0`
- `mass_rewrite_recommended_rows=0`
- `missing_check_count=0`
- `closure_complete=1`

## Next Decision
- MLPE output defaults can stay as developer-local write destinations for now.
- Reproducible, reviewer-facing, or packaged runs should continue passing explicit `--output-dir`.
- Continue next with static directory references or broader repo organization cleanup without reopening the closed input/generated dependency lanes.

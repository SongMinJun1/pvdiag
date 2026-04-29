# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_216_PREPATCH_SCORECARD_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1

## Summary
- This patch closes the 4 prepatch scorecard static directory contract gaps found by BR-215.
- It adds optional `--input-manifest` resolution while retaining each legacy default path and each explicit CLI override.
- It does not rewrite static defaults, change runtime semantics, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-215 found 4 prepatch scorecard static directory rows.
- 0 rows were contract-closed.
- 4 rows had explicit CLI flags but lacked `--input-manifest` and manifest resolver handling.
- This branch patches only those input-contract gaps before any default rewrite discussion.

## Changed Contracts
- `build_panel_day_engine_result_delta_scorecard_v1.py`
  - Adds `--input-manifest`
  - Resolves `prepatch_runbook_summary` from manifest, explicit CLI, or legacy default
- `check_panel_day_engine_algorithm_prepatch_runbook_v1.py`
  - Adds `--input-manifest`
  - Resolves `packet_input`, `common_cause_strong_blocker_input`, `common_cause_exact_search_input`, `common_cause_structural_input`, and `common_cause_trace_input`
  - `common_cause_exact_search_input` and `common_cause_trace_input` are included because the runbook should resolve all upstream common-cause gate inputs consistently once manifest mode is available
- `compare_panel_day_engine_result_delta_scorecards_v1.py`
  - Adds `--input-manifest`
  - Resolves `baseline_scorecard_summary` and `post_scorecard_summary`

## Closure Result
- Prepatch scorecard directory rows: `4`
- Source files: `3`
- Contract closed rows: `4`
- Contract gap rows: `0`
- Explicit CLI argument rows: `4`
- Input-manifest argument rows: `4`
- Manifest resolver rows: `4`
- Legacy default retained rows: `4`
- Missing check count: `0`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`
- Contract complete: `1`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_216_PREPATCH_SCORECARD_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1.md`
  - `research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py`
  - `research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py`
  - `research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py`
  - `research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py`
  - prepatch scorecard smoke tests that now exercise manifest mode
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - result score semantics
  - prepatch runbook gate logic
  - truth, threshold, engine, or operator-facing behavior
  - static default path strings
  - path portability scanner semantics

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py \
  research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py \
  research/prognostics/check_panel_day_engine_algorithm_prepatch_runbook_v1.py \
  research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py \
  research/prognostics/smoke_test_prepatch_scorecard_static_directory_contract_gap_v1.py \
  research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py \
  research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py \
  research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_compare_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_algorithm_prepatch_runbook_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_compare_v1.py
python3 research/prognostics/smoke_test_prepatch_scorecard_static_directory_contract_gap_v1.py

python3 research/prognostics/build_prepatch_scorecard_static_directory_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/prepatch_scorecard_static_directory_contract_closure_br216_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `prepatch_directory_rows=4`
- `source_file_count=3`
- `contract_closed_rows=4`
- `contract_gap_rows=0`
- `input_manifest_arg_rows=4`
- `manifest_resolver_rows=4`
- `explicit_cli_arg_rows=4`
- `legacy_default_retained_rows=4`
- `missing_check_count=0`
- `contract_complete=1`

## Next Decision
- Do not bulk-rewrite prepatch scorecard static defaults.
- Treat the closure audit and manifest-mode smokes as regression guards.
- Move to the remaining voltage-preserved static directory lane only after this branch is merged.

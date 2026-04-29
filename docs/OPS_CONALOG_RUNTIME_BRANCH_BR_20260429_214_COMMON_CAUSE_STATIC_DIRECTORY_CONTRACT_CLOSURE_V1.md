# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_214_COMMON_CAUSE_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1

## Summary
- This patch closes the 5 common-cause static directory contract gaps found by BR-213.
- It adds optional `--input-manifest` resolution while retaining each legacy default path and each explicit CLI override.
- It does not rewrite static defaults, change runtime semantics, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-213 found 8 common-cause static directory rows.
- 3 rows were already contract-closed.
- 5 rows had explicit CLI flags but lacked `--input-manifest` and manifest resolver handling.
- This branch patches only those input-contract gaps before any default rewrite discussion.

## Changed Contracts
- `build_panel_day_engine_common_cause_structural_blocker_review_v1.py`
  - Adds `--input-manifest`
  - Resolves `exact_seed_input` from manifest, explicit CLI, or legacy default
- `build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py`
  - Adds `--input-manifest`
  - Resolves `judgment_input` from manifest, explicit CLI, or legacy default
- `check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py`
  - Adds `--input-manifest`
  - Resolves `strong_blocker_input`, `exact_search_input`, `structural_input`, and `trace_input`
  - `exact_search_input` is included because the gate should resolve all upstream packet inputs consistently once manifest mode is available

## Closure Result
- Common-cause directory rows: `8`
- Source files: `5`
- Contract closed rows: `8`
- Contract gap rows: `0`
- Explicit CLI argument rows: `8`
- Input-manifest argument rows: `8`
- Manifest resolver rows: `8`
- Missing check count: `0`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`
- Contract complete: `1`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_214_COMMON_CAUSE_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1.md`
  - `research/prognostics/build_common_cause_static_directory_contract_gap_v1.py`
  - `research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py`
  - `research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py`
  - `research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py`
  - common-cause smoke tests that now exercise manifest mode
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - common-cause judgment semantics
  - truth, threshold, engine, or operator-facing behavior
  - static default path strings
  - path portability scanner semantics

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_common_cause_static_directory_contract_gap_v1.py \
  research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py \
  research/prognostics/build_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py \
  research/prognostics/check_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py \
  research/prognostics/smoke_test_common_cause_static_directory_contract_gap_v1.py \
  research/prognostics/smoke_test_panel_day_engine_common_cause_structural_blocker_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_common_cause_structural_blocker_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_strong_common_cause_blocker_regression_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_semantic_prepatch_gate_v1.py
python3 research/prognostics/smoke_test_common_cause_static_directory_contract_gap_v1.py

python3 research/prognostics/build_common_cause_static_directory_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/common_cause_static_directory_contract_closure_br214_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `contract_closed_rows=8`
- `contract_gap_rows=0`
- `input_manifest_arg_rows=8`
- `manifest_resolver_rows=8`
- `missing_check_count=0`
- `contract_complete=1`

## Next Decision
- Do not bulk-rewrite common-cause static defaults.
- Treat the closure audit and manifest-mode smokes as regression guards.
- Move to the next unresolved static directory lane only after this branch is merged.

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_220_STATIC_ARTIFACT_REFERENCE_CONTRACT_CLOSURE_V1

## Summary
- This patch closes the 2 static artifact contract gaps found by BR-219.
- It adds optional `--input-manifest` resolution to the two remaining static artifact consumers while preserving the existing explicit CLI flags and legacy default artifact paths.
- It also makes the BR-219 audit less brittle by allowing expected-contract lookup by `source_file + matched_text`, not only by line number.
- It adds a small fixture smoke so the two patched consumers are exercised with manifest-provided inputs, not only source-text audit checks.
- It does not change `pv_ae/panel_day_engine.py`, runtime semantics, truth, threshold, engine logic, or operator-facing outputs.

## Why This Patch Exists
- BR-219 found 10 `static_upstream_artifact_input` rows.
- 8 rows were already contract-closed.
- 2 rows had explicit CLI flags but lacked `--input-manifest` and manifest resolver support.
- Adding imports shifted the default-path line numbers in those two files, so the audit needed a stable fallback key to avoid treating harmless line drift as a contract failure.

## Patched Consumers
- `research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py`
  - Adds `--input-manifest`.
  - Resolves `gap_review_input` from explicit CLI, input manifest, or legacy default.
  - Records input resolution source in the generated note.
- `research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`
  - Adds `--input-manifest`.
  - Resolves `packet_input` from explicit CLI, input manifest, or legacy default.
  - Keeps gate behavior and fail/pass logic unchanged.

## Observed Contract State
- Static artifact rows: `10`
- Source files: `6`
- Contract closed rows: `10`
- Contract gap rows: `0`
- Explicit CLI argument rows: `10`
- Input-manifest argument rows: `10`
- Manifest resolver rows: `10`
- Legacy default retained rows: `10`
- Missing check count: `0`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`
- Contract complete: `1`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_220_STATIC_ARTIFACT_REFERENCE_CONTRACT_CLOSURE_V1.md`
  - `research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py`
  - `research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`
  - `research/prognostics/build_static_artifact_reference_contract_gap_v1.py`
  - `research/prognostics/smoke_test_static_artifact_contract_closure_inputs_v1.py`
  - `research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - static artifact default path strings
  - static artifact consumer selection/gate semantics
  - truth, threshold, engine, or operator-facing behavior

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py \
  research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py \
  research/prognostics/build_static_artifact_reference_contract_gap_v1.py \
  research/prognostics/smoke_test_static_artifact_contract_closure_inputs_v1.py \
  research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py

python3 research/prognostics/smoke_test_static_artifact_contract_closure_inputs_v1.py

python3 research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py

python3 research/prognostics/build_static_artifact_reference_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/static_artifact_reference_contract_gap_br220_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `static_artifact_rows=10`
- `source_file_count=6`
- `contract_closed_rows=10`
- `contract_gap_rows=0`
- `input_manifest_arg_rows=10`
- `manifest_resolver_rows=10`
- `explicit_cli_arg_rows=10`
- `legacy_default_retained_rows=10`
- `missing_check_count=0`
- `contract_complete=1`

## Next Decision
- Do not bulk-rewrite static artifact defaults.
- Treat the static artifact bucket as closed if this audit remains green.
- Continue only with remaining non-directory/non-artifact live-temp reference buckets, such as runtime result bundle inputs or embedded repro references, under the same audit-first boundary.

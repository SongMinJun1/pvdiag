# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_219_STATIC_ARTIFACT_REFERENCE_CONTRACT_GAP_V1

## Summary
- This patch audits the 10 `static_upstream_artifact_input` rows from BR-169.
- It confirms that static artifact references are not fully contract-closed yet.
- It does not rewrite artifact defaults, change runtime semantics, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-211 through BR-218 closed the `static_upstream_directory_input` bucket without bulk rewriting defaults.
- BR-169 still had a separate `static_upstream_artifact_input` bucket.
- This branch determines whether that artifact bucket is already manifest-aware or still needs a targeted patch.

## Observed Contract State
- Static artifact rows: `10`
- Source files: `6`
- Contract closed rows: `8`
- Contract gap rows: `2`
- Explicit CLI argument rows: `10`
- Input-manifest argument rows: `8`
- Manifest resolver rows: `8`
- Legacy default retained rows: `10`
- Missing check count: `4`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`
- Contract complete: `0`

## Gap Interpretation
- Gap rows already have explicit per-input CLI flags.
- Gap rows still lack:
  - `--input-manifest`
  - manifest resolver handling
- Gap files:
  - `research/prognostics/build_panel_day_engine_non_fault_morphology_observation_sidecar_v1.py`
  - `research/prognostics/check_panel_day_engine_fault_family_regression_prepatch_gate_v1.py`
- Already-closed artifact consumers include:
  - exact-family closure readiness review
  - fault-family regression pressure packet
  - algorithm prepatch runbook
  - common-cause semantic prepatch gate

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_219_STATIC_ARTIFACT_REFERENCE_CONTRACT_GAP_V1.md`
  - `research/prognostics/build_static_artifact_reference_contract_gap_v1.py`
  - `research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - static artifact consumer semantics
  - truth, threshold, engine, or operator-facing behavior
  - static default artifact path strings
  - path portability scanner semantics

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_static_artifact_reference_contract_gap_v1.py \
  research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py

python3 research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py

python3 research/prognostics/build_static_artifact_reference_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/static_artifact_reference_contract_gap_br219_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `static_artifact_rows=10`
- `source_file_count=6`
- `contract_closed_rows=8`
- `contract_gap_rows=2`
- `input_manifest_arg_rows=8`
- `manifest_resolver_rows=8`
- `explicit_cli_arg_rows=10`
- `legacy_default_retained_rows=10`
- `missing_check_count=4`
- `contract_complete=0`

## Next Decision
- Do not bulk-rewrite static artifact defaults.
- Patch only the 2 gap scripts with `--input-manifest` and manifest resolver support.
- Re-run this audit after that patch; expected closure should become `10/10`.

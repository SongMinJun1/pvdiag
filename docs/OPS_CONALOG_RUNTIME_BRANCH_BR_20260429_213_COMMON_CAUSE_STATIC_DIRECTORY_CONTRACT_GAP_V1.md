# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_213_COMMON_CAUSE_STATIC_DIRECTORY_CONTRACT_GAP_V1

## Summary
- This patch reviews the common-cause static directory lane after BR-211 and BR-212.
- It confirms that common-cause is not fully contract-closed yet.
- It does not rewrite paths, change runtime behavior, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-211 found 8 common-cause static directory references.
- BR-212 showed episode-truth was already contract-closed despite retaining legacy defaults.
- Common-cause needed the same closure check before we decide whether to patch code or leave legacy defaults alone.

## Observed Contract State
- Common-cause directory rows: `8`
- Source files: `5`
- Contract closed rows: `3`
- Contract gap rows: `5`
- Explicit CLI argument rows: `8`
- Input-manifest argument rows: `3`
- Manifest resolver rows: `3`
- Missing check count: `10`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`

## Gap Interpretation
- Closed rows already have:
  - `--input-manifest`
  - explicit per-input CLI flags
  - manifest resolver handling
- Gap rows still have explicit CLI flags but lack:
  - `--input-manifest`
  - manifest resolver handling

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_213_COMMON_CAUSE_STATIC_DIRECTORY_CONTRACT_GAP_V1.md`
  - `research/prognostics/build_common_cause_static_directory_contract_gap_v1.py`
  - `research/prognostics/smoke_test_common_cause_static_directory_contract_gap_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - common-cause builder behavior
  - truth, threshold, engine, or operator-facing semantics
  - path portability scanner semantics
  - historical evidence pointers

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_common_cause_static_directory_contract_gap_v1.py \
  research/prognostics/smoke_test_common_cause_static_directory_contract_gap_v1.py

python3 research/prognostics/smoke_test_common_cause_static_directory_contract_gap_v1.py

python3 research/prognostics/build_common_cause_static_directory_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/common_cause_static_directory_contract_gap_br213_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `common_cause_directory_rows=8`
- `source_file_count=5`
- `contract_closed_rows=3`
- `contract_gap_rows=5`
- `input_manifest_arg_rows=3`
- `manifest_resolver_rows=3`
- `explicit_cli_arg_rows=8`
- `missing_check_count=10`
- `contract_complete=0`

## Next Decision
- Do not bulk-rewrite common-cause paths yet.
- Next code patch should add `--input-manifest` and manifest resolver handling to the 5 gap rows before any default rewrite.
- Keep runtime semantic and bulk rewrite permission at 0.

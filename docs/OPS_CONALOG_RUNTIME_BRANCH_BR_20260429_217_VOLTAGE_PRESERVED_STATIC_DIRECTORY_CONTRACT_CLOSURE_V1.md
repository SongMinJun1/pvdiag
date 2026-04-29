# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_217_VOLTAGE_PRESERVED_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1

## Summary
- This patch audits the 4 voltage-preserved static directory rows found by BR-211.
- It confirms the lane is already contract-closed through existing optional `--input-manifest` resolution, explicit CLI overrides, and retained legacy defaults.
- It does not rewrite static defaults, change runtime semantics, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-211 left a 4-row `panel_engine_voltage_preserved` static directory lane.
- BR-193 through BR-196 had already added manifest resolution to the relevant voltage-preserved builders.
- This branch records that closure explicitly so the roadmap does not reopen the voltage-preserved lane as a pending rewrite target.

## Audited Contracts
- `build_panel_day_engine_voltage_preserved_positive_search_v1.py`
  - Resolves `shape_input` from manifest, explicit CLI, or legacy BR-089 default
  - Resolves `hold_input` from manifest, explicit CLI, or legacy BR-091 default
- `build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py`
  - Resolves `candidate_input` from manifest, explicit CLI, or legacy BR-092 default
- `build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py`
  - Resolves `source_map_input` from manifest, explicit CLI, or legacy BR-093 default

## Closure Result
- Voltage-preserved directory rows: `4`
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
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_217_VOLTAGE_PRESERVED_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1.md`
  - `research/prognostics/build_voltage_preserved_static_directory_contract_gap_v1.py`
  - `research/prognostics/smoke_test_voltage_preserved_static_directory_contract_gap_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - voltage-preserved search, packet, or attachment semantics
  - truth, threshold, engine, or operator-facing behavior
  - static default path strings
  - path portability scanner semantics

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_voltage_preserved_static_directory_contract_gap_v1.py \
  research/prognostics/smoke_test_voltage_preserved_static_directory_contract_gap_v1.py

python3 research/prognostics/smoke_test_voltage_preserved_static_directory_contract_gap_v1.py

python3 research/prognostics/build_voltage_preserved_static_directory_contract_gap_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/voltage_preserved_static_directory_contract_gap_br217_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `voltage_directory_rows=4`
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
- Do not bulk-rewrite voltage-preserved static defaults.
- Treat this audit and smoke as the regression guard for the voltage-preserved lane.
- Move to the remaining `panel_day_engine_evidence` static directory lane next.

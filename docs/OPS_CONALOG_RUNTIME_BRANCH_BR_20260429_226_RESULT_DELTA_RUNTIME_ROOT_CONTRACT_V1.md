# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_226_RESULT_DELTA_RUNTIME_ROOT_CONTRACT_V1

## Summary
- This patch closes the single p1 temp input-default gap left by BR-225.
- `build_panel_day_engine_result_delta_scorecard_v1.py` now resolves `runtime_root` from:
  - explicit `--runtime-root`
  - `--input-manifest` key `runtime_root`
  - retained legacy default when no manifest is provided
- It updates the p1 temp input-default audit so the current lane state is `15/15` closed.
- It does not rewrite the legacy default string or change scorecard semantics.

## Why This Patch Exists
- BR-225 found one true remaining gap:
  - `research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py:13`
  - `DEFAULT_RUNTIME_ROOT`
  - explicit CLI existed, but there was no source-specific manifest resolution for `runtime_root`.
- The safe fix is to add manifest resolution, not delete or bulk-rewrite historical defaults.

## Closure Result
- P1 temp input-default rows: `15`
- Closed rows: `15`
- Open gap rows: `0`
- MLPE guarded user-filled rows: `7`
- Non-MLPE manifest/explicit closed rows: `8`
- Explicit-CLI-only open rows: `0`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`
- Closure complete: `1`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_226_RESULT_DELTA_RUNTIME_ROOT_CONTRACT_V1.md`
  - `research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py`
  - `research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py`
  - `research/prognostics/build_p1_temp_input_default_gap_audit_v1.py`
  - `research/prognostics/smoke_test_p1_temp_input_default_gap_audit_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - scorecard metric semantics
  - truth, threshold, engine, runtime, or operator-facing behavior
  - legacy default path string

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py \
  research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py \
  research/prognostics/build_p1_temp_input_default_gap_audit_v1.py \
  research/prognostics/smoke_test_p1_temp_input_default_gap_audit_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py

python3 research/prognostics/smoke_test_p1_temp_input_default_gap_audit_v1.py

python3 research/prognostics/build_p1_temp_input_default_gap_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/p1_temp_input_default_gap_audit_br226_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `p1_temp_input_default_rows=15`
- `closed_rows=15`
- `open_gap_rows=0`
- `non_mlpe_manifest_or_explicit_closed_rows=8`
- `explicit_cli_only_open_rows=0`
- `closure_complete=1`

## Next Decision
- Treat P1 temp input defaults as closed unless the audit count changes.
- Move to p2 cleanup next, starting with historical evidence/repro references or documentation path normalization.
- Keep p2 cleanup separate from runtime semantics and panel-engine code.

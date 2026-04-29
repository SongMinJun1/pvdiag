# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_212_EPISODE_TRUTH_STATIC_DIRECTORY_CONTRACT_CLOSURE_V1

## Summary
- This patch closes the episode-truth static directory contract lane.
- It verifies that the 12 episode-truth static directory references already have `--input-manifest`, explicit per-input CLI flags, and `resolve_chain_input` handling.
- It does not rewrite legacy defaults, change runtime behavior, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-211 showed 48 unresolved static directory references across five workflow lanes.
- The episode-truth lane has 12 rows across 8 source files and is a coherent chain from BR-081 through BR-089.
- Before rewriting paths, we needed to know whether the lane is actually unsafe or merely retains legacy local defaults for continuity.

## Closure Contract
- Expected episode-truth directory rows: `12`
- Expected source files: `8`
- Required checks per row:
  - script supports `--input-manifest`
  - script uses `resolve_chain_input`
  - script exposes a matching explicit CLI input flag
  - legacy default is still detected and therefore backward-compatible
  - runtime semantic change allowed rows remain `0`
  - bulk rewrite allowed rows remain `0`

## Scope Boundary
- Changed:
  - `research/prognostics/build_episode_truth_static_directory_contract_closure_v1.py`
  - `research/prognostics/smoke_test_episode_truth_static_directory_contract_closure_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - episode-truth builder behavior
  - truth, threshold, engine, or operator-facing semantics
  - path portability scanner semantics
  - historical evidence pointers

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_episode_truth_static_directory_contract_closure_v1.py \
  research/prognostics/smoke_test_episode_truth_static_directory_contract_closure_v1.py

python3 research/prognostics/smoke_test_episode_truth_static_directory_contract_closure_v1.py

python3 research/prognostics/build_episode_truth_static_directory_contract_closure_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/episode_truth_static_directory_contract_closure_br212_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `episode_truth_directory_rows=12`
- `source_file_count=8`
- `contract_closed_rows=12`
- `contract_fail_rows=0`
- `input_manifest_arg_rows=12`
- `resolve_chain_input_rows=12`
- `explicit_cli_arg_rows=12`
- `legacy_default_retained_rows=12`
- `runtime_semantic_change_allowed_rows=0`
- `bulk_rewrite_allowed_rows=0`
- `contract_complete=1`

## Next Decision
- Episode-truth static directory references can stay as legacy defaults for local continuity.
- Reproducible runs should use `--input-manifest` or explicit per-input CLI flags.
- Continue with another static directory lane, likely common-cause or panel-day evidence, before considering any bulk rewrite.

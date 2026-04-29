# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_211_STATIC_DIRECTORY_REFERENCE_INVENTORY_V1

## Summary
- This patch inventories the unresolved static `/private/tmp` directory references after the MLPE input/output-default cleanup lanes.
- It classifies the 48 static directory references by workflow lane and source file.
- It does not rewrite paths, change runtime behavior, change truth/threshold/engine logic, or modify operator-facing outputs.

## Why This Patch Exists
- BR-169 split unresolved live temp references into directory, artifact, runtime-result, repro, and detector-literal buckets.
- BR-202..BR-210 closed the MLPE user-filled, generated, and output-default lanes.
- The next safe target is now the static directory bucket, but direct bulk rewrite is still unsafe because these rows point to upstream evidence bundles.

## Inventory Contract
- Expected static directory rows: `48`
- Expected source files: `29`
- Required interpretation:
  - `requires_manifest_or_explicit_directory_flag = 1`
  - `immediate_patch_allowed_flag = 0`
  - `bulk_rewrite_allowed_flag = 0`
  - `runtime_semantic_change_allowed_flag = 0`

## Workflow Split
| workflow_lane | expected rows |
|---|---:|
| `panel_day_engine_evidence` | 20 |
| `panel_engine_episode_truth` | 12 |
| `panel_engine_common_cause` | 8 |
| `panel_engine_prepatch_scorecard` | 4 |
| `panel_engine_voltage_preserved` | 4 |

## Scope Boundary
- Changed:
  - `research/prognostics/build_repo_static_directory_reference_inventory_v1.py`
  - `research/prognostics/smoke_test_repo_static_directory_reference_inventory_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - path portability scanner semantics
  - runtime result generation
  - truth, threshold, engine, and operator-facing semantics
  - historical evidence pointers

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_repo_static_directory_reference_inventory_v1.py \
  research/prognostics/smoke_test_repo_static_directory_reference_inventory_v1.py

python3 research/prognostics/smoke_test_repo_static_directory_reference_inventory_v1.py

python3 research/prognostics/build_repo_static_directory_reference_inventory_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/repo_static_directory_reference_inventory_br211_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `static_directory_rows=48`
- `source_file_count=29`
- `requires_manifest_or_explicit_directory_rows=48`
- `immediate_patch_allowed_rows=0`
- `bulk_rewrite_allowed_rows=0`
- `runtime_semantic_change_allowed_rows=0`
- `inventory_complete=1`

## Next Decision
- Do not bulk-rewrite the 48 directory literals.
- Pick one cohesive lane and add manifest/explicit-directory input handling with smoke coverage.
- The likely next candidates are:
  - `panel_engine_episode_truth`, because it is a coherent chain with 12 rows.
  - `panel_day_engine_evidence`, because it is the largest bucket with 20 rows.

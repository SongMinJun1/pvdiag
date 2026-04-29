<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_193_VOLTAGE_PRESERVED_SEARCH_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-192.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_positive_search_v1.py`.
- Let the BR-092 voltage-preserved positive search resolve its BR-089 shape review and BR-091 hold review inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change candidate tiering, search windows, known-overlap marking, manual-review readiness, positive-truth flags, threshold tuning flags, operator-facing flags, engine patch flags, or selected panel-day metrics.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` shape or hold input defaults in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-092 voltage-preserved positive-search builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `shape_input`
  - `hold_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the two volatile evidence inputs that were previously tied to `/private/tmp`.
- The data root remains a deliberate raw/core observation root, because it is the actual panel-day source for the search.
- The search remains a voltage-preserved positive-candidate evidence artifact only.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture candidate roles and search actions from the same fixture inputs and data root.
- A manifest missing `shape_input` or `hold_input` fails closed.
- Unsafe truth/threshold/operator-facing flags remain guarded by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_positive_search_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_positive_search_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the BR-093 confirmation packet path, but re-scan before patching.

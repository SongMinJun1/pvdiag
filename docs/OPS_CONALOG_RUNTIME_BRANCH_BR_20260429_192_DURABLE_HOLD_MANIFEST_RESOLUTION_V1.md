<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_192_DURABLE_HOLD_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-191.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_durable_hold_raw_shape_review_v1.py`.
- Let the BR-091 durable-hold raw-shape review resolve its BR-089 shape review input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change raw-shape decision assignment, positive-truth candidate flags, threshold tuning flags, operator-facing flags, engine patch flags, or selected-day raw metrics.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` shape input default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-091 durable-hold raw-shape review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `shape_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-089 shape review input that was previously tied to `/private/tmp`.
- The data root remains a deliberate raw/core observation root, because it is the actual raw waveform and panel-core source.
- The review remains a durable-hold raw-shape evidence review only.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same raw-shape decisions from the same fixture input and data root.
- A manifest missing `shape_input` fails closed.
- Unsafe input with patch flags still fails.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_durable_hold_raw_shape_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_durable_hold_raw_shape_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `br091_raw_hold_smoke_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the BR-092 voltage-preserved positive search, but re-scan before patching.

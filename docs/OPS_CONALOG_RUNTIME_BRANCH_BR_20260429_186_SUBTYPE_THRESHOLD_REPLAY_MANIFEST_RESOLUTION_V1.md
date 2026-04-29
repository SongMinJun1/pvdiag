<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_186_SUBTYPE_THRESHOLD_REPLAY_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-185.
- Target the remaining two-row evidence consumer: `build_panel_day_engine_subtype_threshold_replay_pilot_v1.py`.
- Let the BR-090 subtype-threshold replay pilot resolve BR-089 shape review and BR-084 reviewed-truth inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change replay rules, pilot decisions, precision/recall/F1 calculations, action queue rows, threshold tuning approval logic, or patch authorization flags.
- Do not wrap the repo-tracked BR-017 threshold candidate doc:
  - `--threshold-candidate-input`
- Do not remove the legacy `/private/tmp` evidence defaults in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-090 subtype-threshold replay pilot builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `shape_input`
  - `reviewed_truth_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note and JSON record whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this consumer as a two-row evidence-input consumer.
- This branch resolves only volatile evidence inputs that were previously tied to `/private/tmp`.
- BR-017 threshold candidates remain a stable criteria document, not a live evidence artifact.
- Threshold tuning approval and operator/engine/threshold patch authorization remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same pilot decisions from the same fixture inputs.
- A manifest missing `reviewed_truth_input` fails closed.
- Threshold tuning, operator-facing, engine-patch, and threshold-patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_subtype_threshold_replay_pilot_v1.py \
  research/prognostics/smoke_test_panel_day_engine_subtype_threshold_replay_pilot_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_subtype_threshold_replay_pilot_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `br090_threshold_replay_smoke_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the remaining single-row evidence consumers.
- Pick the next branch by inspecting explicit-input-supported `/private/tmp` dependencies, not note/repro literals.

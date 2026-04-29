<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_187_FAULT_FAMILY_REGRESSION_PRESSURE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-186.
- Target the next single-row evidence consumer: `build_panel_day_engine_fault_family_regression_pressure_packet_v1.py`.
- Let the BR-058 fault-family regression pressure packet resolve its BR-057 exact-family closure readiness input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change packet bucket assignment, counterexample bucket assignment, regression assertions, recommended next actions, promotion flags, or engine patch flags.
- Do not remove the legacy `/private/tmp` evidence default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-058 fault-family regression pressure packet builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `readiness_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified the remaining lane as single-row evidence consumers after the two-row consumers were handled.
- This branch resolves only the volatile BR-057 readiness input that was previously tied to `/private/tmp`.
- The packet remains regression/counterexample material only.
- Target exact closure, operator promotion, and engine patch candidate sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same packet buckets from the same fixture input.
- A manifest missing `readiness_input` fails closed.
- Target exact closure, operator promotion, and engine patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_fault_family_regression_pressure_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_fault_family_regression_pressure_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_fault_family_regression_pressure_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next single-row evidence consumer.
- Pick the next branch by inspecting explicit-input-supported `/private/tmp` dependencies, not note/repro literals.

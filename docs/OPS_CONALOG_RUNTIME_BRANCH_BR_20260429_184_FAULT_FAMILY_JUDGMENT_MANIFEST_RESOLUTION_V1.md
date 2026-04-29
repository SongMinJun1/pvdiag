<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_184_FAULT_FAMILY_JUDGMENT_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-183.
- Target the next two-row evidence consumer: `build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py`.
- Let the BR-064 fault-family judgment candidate packet resolve its cross-axis review and regression-pressure packet inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change judgment bucket assignment, family-track assignment, criteria interpretation, promotion flags, engine patch flags, or threshold candidate roles.
- Do not wrap repo-tracked criteria docs:
  - `--threshold-input`
  - `--subtype-input`
- Do not remove the legacy `/private/tmp` evidence defaults in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-064 fault-family judgment candidate packet builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `cross_axis_input`
  - `pressure_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this consumer as a two-row evidence-input consumer.
- This branch resolves only the volatile evidence inputs; repo-tracked threshold/subtype criteria remain stable docs inputs.
- The packet remains audit-only and review-only.
- Promotion and engine patch candidate sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same judgment buckets from the same fixture inputs.
- A manifest missing `pressure_input` fails closed.
- Operator promotion and engine-patch candidate sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_fault_family_judgment_candidate_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_fault_family_judgment_candidate_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `fault_family_judgment_packet_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 one-consumer-at-a-time evidence manifest resolution.
- The next practical two-row consumer is `build_panel_day_engine_physical_evidence_request_packet_v1.py`.

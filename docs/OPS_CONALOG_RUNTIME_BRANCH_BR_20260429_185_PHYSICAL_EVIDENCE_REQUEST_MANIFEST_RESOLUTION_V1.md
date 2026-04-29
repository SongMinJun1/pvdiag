<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_185_PHYSICAL_EVIDENCE_REQUEST_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-184.
- Target the next two-row evidence consumer: `build_panel_day_engine_physical_evidence_request_packet_v1.py`.
- Let the BR-070 physical evidence request packet resolve BR-069 confirmation and checklist inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change request priority, request status, evidence bundle naming, required-axis counting, acceptance criteria, handoff text, promotion flags, engine patch flags, or threshold patch flags.
- Do not remove the legacy `/private/tmp` evidence defaults in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-070 physical evidence request packet builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `confirmation_input`
  - `checklist_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this consumer as a two-row evidence-input consumer.
- This branch resolves only the volatile evidence inputs that were previously tied to `/private/tmp`.
- The packet remains acquisition-oriented and review-only.
- Operator promotion, engine patch candidate, and threshold patch allowed sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same evidence request bundle from the same fixture inputs.
- A manifest missing `checklist_input` fails closed.
- Operator promotion, engine-patch candidate, and threshold-patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_physical_evidence_request_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_physical_evidence_request_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `physical_evidence_request_packet_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 one-consumer-at-a-time evidence manifest resolution.
- The next branch should inspect the remaining evidence consumers and select the next explicit-input-supported `/private/tmp` dependency without changing runtime semantics.

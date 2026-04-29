<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_199_VOLTAGE_TRUTH_ACQUISITION_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-198.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py`.
- Let the BR-099 truth-acquisition queue resolve its required BR-098 attachment input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change acquisition axis logic, priority logic, panel/site summary logic, collector template generation, truth-intake readiness logic, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not remove the legacy `/private/tmp` BR-098 attachment directory default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-099 voltage-preserved truth-acquisition queue builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `attachment_input`
- Explicit `--attachment-input` and explicit `--attachment-dir` continue to win over manifest paths.
- If a manifest is provided and `attachment_input` is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether `attachment_input` came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-098 evidence input that was previously tied to `/private/tmp`.
- BR-099 remains a collector-facing acquisition queue only, not a truth write, threshold approval, or engine patch.
- Collected evidence must still be fed back through BR-098 before any separate truth-intake branch can exist.
- Operator-facing, engine, and threshold patch sums remain guarded at `0`.

## Expected Result
- Existing explicit `--attachment-dir` smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture queue priorities and collector-template counts from the same fixture inputs.
- A manifest missing `attachment_input` fails closed.
- Unsafe authorizing BR-098 attachment rows remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Re-scan before patching; do not infer truth-intake or threshold-readiness changes from this manifest-only branch.

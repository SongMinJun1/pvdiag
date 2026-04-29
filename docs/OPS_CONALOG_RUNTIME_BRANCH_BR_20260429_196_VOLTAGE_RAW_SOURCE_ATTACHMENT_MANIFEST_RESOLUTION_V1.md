<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_196_VOLTAGE_RAW_SOURCE_ATTACHMENT_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-195.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py`.
- Let the BR-096 raw/source attachment resolve its BR-095 request input and BR-093 source-map input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change source-candidate trace logic, daily trace logic, attachment status, raw-file reference counting, common-cause context flags, raw-waveform independence policy, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` request directory or source-map defaults in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-096 voltage-preserved raw/source attachment builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `request_input`
  - `source_map_input`
- Explicit `--request-input`, explicit `--request-dir`, and explicit `--source-map-input` continue to win over manifest paths.
- If a manifest is provided and a wrapped input is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-095/BR-093 evidence inputs that were previously tied to `/private/tmp`.
- The data root remains a deliberate raw/core observation root, because it is the actual panel-day and raw CSV evidence source.
- BR-096 remains a raw/source traceability attachment only, not a truth write, threshold approval, independent confirmation, or engine patch.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit `--request-dir` and `--source-map-input` smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture attachment statuses from the same fixture inputs and data root.
- A manifest missing `request_input` or `source_map_input` fails closed.
- Unsafe authorizing request/source-map inputs remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the BR-097 confirmation gap-review path, but re-scan before patching.

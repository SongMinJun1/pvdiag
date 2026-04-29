<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_197_VOLTAGE_CONFIRMATION_GAP_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-196.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py`.
- Let the BR-097 confirmation-gap review resolve its BR-096 attachment index and daily trace inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change review bucket logic, checklist axes, summary counts, action queue semantics, vendor support interpretation, manual-site context handling, blocker clearance semantics, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not wrap vendor/manual inputs in this branch:
  - `--vendor-input`
  - `--manual-site-input`
- Do not remove the legacy `/private/tmp` BR-096 attachment directory default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-097 voltage-preserved confirmation-gap review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence inputs:
  - `attachment_input`
  - `daily_trace_input`
- Explicit `--attachment-input`, explicit `--daily-trace-input`, and explicit `--attachment-dir` continue to win over manifest paths.
- If a manifest is provided and a wrapped input is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-096 evidence inputs that were previously tied to `/private/tmp`.
- Vendor/manual evidence remains outside this manifest step because those inputs are stable reference/context layers and changing them would widen scope.
- BR-097 remains a confirmation-gap review only, not a truth write, threshold approval, independent confirmation, or engine patch.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit `--attachment-dir`, `--vendor-input`, and `--manual-site-input` smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture review buckets from the same fixture inputs.
- A manifest missing `attachment_input` or `daily_trace_input` fails closed.
- Unsafe authorizing BR-096 attachment/daily inputs remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the BR-098 independent-confirmation attachment path, but re-scan before patching.

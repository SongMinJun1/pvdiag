<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_194_VOLTAGE_CONFIRMATION_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-193.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py`.
- Let the BR-093 confirmation packet resolve its BR-092 candidate input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change confirmation packet grouping, review priority, candidate map, family summary, counterexample risk flags, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not remove the legacy `/private/tmp` candidate input default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-093 voltage-preserved confirmation-packet builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `candidate_input`
- Explicit CLI input continues to win over manifest paths.
- If a manifest is provided and `candidate_input` is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-092 candidate input that was previously tied to `/private/tmp`.
- BR-093 remains a confirmation packet only, not a truth write, threshold approval, or engine patch.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture packet priorities from the same fixture candidate input.
- A manifest missing `candidate_input` fails closed.
- Unsafe authorizing candidate inputs remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the BR-095 evidence-request packet path, but re-scan before patching.

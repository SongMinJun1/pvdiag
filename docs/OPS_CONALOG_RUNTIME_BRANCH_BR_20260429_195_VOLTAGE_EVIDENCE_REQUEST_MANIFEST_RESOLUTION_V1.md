<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_195_VOLTAGE_EVIDENCE_REQUEST_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-194.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py`.
- Let the BR-095 evidence-request packet resolve its BR-093 packet input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change evidence request priority, checklist axes, summary rows, counterexample clearance, raw-waveform independence policy, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not remove the legacy `/private/tmp` confirmation directory default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-095 voltage-preserved evidence-request builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `packet_input`
- Explicit `--packet-input` and explicit `--confirmation-dir` continue to win over manifest paths.
- If a manifest is provided and `packet_input` is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-093 packet input that was previously tied to `/private/tmp`.
- BR-095 remains an evidence request/checklist packet only, not a truth write, threshold approval, or engine patch.
- Raw waveform attachment remains support only; it is not upgraded into independent confirmation.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit `--confirmation-dir` smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture request priorities from the same fixture packet input.
- A manifest missing `packet_input` fails closed.
- Unsafe authorizing packet inputs remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Likely next target is the downstream voltage-preserved attachment/gap-review chain, but re-scan before patching.

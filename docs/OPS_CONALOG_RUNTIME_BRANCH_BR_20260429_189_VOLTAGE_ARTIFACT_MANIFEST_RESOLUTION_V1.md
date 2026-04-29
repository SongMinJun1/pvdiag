<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_189_VOLTAGE_ARTIFACT_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-188.
- Target the next downstream single-row evidence consumer: `build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py`.
- Let the BR-067 voltage-dominant physical-vs-artifact review resolve its BR-065 shape review input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change physical-vs-artifact bucket assignment, physical/artifact scores, peer/reference metrics, raw `data-root` reads, two-axis review readiness, promotion flags, or engine patch flags.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` shape input default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-067 voltage-dominant physical-vs-artifact review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `shape_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-065 shape review input that was previously tied to `/private/tmp`.
- The data root remains a deliberate raw/core observation root rather than a generated evidence artifact.
- The review remains physical-vs-artifact triage only.
- Operator promotion and engine patch candidate sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same physical-vs-artifact buckets from the same fixture input and data root.
- A manifest missing `shape_input` fails closed.
- Operator promotion and engine patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `voltage_dominant_artifact_review_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next downstream single-row evidence consumer.
- Likely next target is `build_panel_day_engine_raw_waveform_physical_support_review_v1.py`, selected by actual `/private/tmp` input dependency.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_188_LOCAL_MORPHOLOGY_SHAPE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-187.
- Target the next single-row evidence consumer: `build_panel_day_engine_local_morphology_family_shape_review_v1.py`.
- Let the BR-065 local morphology family-shape review resolve its BR-064 judgment packet input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change family-shape bucket assignment, morphology metrics, raw `data-root` reads, two-axis review readiness, promotion flags, or engine patch flags.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` packet default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-065 local morphology family-shape review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `packet_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this remaining lane as single-row evidence consumers after the larger two-row consumers were handled.
- This branch resolves only the volatile BR-064 judgment packet input that was previously tied to `/private/tmp`.
- The review remains shape-evidence triage only.
- Operator promotion and engine patch candidate sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same family-shape buckets from the same fixture input and data root.
- A manifest missing `packet_input` fails closed.
- Operator promotion and engine patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_local_morphology_family_shape_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_local_morphology_family_shape_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `local_morphology_shape_review_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next single-row evidence consumer.
- Likely next candidates are downstream shape consumers such as voltage-dominant physical-vs-artifact review or raw waveform physical support review, selected by actual `/private/tmp` input dependency.

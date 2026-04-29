<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_190_RAW_WAVEFORM_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-189.
- Target the next downstream single-row evidence consumer: `build_panel_day_engine_raw_waveform_physical_support_review_v1.py`.
- Let the BR-068 raw waveform physical-support review resolve its BR-067 review input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change raw waveform support bucket assignment, physical-support score, limitation score, raw timestamp ratio metrics, promotion flags, or engine patch flags.
- Do not wrap the data root in this branch:
  - `--data-root`
- Do not remove the legacy `/private/tmp` review input default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-068 raw waveform physical-support review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `review_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-067 review input that was previously tied to `/private/tmp`.
- The raw/core `data-root` remains a deliberate observation root, because it is the actual raw waveform source rather than a generated evidence artifact.
- The review remains support evidence only.
- Operator promotion and engine patch candidate sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same raw waveform support buckets from the same fixture input and data root.
- A manifest missing `review_input` fails closed.
- Operator promotion and engine patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `raw_waveform_physical_support_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next downstream single-row evidence consumer.
- Pick the next target by actual `/private/tmp` input dependency, not by branch number alone.

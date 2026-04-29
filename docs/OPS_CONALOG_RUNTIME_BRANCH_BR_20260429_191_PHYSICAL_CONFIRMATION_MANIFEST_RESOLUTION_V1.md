<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_191_PHYSICAL_CONFIRMATION_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-190.
- Target the next downstream single-row evidence consumer: `build_panel_day_engine_physical_confirmation_requirements_review_v1.py`.
- Let the BR-069 physical confirmation requirements review resolve its BR-068 raw review input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change confirmation bucket assignment, readiness level, confirmation-axis matching, manual evidence parsing, promotion flags, engine patch flags, or threshold patch flags.
- Do not wrap the manual evidence input in this branch:
  - `--manual-evidence-input`
- Do not remove the legacy `/private/tmp` raw review input default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-069 physical confirmation requirements review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `raw_review_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether the wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-068 raw review input that was previously tied to `/private/tmp`.
- The manual field evidence input remains a deliberate repo-local/optional evidence source rather than a generated evidence artifact.
- The review remains an independent-confirmation checklist only.
- Operator promotion, engine patch, and threshold patch sums remain guarded at `0`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same confirmation buckets from the same fixture input and manual evidence.
- A manifest missing `raw_review_input` fails closed.
- Operator promotion, engine patch, and threshold patch sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_physical_confirmation_requirements_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_physical_confirmation_requirements_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary `physical_confirmation_requirements_*` directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- BR-070 already has manifest coverage from BR-185, so pick the next target by actual current scan rather than by historical branch order alone.

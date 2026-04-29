<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_183_EXACT_FAMILY_CLOSURE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-182.
- Target the next evidence consumer: `build_panel_day_engine_exact_family_closure_readiness_review_v1.py`.
- Let the BR-057 exact-family closure readiness review resolve its three evidence CSV inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change closure classification, evidence grade, target/fault-family seed flags, recommended actions, or patch authorization values.
- Do not remove the legacy `/private/tmp` input defaults in this branch.
- Do not add new operator-facing outputs or performance claims.

## Change
- Add optional `--input-manifest` to the exact-family closure readiness review builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped CSV inputs:
  - `local_morphology_input`
  - `gap_review_input`
  - `observation_sidecar_input`
- Explicit CLI input flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- The generated note records whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this consumer as a three-row evidence-input consumer.
- This branch resolves only execution inputs; it does not reinterpret the closure taxonomy.
- The builder has no JSON output today, so this branch does not add a new artifact format only for bookkeeping.
- The exact-family review remains a readiness/review layer, not a production rule or threshold patch.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same closure classes from the same fixture inputs.
- A manifest missing `observation_sidecar_input` fails closed.
- Operator promotion and engine-patch candidate sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_exact_family_closure_readiness_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_exact_family_closure_readiness_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_exact_family_closure_readiness_review_v1.py

python3 research/prognostics/build_panel_day_engine_exact_family_closure_readiness_review_v1.py \
  --input-manifest /private/tmp/panel_day_engine_exact_family_closure_readiness_review_br183_fixture/inputs.json \
  --output-dir /private/tmp/panel_day_engine_exact_family_closure_readiness_review_br183_check

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_exact_family_closure_readiness_review_br183_check/panel_day_engine_exact_family_closure_readiness_review_v1.csv`
- `/private/tmp/panel_day_engine_exact_family_closure_readiness_review_br183_check/panel_day_engine_exact_family_closure_readiness_review_summary_v1.csv`
- `/private/tmp/panel_day_engine_exact_family_closure_readiness_review_br183_check/panel_day_engine_exact_family_closure_readiness_review_note_v1.md`

## Next Branch
- Continue BR-180 one-consumer-at-a-time evidence manifest resolution.
- The next practical candidates are the two-row consumers in the evidence contract, starting with `build_panel_day_engine_fault_family_judgment_candidate_packet_v1.py`.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_174_EPISODE_TRUTH_EVIDENCE_ATTACHMENT_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171, BR-172, and BR-173.
- Target only `build_panel_day_engine_episode_truth_evidence_attachment_v1.py`.
- Let the BR-085 evidence attachment builder resolve its BR-084 reviewed rows input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change evidence card content semantics or review template blank-field behavior.
- Do not infer or auto-fill truth labels.
- Do not approve threshold replay or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-084 default in this branch.

## Change
- Add optional `--input-manifest` to the BR-085 evidence attachment builder.
- The manifest may provide:
  - top-level `reviewed_rows_input`, or
  - `inputs.reviewed_rows_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--reviewed-rows-input` continues to win over manifest paths.
- If a manifest is provided and the defaulted reviewed-rows key is missing, the builder fails closed with a clear error.

## Why This Is Safer
- BR-170 identified episode-truth chain inputs that should be manifest or explicit-input driven.
- BR-171 covered the BR-087 worksheet input edge.
- BR-172 covered the BR-088 conservative adjudication input edge.
- BR-173 covered the BR-089 durable-shape input edge.
- BR-174 covers the BR-085 evidence attachment input edge without changing reviewer-card behavior.
- JSON/note outputs record whether reviewed rows input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same evidence card/template counts from the same fixture BR-084 rows.
- A bad manifest cannot override an explicit `--reviewed-rows-input`.
- Reviewer labels, evidence paths, threshold replay, and patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_evidence_attachment_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

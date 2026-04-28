<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_173_EPISODE_TRUTH_DURABLE_SHAPE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171 and BR-172.
- Target only `build_panel_day_engine_episode_truth_durable_shape_review_v1.py`.
- Let the BR-089 durable-shape review builder resolve its BR-088 adjudication input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change durable-shape classification rules.
- Do not approve threshold tuning or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-088 default in this branch.
- Do not manifest-wrap `--data-root`; it is a repo data-root/default runtime input, not the BR-170 live-temp chain dependency under cleanup.

## Change
- Add optional `--input-manifest` to the BR-089 durable-shape review builder.
- The manifest may provide:
  - top-level `br088_input`, or
  - `inputs.br088_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--br088-input` continues to win over manifest paths.
- If a manifest is provided and the defaulted BR-088 key is missing, the builder fails closed with a clear error.

## Why This Is Safer
- BR-170 identified episode-truth chain inputs that should be manifest or explicit-input driven.
- BR-171 covered the BR-087 worksheet input edge.
- BR-172 covered the BR-088 conservative adjudication input edge.
- BR-173 covers the next BR-089 durable-shape input edge without changing shape-review decisions.
- JSON/note outputs record whether BR-088 input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same durable-shape review counts from the same fixture BR-088 input.
- A bad manifest cannot override an explicit `--br088-input`.
- Threshold tuning and patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_durable_shape_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

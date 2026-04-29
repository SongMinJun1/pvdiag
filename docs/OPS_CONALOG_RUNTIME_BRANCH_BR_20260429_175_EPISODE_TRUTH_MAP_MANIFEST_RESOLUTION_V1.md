<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_175_EPISODE_TRUTH_MAP_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171 through BR-174.
- Target only `build_panel_day_engine_episode_truth_map_v1.py`.
- Let the BR-081 episode truth map builder resolve BR-065 shape review and BR-080 subtype-backlog inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change episode classification buckets, promotion readings, action queue rules, or truth status semantics.
- Do not infer or auto-fill truth labels.
- Do not approve threshold replay or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-065/BR-080 defaults in this branch.
- Do not wrap repo-tracked docs defaults for BR-017 episode, BR-017 G1, or BR-023 blocker inputs; those are not the live-temp references identified by BR-170 for this consumer.

## Change
- Add optional `--input-manifest` to the BR-081 episode truth map builder.
- The manifest may provide:
  - top-level `shape_input` and `backlog_input`, or
  - `inputs.shape_input` and `inputs.backlog_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--shape-input` and `--backlog-input` continue to win over manifest paths.
- If a manifest is provided and a defaulted `shape_input` or `backlog_input` key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether each manifest-wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-170 identified `shape_input` and `backlog_input` as the live-temp dependencies for this consumer.
- The other BR-081 inputs are repo-tracked docs artifacts and are intentionally left on their existing explicit/default path contract.
- This keeps the episode map reproducible without broad-rewriting all historical defaults.
- Bad manifest paths cannot override explicit CLI inputs, so reviewer/local override workflows remain stable.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same row and bucket counts from the same fixture shape/backlog inputs.
- A manifest missing a required defaulted key fails closed.
- Episode truth rows remain `truth_pending`.
- Operator-facing, engine-patch, and threshold-patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_map_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_map_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_map_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

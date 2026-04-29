<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_176_EPISODE_TRUTH_REVIEW_PACKET_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171 through BR-175.
- Target only `build_panel_day_engine_episode_truth_review_packet_v1.py`.
- Let the BR-082 episode truth review packet builder resolve the BR-081 episode map input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change review bucket selection, duplicate-lens collapse logic, review priorities, action queue rules, or reviewer label blanks.
- Do not infer or auto-fill truth labels.
- Do not approve threshold replay or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-081 default in this branch.

## Change
- Add optional `--input-manifest` to the BR-082 episode truth review packet builder.
- The manifest may provide:
  - top-level `episode_map_input`, or
  - `inputs.episode_map_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--episode-map-input` continues to win over manifest paths.
- If a manifest is provided and the defaulted `episode_map_input` key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether `episode_map_input` came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-170 identified `episode_map_input` as the live-temp dependency for this consumer.
- BR-175 made BR-081 map generation manifest-aware; BR-176 lets the next packet stage consume that output without hard-coding `/private/tmp`.
- Bad manifest paths cannot override explicit CLI inputs, so reviewer/local override workflows remain stable.
- The review packet remains a truth-review artifact, not a production or threshold patch.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same packet counts and duplicate-lens collapse counts from the same fixture map.
- A manifest missing `episode_map_input` fails closed.
- Reviewer truth labels remain blank.
- Operator-facing, engine-patch, and threshold-patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_review_packet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_review_packet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_review_packet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

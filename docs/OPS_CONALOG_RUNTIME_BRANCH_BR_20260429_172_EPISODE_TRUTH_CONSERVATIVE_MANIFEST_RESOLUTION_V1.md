<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_172_EPISODE_TRUTH_CONSERVATIVE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171.
- Target only `build_panel_day_engine_episode_truth_conservative_adjudication_v1.py`.
- Let the BR-088 conservative adjudication builder resolve its BR-087 worksheet input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change conservative adjudication decisions or label-filling rules.
- Do not create positive truth labels, threshold approval, or runtime semantic changes.
- Do not remove the legacy `/private/tmp` worksheet default in this branch.

## Change
- Add optional `--input-manifest` to the BR-088 conservative adjudication builder.
- The manifest may provide:
  - top-level `worksheet_input`, or
  - `inputs.worksheet_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--worksheet-input` continues to win over manifest paths.
- If a manifest is provided and the defaulted worksheet key is missing, the builder fails closed with a clear error.

## Why This Is Safer
- BR-170 identified episode-truth chain inputs that should be manifest or explicit-input driven.
- BR-171 covered the BR-087 worksheet producer/consumer edge.
- BR-172 covers the next consumer edge without altering the adjudication output semantics.
- JSON/note outputs record whether the worksheet came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same conservative adjudication counts from the same fixture worksheet.
- A bad manifest cannot override an explicit `--worksheet-input`.
- Positive labels and patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_conservative_adjudication_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_171_EPISODE_TRUTH_WORKSHEET_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-170 by wiring one episode-truth consumer to a manifest-aware input path.
- Target only `build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py`.
- Preserve existing explicit CLI input behavior and legacy defaults for old repro commands.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change diagnosis, truth labels, thresholds, or operator-facing runtime semantics.
- Do not delete legacy `/private/tmp` defaults in this branch.
- Do not bulk-rewrite other episode-truth consumers before their own manifest resolver branch.

## Change
- Add optional `--input-manifest` to the BR-087 adjudication worksheet builder.
- The manifest may provide:
  - top-level `trace_input` / `index_input`, or
  - `inputs.trace_input` / `inputs.index_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--trace-input` and `--index-input` continue to win over manifest paths.
- If a manifest is provided and a defaulted input is missing from it, the builder fails closed with a clear error.

## Why This Is Safer
- BR-170 found 12 episode-truth inputs that should be manifest or explicit-input driven.
- This branch resolves the first consumer without changing its result logic.
- The JSON/note output now records whether each input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same worksheet row counts from the same fixture inputs.
- A bad manifest cannot override explicit CLI inputs.
- Patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_adjudication_worksheet_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Apply the same manifest-or-explicit-input pattern to the next episode-truth consumer from BR-170, one consumer at a time.
- Keep each patch scoped to one resolver plus its smoke coverage.

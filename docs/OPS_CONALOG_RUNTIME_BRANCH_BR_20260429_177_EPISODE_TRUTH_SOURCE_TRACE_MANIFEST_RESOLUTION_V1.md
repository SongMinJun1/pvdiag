<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_177_EPISODE_TRUTH_SOURCE_TRACE_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171 through BR-176.
- Target only `build_panel_day_engine_episode_truth_source_trace_audit_v1.py`.
- Let the BR-086 source trace audit resolve BR-085 index/template inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change source-reference resolution, identity matching, trace-ready criteria, action queue rules, or safety assertions.
- Do not infer or auto-fill truth labels.
- Do not approve threshold replay or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-085 defaults in this branch.

## Change
- Add optional `--input-manifest` to the BR-086 source trace audit builder.
- The manifest may provide:
  - top-level `index_input` and `template_input`, or
  - `inputs.index_input` and `inputs.template_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--index-input` and `--template-input` continue to win over manifest paths.
- If a manifest is provided and a defaulted `index_input` or `template_input` key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether each input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-170 identified `index_input` and `template_input` as live-temp dependencies for this consumer.
- BR-174 made BR-085 evidence attachment manifest-aware; BR-177 lets BR-086 consume that output without hard-coding `/private/tmp`.
- Bad manifest paths cannot override explicit CLI inputs, so reviewer/local override workflows remain stable.
- Source trace readiness remains evidence availability only, not a truth label or replay approval.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same source-reference and trace-ready counts from the same fixture inputs.
- A manifest missing `index_input` or `template_input` fails closed.
- Unsafe BR-085 inputs with patch/replay authorization still fail.
- Reviewer truth labels, evidence path fills, threshold replay, and patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_source_trace_audit_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_source_trace_audit_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for the remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

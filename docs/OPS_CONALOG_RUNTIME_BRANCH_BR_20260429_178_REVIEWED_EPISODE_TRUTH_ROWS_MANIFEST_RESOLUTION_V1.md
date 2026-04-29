<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_178_REVIEWED_EPISODE_TRUTH_ROWS_MANIFEST_RESOLUTION_V1

## Purpose
- Continue the BR-170 episode-truth input cleanup after BR-171 through BR-177.
- Target only `build_panel_day_engine_reviewed_episode_truth_rows_v1.py`.
- Let the BR-084 reviewed episode truth rows builder resolve BR-082 packet and BR-083 guard inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change reviewer label validation, guard-green logic, truth-role mapping, replay-ready criteria, action queue rules, or patch authorization values.
- Do not infer or auto-fill truth labels.
- Do not approve threshold replay or runtime semantics from this branch.
- Do not remove the legacy `/private/tmp` BR-082/BR-083 defaults in this branch.
- Do not manifest-wrap `--review-input`; that file is an optional human-filled input and stays explicit.

## Change
- Add optional `--input-manifest` to the BR-084 reviewed rows builder.
- The manifest may provide:
  - top-level `packet_input` and `guard_json_input`, or
  - `inputs.packet_input` and `inputs.guard_json_input`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Explicit `--packet-input` and `--guard-json-input` continue to win over manifest paths.
- If a manifest is provided and a defaulted `packet_input` or `guard_json_input` key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether each manifest-wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-170 identified `packet_input` and `guard_json_input` as live-temp dependencies for this consumer.
- BR-176 made the BR-082 packet stage manifest-aware; BR-178 lets BR-084 consume that packet plus its guard without hard-coding `/private/tmp`.
- Bad manifest paths cannot override explicit CLI inputs, so reviewer/local override workflows remain stable.
- Reviewed rows remain truth-intake-only; replay-ready rows are not production authorization.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same reviewed-row and replay-ready counts from the same fixture packet/guard.
- A manifest missing `packet_input` or `guard_json_input` fails closed.
- Optional reviewer input behavior remains explicit and unchanged.
- Operator-facing, engine-patch, and threshold-patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_reviewed_episode_truth_rows_v1.py \
  research/prognostics/smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_reviewed_episode_truth_rows_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Next Branch
- Continue one-consumer-at-a-time manifest resolution for any remaining BR-170 episode-truth consumers.
- Keep each branch scoped to one resolver plus its smoke coverage.

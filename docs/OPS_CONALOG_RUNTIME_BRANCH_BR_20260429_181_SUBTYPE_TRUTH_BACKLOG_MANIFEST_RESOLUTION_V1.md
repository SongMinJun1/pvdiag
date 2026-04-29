<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_181_SUBTYPE_TRUTH_BACKLOG_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane.
- Target one high-impact consumer: `build_panel_day_engine_subtype_truth_expansion_backlog_v1.py`.
- Let the BR-080 subtype truth backlog builder resolve BR-079/064/065/069/072 evidence inputs from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change subtype backlog classification, priority, action queue, truth support counts, threshold replay, or patch authorization values.
- Do not wrap repo-tracked docs inputs:
  - `--subtype-map`
  - `--morphology-atlas`
  - `--shadow-summary-input`
- Do not remove the legacy `/private/tmp` defaults in this branch.
- Do not claim diagnosis, truth, threshold, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-080 subtype truth backlog builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped inputs:
  - `br079_gap_input`
  - `candidate_packet_input`
  - `shape_review_input`
  - `physical_confirmation_input`
  - `common_cause_search_input`
- Explicit CLI flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether each wrapped input came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 found this consumer has the largest evidence-lane input footprint: `6` live-temp rows, `5` manifest-required execution inputs, and `1` repro-only note row.
- This branch resolves the execution inputs only.
- Note/repro strings and scanner literals stay out of execution patches.
- The subtype truth backlog remains evidence planning; it does not authorize engine or threshold changes.

## Expected Result
- Existing explicit-input smoke behavior stays unchanged.
- Manifest-based execution produces the same subtype backlog and exact-truth-support counts from the same fixture inputs.
- A manifest missing `common_cause_search_input` fails closed.
- Operator-facing, engine-patch, and threshold-patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py \
  research/prognostics/smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_subtype_truth_expansion_backlog_v1.py

python3 research/prognostics/build_panel_day_engine_subtype_truth_expansion_backlog_v1.py \
  --repo-root "$(pwd)" \
  --output-dir /private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check/panel_day_engine_subtype_truth_expansion_backlog_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check/panel_day_engine_subtype_truth_expansion_backlog_summary_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check/panel_day_engine_subtype_truth_expansion_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check/panel_day_engine_subtype_truth_expansion_note_v1.md`
- `/private/tmp/panel_day_engine_subtype_truth_expansion_backlog_br181_check/panel_day_engine_subtype_truth_expansion_backlog_v1.json`

## Next Branch
- Continue BR-180 one-consumer-at-a-time evidence manifest resolution.
- The next practical candidate is `build_panel_day_engine_direction_assumption_audit_v1.py`, which has four execution inputs plus one repro-only note row.

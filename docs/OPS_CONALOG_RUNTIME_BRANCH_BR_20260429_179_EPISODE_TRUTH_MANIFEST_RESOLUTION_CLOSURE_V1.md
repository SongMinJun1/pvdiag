<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_179_EPISODE_TRUTH_MANIFEST_RESOLUTION_CLOSURE_V1

## Purpose
- Close the BR-170 episode-truth input-manifest resolution lane with a reproducible audit.
- Verify that every BR-170 manifest-required consumer has source, smoke, docs, and register coverage.
- Convert the hand-tracked "171 through 178 are done" claim into a repeatable static check.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change runtime verdicts, thresholds, truth labels, reviewer decisions, replay eligibility, or operator-facing outputs.
- Do not remove the legacy `/private/tmp` defaults in this branch.
- Do not add a new production manifest schema; this branch audits the already-wired consumer-level contract.

## Change
- Add `build_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py`.
- Add `smoke_test_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py`.
- Extend four earlier episode-truth smokes with missing-key fail-closed assertions:
  - `smoke_test_panel_day_engine_episode_truth_adjudication_worksheet_v1.py`
  - `smoke_test_panel_day_engine_episode_truth_conservative_adjudication_v1.py`
  - `smoke_test_panel_day_engine_episode_truth_durable_shape_review_v1.py`
  - `smoke_test_panel_day_engine_episode_truth_evidence_attachment_v1.py`
- Record BR-179 in the active branch register as the closure audit for BR-170 through BR-178.

## Closure Criteria
- Expected BR-170 consumers: `8`
- Expected manifest-required inputs: `12`
- Every consumer source must contain:
  - `--input-manifest`
  - manifest helper functions
  - expected explicit CLI flags
  - expected manifest keys
  - resolution-source recording: `explicit_cli`, `input_manifest`, `legacy_default`
- Every consumer smoke must cover:
  - manifest path resolution
  - explicit CLI override precedence
  - missing-key fail-closed behavior
- Every branch doc/register row must preserve the non-semantic boundary.

## Expected Result
- `closure_pass_count = 8`
- `closure_fail_count = 0`
- `unresolved_manifest_consumer_count = 0`
- `missing_check_count = 0`
- `operator_facing_change_allowed_sum = 0`
- `engine_patch_allowed_sum = 0`
- `threshold_patch_allowed_sum = 0`
- `closure_complete = 1`

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py \
  research/prognostics/smoke_test_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py

python3 research/prognostics/build_panel_day_engine_episode_truth_manifest_resolution_closure_v1.py \
  --repo-root "$(pwd)" \
  --output-dir /private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check/panel_day_engine_episode_truth_manifest_resolution_closure_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check/panel_day_engine_episode_truth_manifest_resolution_closure_summary_v1.csv`
- `/private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check/panel_day_engine_episode_truth_manifest_resolution_closure_v1.json`
- `/private/tmp/panel_day_engine_episode_truth_manifest_resolution_closure_br179_check/panel_day_engine_episode_truth_manifest_resolution_closure_note_v1.md`

## Decision
- BR-170 through BR-178 are treated as manifest-resolution complete only if this closure audit passes.
- This closes the current episode-truth manifest-resolution lane and allows the next cleanup lane to start from a mechanical check instead of memory.
- Any new episode-truth consumer should be added to the closure audit before relying on `/private/tmp` defaults.

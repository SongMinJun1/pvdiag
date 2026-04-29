<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_182_DIRECTION_ASSUMPTION_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-181.
- Target the next high-impact consumer: `build_panel_day_engine_direction_assumption_audit_v1.py`.
- Let the BR-083 direction assumption audit resolve BR-079/080/081/082 upstream roots from a manifest when no explicit CLI root is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change direction-assumption audit checks, expected counts, severity, action queue, truth labels, replay eligibility, threshold tuning, or patch authorization values.
- Do not remove the legacy `/private/tmp` root defaults in this branch.
- Do not treat note/repro strings as execution inputs.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-083 direction assumption audit builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped root inputs:
  - `br079_root`
  - `br080_root`
  - `br081_root`
  - `br082_root`
- Explicit CLI root flags continue to win over manifest paths.
- If a manifest is provided and a defaulted wrapped key is missing, the builder fails closed with a clear error.
- JSON and note outputs record whether each wrapped root came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- BR-180 classified this consumer as the second largest evidence-lane footprint: `5` rows total, `4` execution root inputs, and `1` repro-only note row.
- This branch resolves only the execution roots.
- The stale repro path is refreshed in the generated note because the builder is already being touched.
- The direction assumption audit remains guard-only; it does not authorize engine, threshold, truth, or operator-facing changes.

## Expected Result
- Existing explicit-root smoke behavior stays unchanged.
- Manifest-based execution produces the same check count and zero failures from the same fixture roots.
- A manifest missing `br082_root` fails closed.
- Operator-facing, engine-patch, and threshold-patch authorization sums remain `0`.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py \
  research/prognostics/smoke_test_panel_day_engine_direction_assumption_audit_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_direction_assumption_audit_v1.py

python3 research/prognostics/build_panel_day_engine_direction_assumption_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir /private/tmp/panel_day_engine_direction_assumption_audit_br182_check

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- `/private/tmp/panel_day_engine_direction_assumption_audit_br182_check/panel_day_engine_direction_assumption_audit_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br182_check/panel_day_engine_direction_assumption_audit_summary_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br182_check/panel_day_engine_direction_assumption_audit_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br182_check/panel_day_engine_direction_assumption_audit_note_v1.md`
- `/private/tmp/panel_day_engine_direction_assumption_audit_br182_check/panel_day_engine_direction_assumption_audit_v1.json`

## Next Branch
- Continue BR-180 one-consumer-at-a-time evidence manifest resolution.
- The next practical candidate is `build_panel_day_engine_exact_family_closure_readiness_review_v1.py`, which has three evidence input rows.

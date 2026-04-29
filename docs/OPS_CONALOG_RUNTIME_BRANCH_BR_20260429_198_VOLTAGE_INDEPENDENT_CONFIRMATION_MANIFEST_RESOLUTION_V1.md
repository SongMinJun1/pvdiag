<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_198_VOLTAGE_INDEPENDENT_CONFIRMATION_MANIFEST_RESOLUTION_V1

## Purpose
- Continue BR-180's `panel_day_engine_evidence` input-contract lane after BR-197.
- Target the next unresolved `/private/tmp` input dependency: `build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py`.
- Let the BR-098 independent-confirmation attachment resolve its required BR-097 gap-review input from a manifest when no explicit CLI input is provided.

## Boundary
- Do not edit `pv_ae/panel_day_engine.py`.
- Do not change independent-confirmation status logic, blocker-clearance logic, source-scan rows, template generation, truth-intake readiness logic, truth flags, threshold flags, operator-facing flags, or engine patch flags.
- Do not wrap optional evidence-fill inputs in this branch:
  - `--independent-evidence-input`
  - `--blocker-clearance-input`
- Do not wrap vendor/manual context inputs in this branch:
  - `--vendor-input`
  - `--manual-site-input`
- Do not remove the legacy `/private/tmp` BR-097 gap-review directory default in this branch.
- Do not claim diagnosis, truth, threshold, runtime, or performance improvement.

## Change
- Add optional `--input-manifest` to the BR-098 voltage-preserved independent-confirmation attachment builder.
- The manifest may provide:
  - top-level keys, or
  - `inputs.<key>`, or
  - artifact-style entries with `path`, `artifact_path`, or `static_path`.
- Manifest-wrapped evidence input:
  - `gap_review_input`
- Explicit `--gap-review-input` and explicit `--gap-review-dir` continue to win over manifest paths.
- If a manifest is provided and `gap_review_input` is missing, the builder fails closed with a clear error.
- The generated note and JSON payload record whether `gap_review_input` came from `explicit_cli`, `input_manifest`, or `legacy_default`.

## Why This Is Safer
- This branch resolves only the volatile BR-097 evidence input that was previously tied to `/private/tmp`.
- Optional independent evidence and blocker-clearance files remain explicit operator/reviewer inputs because silently defaulting or manifest-failing those optional fills would change workflow semantics.
- BR-098 remains an attachment/template gate only, not a truth write, threshold approval, or engine patch.
- Positive truth, threshold tuning, operator-facing change, and engine patch sums remain guarded at `0`.

## Expected Result
- Existing explicit `--gap-review-dir`, `--vendor-input`, `--manual-site-input`, `--independent-evidence-input`, and `--blocker-clearance-input` smoke behavior stays unchanged.
- Manifest-based execution produces the same fixture independent-confirmation statuses from the same fixture inputs.
- A manifest missing `gap_review_input` fails closed.
- Unsafe authorizing BR-097 gap-review rows remain blocked by the existing input assertions.

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py \
  research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Output Paths
- Smoke fixture outputs are generated under a temporary directory.
- Runtime pack smoke outputs remain temporary and are not committed.

## Next Branch
- Continue BR-180 evidence-lane manifest resolution with the next unresolved `/private/tmp` input dependency.
- Re-scan before patching; do not assume optional evidence-fill inputs should be converted to required manifest keys.

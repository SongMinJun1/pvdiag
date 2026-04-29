# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_207_MLPE_TRUTH_INTAKE_PREFLIGHT_REVIEW_MANIFEST_RESOLUTION_V1

## Summary
- BR-125 `mlpe_field_trial_truth_intake_preflight_review_validator` already failed closed for unsafe user-filled defaults.
- This patch adds optional manifest resolution for the reviewed preflight checklist CSV and records input-source provenance.
- It does not change review-validation buckets, future materialization-precheck candidate logic, canonical truth authorization, truth-intake authorization, threshold authorization, engine authorization, or operator-facing behavior.

## Why This Patch Exists
- 실증 reviewed preflight checklist CSV is user-filled reviewer evidence, so silent `/private/tmp` fallback is risky.
- The existing guard blocks accidental default use, but manifest support is needed for reproducible handoff and replay.
- This patch keeps the guard and adds a second safe entrypoint: explicit CLI or manifest.

## Input Resolution Contract
- Explicit `--reviewed-checklist` has priority over `--input-manifest`.
- If `--input-manifest` is supplied, `inputs.reviewed_checklist` must exist.
- Missing manifest keys fail closed rather than falling back to `/private/tmp`.
- Legacy default behavior remains guarded by `require_explicit_user_filled_input`.

Required manifest key:
- `reviewed_checklist`

## Scope Boundary
- Changed:
  - `research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py`
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - reviewed preflight validation bucket logic
  - future truth materialization precheck candidate logic
  - canonical truth, truth-intake, threshold, and engine approval sums
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged all-checks-passed / validation-failed fixture counts
- Runtime smoke should remain unchanged because this is an MLPE field-trial reviewed preflight validator patch only.

## Next Decision
- Continue with the remaining MLPE field-trial user-filled inputs.
- The likely next lane is truth-seed reviewer decision validator.

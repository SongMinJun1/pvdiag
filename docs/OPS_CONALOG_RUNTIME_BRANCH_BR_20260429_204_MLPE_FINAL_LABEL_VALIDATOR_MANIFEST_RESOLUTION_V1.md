# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_204_MLPE_FINAL_LABEL_VALIDATOR_MANIFEST_RESOLUTION_V1

## Summary
- BR-116 `mlpe_field_trial_final_label_validator` already failed closed for unsafe user-filled defaults.
- This patch adds optional manifest resolution for the reviewer final-label CSV and records input-source provenance.
- It does not change label-validation buckets, truth-gate candidate logic, truth-intake authorization, threshold authorization, engine authorization, or operator-facing behavior.

## Why This Patch Exists
- 실증 final-label CSV is user-filled reviewer evidence, so silent `/private/tmp` fallback is risky.
- The existing guard blocks accidental default use, but manifest support is needed for reproducible handoff and replay.
- This patch keeps the guard and adds a second safe entrypoint: explicit CLI or manifest.

## Input Resolution Contract
- Explicit `--label-input` has priority over `--input-manifest`.
- If `--input-manifest` is supplied, `inputs.label_input` must exist.
- Missing manifest keys fail closed rather than falling back to `/private/tmp`.
- Legacy default behavior remains guarded by `require_explicit_user_filled_input`.

Required manifest key:
- `label_input`

## Scope Boundary
- Changed:
  - `research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py`
  - `research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - final label validation bucket logic
  - truth-gate candidate logic
  - truth-intake, threshold, and engine approval sums
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged valid/failed label fixture counts
- Runtime smoke should remain unchanged because this is an MLPE field-trial final-label validator patch only.

## Next Decision
- Continue with the remaining MLPE field-trial user-filled inputs.
- The likely next lane is label-to-truth gate, real-label intake runbook, or truth-intake preflight review validator.

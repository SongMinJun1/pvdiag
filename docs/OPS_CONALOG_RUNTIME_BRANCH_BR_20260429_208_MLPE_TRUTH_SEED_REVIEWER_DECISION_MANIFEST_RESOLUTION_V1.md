# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_208_MLPE_TRUTH_SEED_REVIEWER_DECISION_MANIFEST_RESOLUTION_V1

## Summary
- BR-122 `mlpe_field_trial_truth_seed_reviewer_decision_validator` already failed closed for unsafe user-filled defaults.
- This patch adds optional manifest resolution for the truth-seed reviewer decision CSV and records input-source provenance.
- It does not change decision-validation buckets, future truth-intake candidate logic, canonical truth authorization, truth-intake authorization, threshold authorization, engine authorization, or operator-facing behavior.

## Why This Patch Exists
- 실증 truth-seed reviewer decision CSV is user-filled reviewer evidence, so silent `/private/tmp` fallback is risky.
- The existing guard blocks accidental default use, but manifest support is needed for reproducible handoff and replay.
- This patch keeps the guard and adds a second safe entrypoint: explicit CLI or manifest.

## Input Resolution Contract
- Explicit `--decision-input` has priority over `--input-manifest`.
- If `--input-manifest` is supplied, `inputs.decision_input` must exist.
- Missing manifest keys fail closed rather than falling back to `/private/tmp`.
- Legacy default behavior remains guarded by `require_explicit_user_filled_input`.

Required manifest key:
- `decision_input`

## Scope Boundary
- Changed:
  - `research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py`
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - decision-validation bucket logic
  - future truth-intake candidate logic
  - canonical truth, truth-intake, threshold, and engine approval sums
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged future-truth-intake candidate / validation-failed / issue fixture counts
- Runtime smoke should remain unchanged because this is an MLPE field-trial truth-seed reviewer decision validator patch only.

## Next Decision
- Continue with the remaining MLPE field-trial user-filled inputs.
- The likely next lane is another guarded user-filled reviewer artifact still lacking manifest resolution.

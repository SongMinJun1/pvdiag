# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_203_MLPE_CAPTURE_RETURN_EVIDENCE_RESOLVER_MANIFEST_RESOLUTION_V1

## Summary
- BR-112 `mlpe_field_trial_capture_return_evidence_resolver` already failed closed for unsafe user-filled defaults.
- This patch adds optional manifest resolution for the returned-capture CSV and records input-source provenance.
- It does not change evidence-resolution buckets, file-existence checks, byte-size checks, truth-intake authorization, threshold authorization, engine authorization, or operator-facing behavior.

## Why This Patch Exists
- 실증 returned-capture CSV is user-filled field evidence, so silent `/private/tmp` fallback is risky.
- The existing guard blocks accidental default use, but manifest support is needed for reproducible handoff and replay.
- This patch keeps the guard and adds a second safe entrypoint: explicit CLI or manifest.

## Input Resolution Contract
- Explicit `--returned-capture` has priority over `--input-manifest`.
- If `--input-manifest` is supplied, `inputs.returned_capture` must exist.
- Missing manifest keys fail closed rather than falling back to `/private/tmp`.
- Legacy default behavior remains guarded by `require_explicit_user_filled_input`.

Required manifest key:
- `returned_capture`

## Scope Boundary
- Changed:
  - `research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py`
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - capture-return validation logic
  - evidence-resolution bucket logic
  - evidence file-existence and byte-size checks
  - truth-intake, threshold, and engine approval sums
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged waiting/resolved evidence fixture counts
- Runtime smoke should remain unchanged because this is an MLPE field-trial evidence resolver patch only.

## Next Decision
- Continue with the remaining MLPE field-trial user-filled inputs.
- The likely next lane is final-label validator, label-to-truth gate, or real-label intake, depending on which unresolved user-filled default is safest to isolate next.

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_221_LIVE_TEMP_REVIEW_SELF_NOISE_FIX_V1

## Summary
- This patch fixes audit self-noise introduced by BR-220.
- BR-220 added fallback matching strings to `build_static_artifact_reference_contract_gap_v1.py`.
- Those fallback strings are not live inputs, but the broad path portability scanner saw their `/private/tmp/...` fragments and re-counted them as static directory inputs.
- This patch marks those fallback mapping lines with the existing `pp-self` scanner skip marker.

## Why This Patch Exists
- Before BR-220, the broad live-temp review had `68` rows.
- After BR-220, the broad live-temp review showed `78` rows because the static artifact audit builder itself contributed `10` false static-directory rows.
- That made the already-closed static directory bucket look reopened.
- The correct fix is not to rewrite the fallback strings or change diagnosis logic, but to mark them as scanner self-literals.

## Observed State After Fix
- Live-temp rows: `68`
- Static upstream directory input rows: `48`
- Static upstream artifact input rows: `10`
- Runtime result bundle input rows: `4`
- Embedded note repro command rows: `4`
- Intentional temp detector literal rows: `2`
- Static artifact audit builder self-noise rows: `0`
- Runtime semantic change allowed rows: `0`
- Bulk rewrite allowed rows: `0`

## Scope Boundary
- Changed:
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
  - `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_221_LIVE_TEMP_REVIEW_SELF_NOISE_FIX_V1.md`
  - `research/prognostics/build_static_artifact_reference_contract_gap_v1.py`
  - `research/prognostics/smoke_test_live_temp_review_self_noise_v1.py`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - static artifact contract closure logic
  - path portability scanner semantics
  - truth, threshold, engine, runtime, or operator-facing behavior

## Repro Commands
```bash
git status --short --branch

python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_static_artifact_reference_contract_gap_v1.py \
  research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py \
  research/prognostics/smoke_test_live_temp_review_self_noise_v1.py

python3 research/prognostics/smoke_test_static_artifact_reference_contract_gap_v1.py

python3 research/prognostics/smoke_test_live_temp_review_self_noise_v1.py

python3 research/prognostics/build_repo_live_temp_reference_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/repo_live_temp_reference_review_br221_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- `live_temp_reference_rows=68`
- `static_upstream_directory_input=48`
- `static_upstream_artifact_input=10`
- `runtime_result_bundle_input=4`
- `embedded_note_repro_command=4`
- `intentional_temp_detection_literal=2`

## Next Decision
- Continue with `runtime_result_bundle_input` contract audit.
- Do not treat BR-220 audit fallback literals as real upstream directories.
- Keep runtime semantic and bulk rewrite permissions at `0`.

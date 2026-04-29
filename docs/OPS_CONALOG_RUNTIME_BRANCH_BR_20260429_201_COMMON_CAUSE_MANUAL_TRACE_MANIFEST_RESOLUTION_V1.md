# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_201_COMMON_CAUSE_MANUAL_TRACE_MANIFEST_RESOLUTION_V1

## Summary
- BR-074 `common_cause_manual_trace_review` still read several volatile `/private/tmp` evidence inputs by default.
- This patch adds optional manifest resolution and records input-source provenance in the note output.
- It does not change trace classification, bridge scope assignment, semantic patch authorization, promotion, threshold, engine, or operator-facing behavior.

## Why This Patch Exists
- BR-074 is downstream of BR-072/BR-073 and helps explain common-cause structural blockers.
- The diagnostic value is weakened if the builder silently depends on deleted local temp artifacts.
- Input manifest resolution keeps the trace review reproducible without loosening any common-cause semantic guardrail.

## Input Resolution Contract
- Explicit CLI flags take priority over manifest paths.
- If `--input-manifest` is supplied, all required keys must exist.
- Missing manifest keys fail closed rather than falling back to `/private/tmp`.
- Legacy defaults remain available only when neither explicit CLI nor manifest is supplied.

Required manifest keys:
- `blocker_input`
- `current_input`
- `precursor_input`
- `rawonly_signal_input`

## Scope Boundary
- Changed:
  - `research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py`
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - trace outcome buckets
  - raw-only bridge / official-current bridge interpretation
  - semantic patch, promotion, threshold, engine, or operator-facing authorization
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_common_cause_manual_trace_review_v1.py \
  research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_common_cause_manual_trace_review_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged trace outcomes for fixture cases
- Runtime smoke should remain unchanged because this is an evidence-lane builder patch only.

## Next Decision
- Continue resolving the remaining non-manifest volatile input defaults.
- The next remaining group is mostly MLPE field-trial returned-capture/final-label/preflight validator inputs.

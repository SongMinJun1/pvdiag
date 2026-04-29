# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_200_COMMON_CAUSE_EXACT_SEED_MANIFEST_RESOLUTION_V1

## Summary
- BR-072 `common_cause_exact_seed_search` still used volatile `/private/tmp` defaults for 5 evidence inputs.
- This patch adds optional manifest resolution and input-source note recording.
- It does not change common-cause role classification, exact-family closure logic, reservoir/blocker/supportive tagging, or any promotion/patch authorization guardrail.

## Why This Patch Exists
- The common-cause lane is a high-value diagnostic safety axis, but it should not depend on deleted local temp artifacts.
- Previous BRs established that exact same-day closure must be separated from candidate reservoir and structural blockers.
- This change preserves that judgment boundary while making the inputs reproducible from explicit CLI or a manifest.

## Input Resolution Contract
- Explicit CLI flags have priority over the manifest.
- If `--input-manifest` is supplied, all 5 evidence keys must exist.
- Missing manifest keys fail closed instead of silently falling back to `/private/tmp`.
- Without a manifest or explicit CLI, the legacy defaults remain available for historical/manual replay only.

Required manifest keys:
- `judgment_input`
- `synchrony_input`
- `current_input`
- `precursor_input`
- `rawonly_signal_input`

## Scope Boundary
- Changed:
  - `research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py`
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py`
  - `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- Not changed:
  - `pv_ae/panel_day_engine.py`
  - exact closure / reservoir / structural blocker / supportive hint rules
  - operator promotion, engine patch, and threshold patch authorization
  - runtime/package outputs

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py \
  research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py

python3 research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Result
- The dedicated smoke verifies:
  - explicit CLI source recording
  - manifest source recording
  - explicit CLI override over a bad manifest
  - missing manifest key fail-closed behavior
  - unchanged role outcomes for the fixture cases
- Runtime smoke should remain unchanged because this is an evidence-lane builder patch only.

## Next Decision
- Continue scanning unresolved volatile evidence inputs.
- Prioritize remaining diagnostic-lane inputs before output-only defaults or historical docs.

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_227_P2_HISTORICAL_REFERENCE_BOUNDARY_AUDIT_V1

## Summary
- This patch starts the p2 cleanup lane after p1 live-temp and p1 temp-input defaults were closed.
- It adds a boundary audit for historical evidence/repro path references.
- It does not rewrite historical paths, move artifacts, change runtime semantics, or touch `pv_ae/panel_day_engine.py`.

## Why
- The remaining path-portability findings are mostly old evidence/provenance or repro text.
- Blindly replacing those paths would make the history look cleaner while making the evidence chain less honest.
- The safer boundary is:
  - preserve historical evidence pointers until a named stable artifact exists,
  - refresh historical doc repro text only when the doc is reopened for current handoff use,
  - rebuild generated handoff repro literals through a refreshed manifest instead of editing many literals by hand.

## Observed Result
- `path_portability_total_matches`: `1935`
- `p2_historical_total_rows`: `1325`
- `p2_historical_evidence_rows`: `1119`
- `p2_historical_repro_rows`: `206`
- `stable_replacement_required_rows`: `1119`
- `refresh_only_when_touching_doc_rows`: `156`
- `current_handoff_rebuild_candidate_rows`: `50`
- `immediate_bulk_rewrite_allowed_rows`: `0`
- `runtime_semantic_change_allowed_rows`: `0`
- `operator_facing_change_allowed_rows`: `0`
- `historical_boundary_complete`: `1`

## Boundary Classes
- `historical_evidence_provenance_pointer`: preserve until a named stable artifact exists.
- `historical_doc_repro_reference`: refresh only when the doc is reopened for current handoff or reproducibility use.
- `generated_handoff_repro_literal`: rebuild the handoff manifest when that handoff becomes current.

## Files
- `research/prognostics/build_p2_historical_reference_boundary_audit_v1.py`
- `research/prognostics/smoke_test_p2_historical_reference_boundary_audit_v1.py`
- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_227_P2_HISTORICAL_REFERENCE_BOUNDARY_AUDIT_V1.md`

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_p2_historical_reference_boundary_audit_v1.py \
  research/prognostics/smoke_test_p2_historical_reference_boundary_audit_v1.py
python3 research/prognostics/smoke_test_p2_historical_reference_boundary_audit_v1.py
python3 research/prognostics/build_p2_historical_reference_boundary_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/p2_historical_reference_boundary_audit_br227_check"
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Expected Result
- The audit should report `p2_historical_total_rows=1325`.
- The audit should report `immediate_bulk_rewrite_allowed_rows=0`.
- The audit should report `runtime_semantic_change_allowed_rows=0`.
- The audit should report `operator_facing_change_allowed_rows=0`.

## Next Decision
- Do not run a blanket historical path cleanup.
- If a current handoff needs those 50 generated repro literals, rebuild the handoff manifest through stable manifest/explicit inputs.
- If a historical evidence row is promoted into a current packet, materialize a named stable artifact first.

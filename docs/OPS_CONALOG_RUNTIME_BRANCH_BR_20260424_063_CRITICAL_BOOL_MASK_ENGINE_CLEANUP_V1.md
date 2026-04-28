<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_063_CRITICAL_BOOL_MASK_ENGINE_CLEANUP_V1

## Purpose
- Run the first small direct panel-engine patch through the BR-054/060/061/062 safety path.
- Replace targeted `critical_fault == True` pandas comparisons with one explicit `critical_fault_mask`.
- Keep source and packaged `panel_day_engine.py` byte-identical.
- This patch is a behavior-preserving cleanup, not a threshold, verdict, row-universe, or performance patch.

## Engine Change
- source:
  - `pv_ae/panel_day_engine.py`
- package mirror:
  - `release/conalog_full_runtime_v1/package/pv_ae/panel_day_engine.py`
- changed block:
  - `critical 2-stage split (confirmed vs suspect)`
- old pattern:
  - direct `out["critical_fault"] == True` comparisons
- new pattern:
  - `critical_fault_mask = out["critical_fault"].fillna(False).astype(bool)`
  - reuse `critical_fault_mask` for the confirmed/suspect split.

## Safety Review
- builder:
  - `research/prognostics/build_panel_day_engine_critical_bool_mask_safety_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_critical_bool_mask_safety_review_v1.py`

## Outputs
- `/private/tmp/panel_engine_critical_bool_mask_safety_review_check/panel_day_engine_critical_bool_mask_safety_review_v1.csv`
- `/private/tmp/panel_engine_critical_bool_mask_safety_review_check/panel_day_engine_critical_bool_mask_safety_review_summary_v1.csv`
- `/private/tmp/panel_engine_patch_safety_gate_check/panel_day_engine_patch_safety_gate_summary_v1.csv`
- `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_critical_bool_mask_check/panel_day_engine_result_delta_scorecard_summary_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_compare_critical_bool_mask_check/panel_day_engine_result_delta_scorecard_compare_summary_v1.csv`
- `/private/tmp/pvdiag_postmerge_j_conalog_smoke_critical_bool_mask_cleanup/result`

## Expected Result
- source/package hash equal:
  - `1`
- old targeted bool equality count:
  - `0`
- new critical mask count:
  - `1` in source and `1` in package
- behavior change claim:
  - `no_semantic_change_claim_only`

## Real Gate Result
- critical bool mask safety review:
  - `pass`
- BR-054 panel-engine patch safety gate:
  - `pass`
  - fail gate count: `0`
- BR-060 combined prepatch runbook:
  - `pass`
  - panel-engine gate status: `pass`
  - fault-family gate status: `pass`
  - engine change detected: `1`
- BR-061 post-patch scorecard:
  - `pass`
  - core diff count: `0`
  - raw-only candidate rows: `72`
  - precursor candidate rows: `0`
- BR-062 baseline-vs-post scorecard compare:
  - `pass`
  - changed metric count: `0`
  - core result changed flag: `0`

## Decision
- Accept this as the first direct engine-patch rehearsal because BR-054, BR-060, BR-061, and BR-062 checks remained green.
- Do not claim performance improvement from this cleanup.
- If result delta compare changes, stop and review before merging.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_critical_bool_mask_safety_review_v1.py --output-dir /private/tmp/panel_engine_critical_bool_mask_safety_review_check
```

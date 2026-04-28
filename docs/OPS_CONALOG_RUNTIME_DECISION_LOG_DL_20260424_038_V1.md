<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_038_V1

## Decision
- Accept BR-056 `non_fault_morphology_observation_sidecar` as the safe handling path for the 3 near-anchor rows from BR-055.
- Keep the rows in analyst/review evidence only.
- Do not patch `pv_ae/panel_day_engine.py` from this evidence.

## Reason
- The selected rows are `near_anchor_1_3d` and may contain useful local morphology context.
- They are still non-fault rows:
  - `raw_audit_status_ko == 미확정`
  - `raw_final_status_ko == 미확정`
  - hard fault row counts are all zero
- BR-055 showed the missing heuristic rows are expected under the existing fault-status gate, not an engine join bug.

## Evidence
- `/private/tmp/non_fault_morphology_observation_sidecar_check` reports:
  - `observation_rows = 3`
  - `site_counts = {'conalog': 2, 'gangui': 1}`
  - `signal_basis_counts = {'early_warning_only': 2, 'early_warning_plus_recovery': 1}`
  - `operator_promotion_allowed_sum = 0`
  - `engine_patch_candidate_sum = 0`
- Output sidecar:
  - `panel_day_engine_non_fault_morphology_observation_sidecar_v1.csv`
  - `panel_day_engine_non_fault_morphology_observation_sidecar_summary_v1.csv`
  - `panel_day_engine_non_fault_morphology_observation_sidecar_note_v1.md`

## Consequence
- The 3 BR-055 near-anchor rows are no longer an ambiguous "maybe report patch" bucket.
- They are preserved as non-fault morphology observation evidence only.
- Exact-family closure remains open.
- Algorithm gating remains blocked until stronger exact-family evidence exists.

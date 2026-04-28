<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FAULT_FAMILY_EVIDENCE_COVERAGE_MATRIX_V1

## Purpose
- Close the remaining BR-126 order-0 gap by mapping each MLPE/PV fault family to required evidence axes, supporting axes, blocking axes, current skill availability, and field-trial collection needs.
- Keep this as an evidence/readiness matrix only.
- Prevent future work from adding rules by intuition when a family is actually blocked by missing truth, missing telemetry, missing independent confirmation, or common-cause/artifact ambiguity.

## Source Records Read
This matrix is based on the current read-first stack:

- `docs/OPS_CONALOG_RUNTIME_ACTIVE_BRANCH_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_MASTER_CONTINUITY_REGISTER_V1.md`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_DIAGNOSTIC_SKILL_SHADOW_BACKLOG_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_WEAK_AXIS_STRENGTHENING_MATRIX_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_PRIORITY_GATE_MAP_V1.csv`
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_101_MLPE_FIELD_TRIAL_FAULT_TAXONOMY_V1.md`
- `docs/OPS_FAULT_COVERAGE_AND_MODEL_PERFORMANCE_V1.md`
- `release/final_delivery_v1/package/docs/panel_day_engine_fault_coverage_matrix_v1.csv`

## Matrix Artifact
- `docs/OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_126_FAULT_FAMILY_EVIDENCE_COVERAGE_MATRIX_V1.csv`

The CSV has one row per BR-101 top-level family:

- `normal`
- `panel_surface_environment_fault`
- `panel_physical_degradation_fault`
- `panel_electrical_submodule_fault`
- `connection_or_open_fault`
- `mlpe_device_or_control_fault`
- `measurement_or_communication_artifact`
- `inverter_or_group_side_fault`
- `site_common_cause_event`
- `unknown_or_compound`

For each row, the matrix separates availability into:

- `already_present_axes`
- `partially_present_axes`
- `field_trial_required_axes`
- `label_blocked_axes`

## Interpretation Rules
| rule | meaning |
| --- | --- |
| Required axes are not automatic verdict inputs | They define what evidence must be observable before a family can be discussed responsibly. |
| Supporting axes are weaker context | They can strengthen an evidence vector, but cannot close truth alone. |
| Blocking axes run first | Common-cause, group-side, MLPE/control, and telemetry artifact risks must be cleared before panel-local physical promotion. |
| Current status is conservative | `partial_shadow` means useful audit evidence exists, not that production classification is solved. |
| Missing telemetry is a real blocker | MLPE/control separation needs optimizer/control/communication fields from field trial capture. |
| Unknown is a valid bucket | Conflicting or incomplete axes should stay `unknown_or_compound` rather than being forced into a single physical family. |

## Current Decision
- Keep `AE`, `DTW`, `HS`, `EWS`, and `Rule` as distinct existing axes.
- Add CP, episode state, peer synchrony, physical invariant, artifact quality, and family evidence vector only as shadow/audit evidence.
- Do not add `shapelet`, `supervised classifier`, `survival/hazard`, or direct MLPE telemetry-state verdicts until field-trial labels/telemetry exist.
- Do not patch `pv_ae/panel_day_engine.py` from this matrix alone.

## What This Improves
- It makes the weak-axis discussion concrete by fault family instead of generic.
- It shows where the current raw/out data is enough for a shadow evidence vector and where real KTC ESS capture is required.
- It gives the next field-trial collection plan a checklist tied to diagnosis needs, not just a list of labels.

## Not Allowed From This Matrix Alone
- no operator-facing fault-family label
- no subtype promotion
- no precursor deletion or promotion
- no threshold loosening
- no canonical truth write
- no performance improvement claim
- no common-cause semantic loosening

## Next Gate
- Order 0 is now complete for BR-126: diagnostic skill backlog plus fault-family evidence coverage matrix.
- The next implementation remains blocked until reviewed preflight candidates exist.
- After reviewed preflight candidates exist, build the source/evidence materialization precheck package and keep canonical truth untouched.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
git diff --check
python3 -m py_compile pv_ae/panel_day_engine.py
```

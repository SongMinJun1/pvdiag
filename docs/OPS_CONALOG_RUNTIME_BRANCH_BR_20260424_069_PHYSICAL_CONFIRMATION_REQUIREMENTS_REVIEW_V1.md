<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_069_PHYSICAL_CONFIRMATION_REQUIREMENTS_REVIEW_V1

## Purpose
- Convert BR-068 raw waveform support into an explicit independent physical-confirmation checklist.
- Prevent a strong raw algorithmic waveform proxy from being mistaken for field confirmation.
- Keep this as audit-only evidence gating before any voltage-axis family threshold proposal.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_physical_confirmation_requirements_review_v1.py`

## Inputs
- BR-068 raw waveform physical-support review:
  - `/private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv`
- manual / field evidence context:
  - `docs/internal/manual_field_evidence_latest.csv`

## Outputs
- `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv`
- `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_checklist_v1.csv`
- `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_summary_v1.csv`
- `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_note_v1.md`

## Confirmation Rule
- Required independent axes for a packet-ready review:
  - exact-panel direct physical measurement:
    - IV curve
    - waveform capture
    - thermal / IR
    - measured voltage/current artifact
  - exact-panel maintenance or inspection record:
    - maintenance
    - inspection
    - repair
    - work-order / ticket
- Optional support axes:
  - exact-panel field reproducibility confirmation
  - independent repeated same-panel channel evidence
  - independent artifact / sensor / reference exclusion
- BR-068 raw waveform support is inherited as support evidence only.
  - It is not counted as independent confirmation.

## Real Data Result
- detail rows: `2`
- checklist rows: `10`
- independent confirmation met sum: `0`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Detail Snapshot
| site | panel_id | confirmation_bucket | required_axes_met | required_axes_total | manual_site_context_rows | manual_exact_panel_rows | raw_median_v_ratio | raw_median_i_ratio | required_next_evidence |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | `raw_supported_confirmation_gap_hold` | 0 | 2 | 5 | 0 | 0.632757 | 1.040984 | exact-panel direct physical measurement + maintenance/inspection |
| `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | `raw_supported_confirmation_gap_hold` | 0 | 2 | 0 | 0 | 0.564797 | 1.044655 | exact-panel direct physical measurement + maintenance/inspection |

## Axis Result
| axis | status | rows | satisfied |
| --- | --- | ---: | ---: |
| direct_physical_measurement | missing | 2 | 0 |
| maintenance_or_inspection_record | missing | 2 | 0 |
| field_reproducibility_confirmation | missing | 2 | 0 |
| same_panel_channel_repetition | raw_or_proxy_support_present_not_independent | 2 | 0 |
| independent_artifact_exclusion | raw_or_proxy_support_present_not_independent | 2 | 0 |

## Interpretation
- BR-068 made the physical voltage-axis hypothesis stronger.
- BR-069 shows the independent confirmation layer is still open:
  - `gangui` has site-level manual context, but not exact-panel usable validation.
  - `ktc_ess` has no matching manual context in the current manual evidence file.
- Therefore the current state is not threshold-ready.
- This is not a negative result for the hypothesis.
  - It means the evidence grade is still `raw support + confirmation gap`, not `confirmed physical fault family`.

## Decision
- Keep both rows in `raw_supported_confirmation_gap_hold`.
- Do not promote either row to operator-facing result.
- Do not authorize an engine patch or voltage-axis threshold patch.
- Next safe step is to collect exact-panel independent physical/inspection evidence, or keep these rows as regression/review material only.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py research/prognostics/smoke_test_panel_day_engine_physical_confirmation_requirements_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_physical_confirmation_requirements_review_v1.py
python3 research/prognostics/build_panel_day_engine_physical_confirmation_requirements_review_v1.py --raw-review-input /private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv --manual-evidence-input docs/internal/manual_field_evidence_latest.csv --output-dir /private/tmp/physical_confirmation_requirements_review_check
```

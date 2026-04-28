<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_070_PHYSICAL_EVIDENCE_REQUEST_PACKET_V1

## Purpose
- Convert BR-069 confirmation gaps into exact-panel evidence requests.
- Make the next non-code action explicit:
  - what evidence is needed
  - for which exact panel
  - why the request is high priority
  - why it still does not authorize thresholding

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_physical_evidence_request_packet_v1.py`

## Inputs
- BR-069 physical confirmation detail:
  - `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv`
- BR-069 physical confirmation checklist:
  - `/private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_checklist_v1.csv`

## Outputs
- `/private/tmp/physical_evidence_request_packet_check/panel_day_engine_physical_evidence_request_packet_v1.csv`
- `/private/tmp/physical_evidence_request_packet_check/panel_day_engine_physical_evidence_request_packet_summary_v1.csv`
- `/private/tmp/physical_evidence_request_packet_check/panel_day_engine_physical_evidence_request_packet_note_v1.md`

## Real Data Result
- request rows: `2`
- high evidence-gap priority rows: `2`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Request Snapshot
| site | panel_id | request_priority | requested_evidence_bundle | missing_required_axis_count | raw_daily_support_frac | raw_median_v_ratio | raw_median_i_ratio |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | `high_evidence_gap_priority` | `exact_panel_physical_measurement_plus_inspection` | 2 | 0.986301 | 0.632757 | 1.040984 |
| `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | `high_evidence_gap_priority` | `exact_panel_physical_measurement_plus_inspection` | 2 | 0.882883 | 0.564797 | 1.044655 |

## Requested Evidence
- Required direct physical measurement:
  - exact-panel IV curve
  - waveform capture
  - thermal / IR evidence
  - measured voltage/current artifact
- Required maintenance or inspection record:
  - exact-panel maintenance record
  - inspection record
  - repair record
  - work-order / ticket
- Acceptance criteria:
  - exact site
  - exact `panel_id`
  - date/time or inspection date
  - evidence type
  - whether it is usable for exact validation

## Interpretation
- BR-070 does not add new physical truth.
- It turns the current missing truth into an actionable request packet.
- Both rows are high priority because raw waveform support is strong:
  - `gangui`: daily support fraction `0.986301`
  - `ktc_ess`: daily support fraction `0.882883`
- Both rows remain blocked from thresholding because the required independent axes are still absent.

## Decision
- Keep the rows as exact-panel evidence requests.
- Do not promote either row to operator-facing result.
- Do not authorize an engine patch or voltage-axis threshold patch.
- After new evidence is attached, rerun BR-069 and BR-070 before reopening semantic threshold work.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py research/prognostics/smoke_test_panel_day_engine_physical_evidence_request_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_physical_evidence_request_packet_v1.py
python3 research/prognostics/build_panel_day_engine_physical_evidence_request_packet_v1.py --confirmation-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_review_v1.csv --checklist-input /private/tmp/physical_confirmation_requirements_review_check/panel_day_engine_physical_confirmation_requirements_checklist_v1.csv --output-dir /private/tmp/physical_evidence_request_packet_check
```

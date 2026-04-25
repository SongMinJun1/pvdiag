<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_095_VOLTAGE_PRESERVED_EVIDENCE_REQUEST_PACKET_V1

## Purpose
- Implement the next safe step after BR-093: convert confirmation packet rows into explicit evidence requests.
- Make every voltage-preserved review row answerable by a checklist instead of relying on scattered notes or memory.
- Keep raw waveform support separate from independent physical/field confirmation.
- Keep this branch evidence-request-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_packet_v1.csv` | BR-093 panel-level confirmation packet |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_checklist_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_packet_v1.json`

## Real Result
- evidence request rows: `14`
- checklist rows: `73`
- summary rows: `7`
- request priority counts:
  - `P0_independent_evidence_request`: `10`
  - `P0_counterexample_guarded_evidence_request`: `3`
  - `P1_shape_evidence_request`: `1`
- checklist axis counts:
  - `raw_waveform_attachment`: `14`
  - `physical_measurement_or_iv_curve`: `14`
  - `maintenance_or_inspection_record`: `14`
  - `common_cause_clearance`: `14`
  - `measurement_artifact_clearance`: `14`
  - `counterexample_clearance`: `3`
- site split:
  - `conalog`: `3` request rows / `15` checklist rows / `0` counterexample-risk rows
  - `gangui`: `9` request rows / `48` checklist rows / `3` counterexample-risk rows
  - `ktc_ess`: `2` request rows / `10` checklist rows / `0` counterexample-risk rows
- raw waveform independent confirmation rows: `0`
- evidence ready for truth use sum: `0`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Evidence Axes
| axis | required rows | role | independent confirmation? | interpretation |
| --- | ---: | --- | --- | --- |
| `raw_waveform_attachment` | 14 | algorithmic raw support | no | explains morphology but cannot approve truth/threshold alone |
| `physical_measurement_or_iv_curve` | 14 | independent physical confirmation | yes | exact-panel electrical/physical evidence before truth use |
| `maintenance_or_inspection_record` | 14 | independent field confirmation | yes | exact-panel field record before truth use |
| `common_cause_clearance` | 14 | blocker clearance | no | prevents site/root/group motion from becoming panel-local truth |
| `measurement_artifact_clearance` | 14 | blocker clearance | no | prevents sensor/reference/instrument effects from being promoted |
| `counterexample_clearance` | 3 | counterexample blocker clearance | no | required only for same-root known negative overlap rows |

## Interpretation
- BR-095 does not say any voltage-preserved row is confirmed.
- It says exactly what evidence is missing before a row can be considered for confirmed-positive truth.
- The most important guard is that raw waveform support remains `raw_waveform_is_independent_confirmation=0`.
- The three `gangui` counterexample-risk rows are separated into `P0_counterexample_guarded_evidence_request`.

## Safety Boundary
- BR-095 is an evidence request packet only.
- Request rows are not positive truth labels.
- All evidence/checklist rows start as missing.
- No threshold tuning, semantic loosening, operator-facing precursor promotion, or direct `panel_day_engine.py` edit is approved.
- Counterexample-risk rows cannot enter truth rebuild until an explicit clearance artifact exists.

## Ordered Next Path
1. Attach raw waveform windows and BR-092 source-candidate references to each request row.
2. Attach independent exact-panel physical measurement, IV curve, string/inverter trace, maintenance, inspection, or repair evidence where available.
3. Clear common-cause and measurement-artifact blockers explicitly.
4. Resolve the 3 counterexample-risk rows separately.
5. Only after evidence fields are populated, build a confirmation attachment artifact.

## Decision
- Accept BR-095 as the evidence request packet.
- Do not rebuild truth rows or rerun threshold replay yet.
- Use BR-095 as the next acquisition/reviewer worksheet for voltage-preserved candidates.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_evidence_request_packet_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --confirmation-dir /private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check --output-dir /private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check
```

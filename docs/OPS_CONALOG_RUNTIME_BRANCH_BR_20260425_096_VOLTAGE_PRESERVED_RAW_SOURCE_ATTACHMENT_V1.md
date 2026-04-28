<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_096_VOLTAGE_PRESERVED_RAW_SOURCE_ATTACHMENT_V1

## Purpose
- Implement the next safe step after BR-095: attach available raw/source traceability evidence to voltage-preserved evidence request rows.
- Convert the BR-095 worksheet from “what evidence is needed” into “which source-candidate rows, core daily rows, and raw CSV references already support each request”.
- Keep raw/source support separate from independent physical or maintenance confirmation.
- Keep this branch attachment-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check/panel_day_engine_voltage_preserved_evidence_request_packet_v1.csv` | BR-095 evidence request packet |
| `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv` | BR-093 candidate-to-packet map |
| `/Users/b9gc/pvdiag/data` | local data root for `panel_day_core.csv` and raw CSV references |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_candidate_trace_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_v1.json`

## Real Result
- attachment rows: `14`
- source candidate trace rows: `86`
- daily trace rows: `1698`
- attachment status counts:
  - `raw_source_trace_attached`: `14`
- raw file refs found: `1698`
- raw file refs missing: `0`
- site split:
  - `conalog`: `3` request rows / `16` source-candidate trace rows / `324` daily trace rows
  - `gangui`: `9` request rows / `52` source-candidate trace rows / `1043` daily trace rows
  - `ktc_ess`: `2` request rows / `18` source-candidate trace rows / `331` daily trace rows
- request-priority split:
  - `P0_independent_evidence_request`: `10` request rows / `66` source-candidate trace rows / `1050` daily trace rows
  - `P0_counterexample_guarded_evidence_request`: `3` request rows / `17` source-candidate trace rows / `498` daily trace rows
  - `P1_shape_evidence_request`: `1` request row / `3` source-candidate trace rows / `150` daily trace rows
- core signal days attached: `177`
- core voltage-preserved days attached: `1319`
- counterexample-risk rows: `3`
- raw waveform independent confirmation rows: `0`
- physical/maintenance evidence attached sum: `0`
- common-cause clearance attached sum: `0`
- measurement-artifact clearance attached sum: `0`
- counterexample clearance attached sum: `0`
- evidence ready for truth use sum: `0`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Interpretation
- BR-096 successfully closes the raw/source traceability question for all `14` BR-095 request rows.
- Every source-candidate anchor/onset trace points to core rows and available raw CSV references.
- This is meaningful progress, but it is not final fault confirmation.
- The remaining blockers are now cleaner:
  - independent physical/electrical or maintenance/inspection evidence
  - common-cause clearance
  - measurement-artifact clearance
  - counterexample clearance for the `3` guarded `gangui` rows

## Safety Boundary
- BR-096 attaches traceability evidence only.
- Raw/core/source CSV references are not independent physical confirmation.
- Raw attachment does not approve truth rebuild or threshold replay.
- No threshold tuning, semantic loosening, operator-facing precursor promotion, or direct `panel_day_engine.py` edit is approved.

## Ordered Next Path
1. Review BR-096 attachment rows and daily traces for obvious trace mistakes.
2. Attach independent exact-panel physical measurement, IV curve, string/inverter trace, maintenance, inspection, or repair evidence if available.
3. Run a blocker-clearance attachment for common-cause, measurement-artifact, and counterexample-risk rows.
4. Only after independent/clearance axes are populated, build confirmed-positive truth input.
5. Re-run threshold replay only after enough positive/negative truth rows are evidence-backed.

## Decision
- Accept BR-096 as the current raw/source attachment packet.
- Do not rebuild truth rows or rerun threshold replay yet.
- Use BR-096 to show that the next bottleneck is external confirmation and blocker clearance, not raw/source traceability.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_raw_source_attachment_v1.py --repo-root "$(pwd)" --request-dir /private/tmp/panel_day_engine_voltage_preserved_evidence_request_packet_br095_check --source-map-input /private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check
```

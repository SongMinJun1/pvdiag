<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_093_VOLTAGE_PRESERVED_CONFIRMATION_PACKET_V1

## Purpose
- Implement the next safe step after BR-092: compress voltage-preserved search hits into reviewable confirmation tasks.
- Deduplicate repeated hard episodes so search-hit volume does not become artificial truth support.
- Carry same-root known negative overlap as a blocker/caution flag.
- Keep this branch packet/evidence-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_packet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_positive_search_br092_check/panel_day_engine_voltage_preserved_positive_search_candidates_v1.csv` | BR-092 voltage-preserved candidate reservoir |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_packet_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_family_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_candidate_map_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check/panel_day_engine_voltage_preserved_confirmation_packet_v1.json`

## Real Result
- source candidate map rows: `86`
- confirmation packet rows: `14`
- confirmation family rows: `7`
- counterexample-risk packet rows: `3`
- counterexample-risk families: `1`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Review Priority Counts
| review priority | rows |
| --- | ---: |
| `P0_multi_anchor_strong_voltage_preserved` | 10 |
| `P0_single_anchor_strong_voltage_preserved` | 3 |
| `P1_repeated_voltage_preserved_10d` | 1 |

## Family Summary
| family | site | root | priority | packet rows | source rows | unique panels | max gap | risk | action |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `BR093-VPCF-001` | `conalog` | `7f7dd654-2760-4eb2-a197-3ebb72b85cda` | `P0_family_multi_anchor_strong` | 1 | 2 | 1 | 55 | 0 | `independent_confirmation_review` |
| `BR093-VPCF-002` | `conalog` | `c42997a6-5881-47e7-9035-7de8a2673b54` | `P0_family_multi_anchor_strong` | 1 | 11 | 1 | 119 | 0 | `independent_confirmation_review` |
| `BR093-VPCF-003` | `conalog` | `d15b9e13-4117-49ae-a78f-7ace013e48de` | `P1_family_repeated_voltage` | 1 | 3 | 1 | 117 | 0 | `independent_confirmation_review` |
| `BR093-VPCF-004` | `gangui` | `4fd0c566-e25e-4d51-96ca-57cc46940593` | `P0_family_multi_anchor_strong` | 6 | 35 | 6 | 120 | 0 | `independent_confirmation_review` |
| `BR093-VPCF-005` | `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511` | `P0_family_multi_anchor_strong` | 3 | 17 | 3 | 120 | 1 | `counterexample_guarded_confirmation_review` |
| `BR093-VPCF-006` | `ktc_ess` | `10305b40-b67e-40d1-9cd1-271b6642a3d9` | `P0_family_multi_anchor_strong` | 1 | 11 | 1 | 120 | 0 | `independent_confirmation_review` |
| `BR093-VPCF-007` | `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05` | `P0_family_multi_anchor_strong` | 1 | 7 | 1 | 106 | 0 | `independent_confirmation_review` |

## Interpretation
- BR-093 turns the BR-092 candidate reservoir into a smaller human-reviewable packet: `86` rows -> `14` panel tasks -> `7` root families.
- Most packet rows are strong enough for P0 confirmation review, but none is truth-approved.
- The `gangui/bf1a912f...` family is counterexample-guarded because the same root has a known BR-092 negative overlap.
- This keeps momentum without silently converting search volume into truth support.

## Safety Boundary
- BR-093 is a confirmation packet only.
- Packet rows are not positive truth labels.
- Confirmation fields all start empty/zero.
- No threshold tuning, semantic loosening, operator-facing precursor promotion, or direct `panel_day_engine.py` edit is approved.

## Ordered Next Path
1. Attach independent confirmation to P0 packet rows.
2. Treat counterexample-risk family rows separately before any truth rebuild.
3. Only after confirmation fields are filled, build a confirmed-positive truth input.
4. Re-run BR-090 after at least 3 independent positive truth rows exist.
5. Keep direct engine edits behind BR-076 prepatch gates.

## Decision
- Accept BR-093 as the current confirmation packet.
- Do not rebuild truth rows or rerun threshold replay yet.
- Use BR-093 to decide which candidate families deserve raw waveform, inspection, maintenance, or independent source attachment next.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_packet_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_packet_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_packet_v1.py --repo-root /private/tmp/pvdiag_postmerge_j --output-dir /private/tmp/panel_day_engine_voltage_preserved_confirmation_packet_br093_check
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

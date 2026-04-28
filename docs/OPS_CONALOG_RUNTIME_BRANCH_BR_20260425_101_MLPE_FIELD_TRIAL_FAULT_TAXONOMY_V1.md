<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_101_MLPE_FIELD_TRIAL_FAULT_TAXONOMY_V1

## Purpose
- Record the MLPE field-trial fault taxonomy before fault injection starts.
- Keep the taxonomy broad enough for PV faults, but specific enough for MLPE telemetry, optimizer control, and communication artifacts.
- Prevent future patches from treating every fault-like pattern as a panel-local physical fault.
- Keep this branch documentation-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Decision
- The current PV fault families are usable as the physical/electrical layer, but not complete for MLPE.
- MLPE trials need additional top-level classes for optimizer/control faults and measurement/communication artifacts.
- Every injected or observed event must be labeled by multiple axes:
  - physical fault family
  - MLPE/control family
  - measurement artifact flag
  - common-cause scope
  - affected electrical scope
  - evidence confidence

## Required Top-Level Families
| fault_family | role | examples | panel-local promotion rule |
| --- | --- | --- | --- |
| `normal` | clean reference | stable clear-day baseline, expected peer variation | not applicable |
| `panel_surface_environment_fault` | external panel surface/environment loss | partial shading, soiling, snow/cover, local obstruction | only if scope and injection/observation are panel-local |
| `panel_physical_degradation_fault` | durable module degradation/damage | degradation emulator, crack/damage proxy, hotspot-like thermal stress | requires persistence plus panel-local evidence |
| `panel_electrical_submodule_fault` | cell/submodule electrical pattern | bypass diode, substring loss, partial substring mismatch | requires V/I shape match and panel-local evidence |
| `connection_or_open_fault` | wiring/connector/open behavior | high series resistance, intermittent connector, partial open, open circuit | requires event timing and local electrical evidence |
| `mlpe_device_or_control_fault` | optimizer/control fault, not necessarily panel fault | optimizer clipping/current limit, MPPT tracking anomaly, rapid-shutdown/safety state, firmware/control response anomaly | do not promote as panel physical fault unless separated from MLPE device behavior |
| `measurement_or_communication_artifact` | telemetry/data problem | stale value, dropout, offset, stuck sensor, timestamp skew, packet loss | blocks physical fault promotion until cleared |
| `inverter_or_group_side_fault` | upstream/downstream group-side effect | inverter curtailment, string/group shutdown, root-level limit | blocks panel-local promotion unless a panel-specific residual remains |
| `site_common_cause_event` | site/root/group synchronous event | irradiance transient, grid event, site control action, simultaneous group dip | blocks panel-local promotion unless isolated evidence exists |
| `unknown_or_compound` | unresolved or intentionally mixed event | overlapping shading plus communication loss, unclear injection setup | no promotion; review only |

## Required Subtype Examples
| fault_family | candidate subtypes |
| --- | --- |
| `panel_surface_environment_fault` | `partial_shading`, `uniform_soiling`, `moving_shadow`, `snow_or_cover`, `localized_obstruction` |
| `panel_physical_degradation_fault` | `degradation_emulation`, `series_resistance_degradation`, `crack_or_damage_proxy`, `hotspot_like_thermal_stress` |
| `panel_electrical_submodule_fault` | `bypass_diode_open`, `bypass_diode_short`, `substring_loss`, `cell_mismatch`, `voltage_preserved_current_drop` |
| `connection_or_open_fault` | `intermittent_connection`, `high_contact_resistance`, `partial_open`, `full_open`, `connector_recovery` |
| `mlpe_device_or_control_fault` | `optimizer_current_limit`, `optimizer_clipping`, `mppt_tracking_anomaly`, `rapid_shutdown_state`, `control_response_delay` |
| `measurement_or_communication_artifact` | `telemetry_dropout`, `telemetry_stuck`, `sensor_offset`, `timestamp_skew`, `missing_packet_burst` |
| `inverter_or_group_side_fault` | `group_curtailment`, `string_shutdown`, `inverter_limit`, `root_level_drop`, `multi_panel_zero_output` |
| `site_common_cause_event` | `cloud_or_irradiance_event`, `site_control_action`, `grid_event`, `maintenance_window`, `site_wide_reference_shift` |

## Required Label Fields
| field | required | description |
| --- | --- | --- |
| `trial_event_id` | yes | stable event id |
| `site` | yes | site id |
| `root_id` | yes | root/string/group id if available |
| `panel_id` | yes | target panel id |
| `mlpe_device_id` | yes | optimizer/MLPE id or mapped device id |
| `start_ts` | yes | injection or observed start timestamp |
| `end_ts` | yes | injection or observed end timestamp |
| `fault_family` | yes | one top-level family above |
| `fault_subtype` | yes | controlled vocabulary under family |
| `affected_scope` | yes | `panel`, `substring`, `string`, `root`, `site`, `unknown` |
| `injection_mode` | yes | `physical`, `electrical_emulator`, `mlpe_control`, `telemetry`, `environment`, `observed_only` |
| `injection_strength` | yes | numeric or structured intensity, e.g. shade ratio, resistance, clipping limit |
| `expected_signature` | yes | expected V/I/P shape, e.g. `v_drop_i_preserved`, `i_drop_v_preserved`, `p_drop_both` |
| `is_panel_local` | yes | `1` only when the event is intended/verified as panel-local |
| `is_common_cause` | yes | `1` for multi-panel/site/root events |
| `is_measurement_artifact` | yes | `1` for telemetry/sensor/data issues |
| `mlpe_state` | yes | normal, clipping, MPPT anomaly, rapid shutdown, dropout, unknown |
| `truth_confidence` | yes | `confirmed_injected`, `confirmed_observed`, `probable`, `ambiguous`, `negative_control` |
| `operator_promotion_allowed` | yes | always `0` until separate truth gate |
| `engine_patch_allowed` | yes | always `0` until separate prepatch gate |
| `review_note` | no | free-form reviewer note |

## Minimum Injection Matrix
| priority | injection case | why it is needed |
| --- | --- | --- |
| P0 | `normal_clear_day_baseline` | required negative/reference anchor |
| P0 | `partial_shading_panel_local` | separates panel-local environmental loss from common irradiance |
| P0 | `uniform_soiling_or_cover` | tests slow broad output reduction without electrical fault |
| P0 | `high_contact_resistance_or_series_resistance` | tests connection/degradation-like gradual voltage/current distortion |
| P0 | `partial_open_or_full_open` | tests abrupt/strict-trigger and recovery logic |
| P0 | `bypass_diode_or_substring_loss` | tests voltage/current ratio and submodule shape family |
| P0 | `optimizer_current_limit_or_clipping` | MLPE-specific non-panel-physical counterexample |
| P0 | `telemetry_dropout_or_stuck_value` | measurement artifact counterexample |
| P0 | `group_or_inverter_curtailment` | common-cause/group-side counterexample |
| P0 | `site_or_root_common_cause_event` | protects against multi-panel false promotion |
| P1 | `mppt_tracking_anomaly` | MLPE control issue that can mimic panel fault |
| P1 | `rapid_shutdown_or_safety_state` | MLPE/system safety state can look like abrupt fault |
| P1 | `degradation_emulation` | durable precursor pattern and threshold tuning material |
| P2 | `compound_fault` | validates unknown/compound routing rather than forced single-label closure |

## Measurement Requirements
- Capture per-panel/MLPE `voltage`, `current`, `power`, `optimizer_state`, `communication_status`, and timestamp quality.
- Capture peer panels in the same root/group/site during the same window.
- Capture weather or irradiance proxy if available.
- Record the exact injection mechanism and intensity for every event.
- Keep raw waveform slices around start, peak, recovery, and post-event baseline.

## Safety Boundary
- Electrical short, ground, and arc-like tests require a controlled low-risk rig or emulator. Do not inject hazardous field faults into production PV hardware.
- If only telemetry is manipulated, label it as `measurement_or_communication_artifact`, not physical panel fault.
- If several panels are intentionally affected together, label the event as common-cause or group-side even if each panel shows a strong fault-like shape.
- Do not collapse `mlpe_device_or_control_fault` into panel physical fault without independent physical evidence.

## Interaction With Current Patch Path
- BR-100 showed that unlabeled data-only candidates exist, but most trigger-only rows need common-cause screening.
- BR-101 defines the field-trial labels that will make those future decisions learnable instead of hand-curated.
- The next implementation can create a CSV template/checker from these fields, but this branch intentionally stops at the taxonomy contract.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

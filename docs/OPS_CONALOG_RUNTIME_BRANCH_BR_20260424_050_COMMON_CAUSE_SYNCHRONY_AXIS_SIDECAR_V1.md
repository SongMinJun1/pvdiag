<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_050_COMMON_CAUSE_SYNCHRONY_AXIS_SIDECAR_V1

## Purpose
- BR-040 `report_entry_friction_axis`, BR-041 `recovery_recurrence_axis` 다음 evidence axis인 `common_cause_synchrony_axis`를 실제 sidecar로 내린다.
- 목표는 raw 후보의 공통원인 흔들림을 operator-facing verdict로 승격하지 않고, 패널별/사이트별로 읽을 수 있게 분리하는 것이다.
- 이 패치는 `pv_ae/panel_day_engine.py`, runtime verdict, threshold, row universe를 바꾸지 않는다.

## Builder
- script: `research/prognostics/build_panel_day_engine_common_cause_synchrony_axis_v1.py`
- smoke: `research/prognostics/smoke_test_panel_day_engine_common_cause_synchrony_axis_v1.py`

## Outputs
- `panel_day_engine_common_cause_synchrony_axis_v1.csv`
  - panel-level detail sidecar
  - bucket, report lane, signal row count, common-cause row count, site/group/subgroup/prefault overlap counts
- `panel_day_engine_common_cause_synchrony_axis_summary_v1.csv`
  - site, best report lane, synchrony bucket별 aggregate summary

## Bucket Priority
- `site_event_synchrony`
  - `site_event_soft` or `site_event_hard`
- `group_off_synchrony`
  - `group_off_date`, `group_off_like`, or meaningful `group_off_group`
- `prefault_B_common_cause_overlap`
  - `prefault_B_common_cause_overlap`
- `subgroup_synchrony_candidate`
  - `subgroup_common_cause_candidate`
- `co_drop_breadth_hint`
  - `co_drop_frac >= 0.35`
- `panel_local_or_weak_synchrony`
  - signal exists but above common-cause synchrony markers are absent

## Real Data Result
- output root: `/private/tmp/common_cause_synchrony_axis_sidecar_check`
- input data root: `/Users/b9gc/pvdiag/data`
- input result root: `/private/tmp/conalog_mlpe_seed_expand_check/result`
- `detail_rows = 206`
- `summary_rows = 23`

## Site Summary
| site | panels | candidate_rows | signal_rows | common_cause_rows | site_event_panels | group_off_panels | subgroup_panels | prefault_B_overlap_panels | co_drop_hint_panels | max_co_drop |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `conalog` | 82 | 620 | 605 | 111 | 0 | 0 | 71 | 0 | 2 | 0.403012 |
| `gangui` | 46 | 793 | 786 | 97 | 0 | 20 | 12 | 1 | 0 | 0.302198 |
| `ktc_ess` | 78 | 382 | 320 | 188 | 30 | 0 | 60 | 0 | 51 | 0.491979 |

## Bucket Counts
| site | synchrony_bucket | panels |
|---|---|---:|
| `conalog` | `co_drop_breadth_hint` | 2 |
| `conalog` | `panel_local_or_weak_synchrony` | 9 |
| `conalog` | `subgroup_synchrony_candidate` | 71 |
| `gangui` | `group_off_synchrony` | 20 |
| `gangui` | `panel_local_or_weak_synchrony` | 19 |
| `gangui` | `subgroup_synchrony_candidate` | 7 |
| `ktc_ess` | `co_drop_breadth_hint` | 2 |
| `ktc_ess` | `panel_local_or_weak_synchrony` | 2 |
| `ktc_ess` | `site_event_synchrony` | 30 |
| `ktc_ess` | `subgroup_synchrony_candidate` | 44 |

## Report-Lane Counts
| site | best_report_lane | panels |
|---|---|---:|
| `conalog` | `none` | 10 |
| `conalog` | `official_current` | 2 |
| `conalog` | `rawonly_current` | 70 |
| `gangui` | `none` | 5 |
| `gangui` | `official_current` | 2 |
| `gangui` | `precursor` | 4 |
| `gangui` | `rawonly_current` | 35 |
| `ktc_ess` | `none` | 52 |
| `ktc_ess` | `official_current` | 2 |
| `ktc_ess` | `precursor` | 24 |

## Important Interpretation
- `common_cause_synchrony_axis` is evidence-only.
  - It does not promote or suppress a fault.
- `co_drop_breadth_hint` is intentionally weak.
  - It records broad co-drop context, not a direct common-cause verdict.
- `group_off_group=False`, `none`, `0`, and empty text are ignored as meaningful group keys.
  - This prevents false group-off inflation from boolean/text placeholders.
- The result shows the sites do not share a single common-cause profile:
  - `conalog`: subgroup-oriented signal concentration
  - `gangui`: actual group-off synchrony is visible
  - `ktc_ess`: site-event/co-drop breadth is prominent

## Decision
- BR-050 completes the third evidence-axis sidecar from BR-039.
- Next safe step:
  - cross-axis review over `report_entry_friction_axis`, `recovery_recurrence_axis`, and `common_cause_synchrony_axis`
- Algorithm gating remains blocked until the cross-axis review and exact-family re-search finish.

## Repro Commands
```bash
python3 -m py_compile research/prognostics/build_panel_day_engine_common_cause_synchrony_axis_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_synchrony_axis_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_synchrony_axis_v1.py
python3 research/prognostics/build_panel_day_engine_common_cause_synchrony_axis_v1.py --data-root /Users/b9gc/pvdiag/data --result-root /private/tmp/conalog_mlpe_seed_expand_check/result --output-dir /private/tmp/common_cause_synchrony_axis_sidecar_check --sites conalog gangui ktc_ess
```

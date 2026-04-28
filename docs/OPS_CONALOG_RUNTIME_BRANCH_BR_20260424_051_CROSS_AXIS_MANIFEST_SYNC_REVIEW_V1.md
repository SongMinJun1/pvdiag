<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_051_CROSS_AXIS_MANIFEST_SYNC_REVIEW_V1

## Purpose
- BR-047~BR-050에서 만든 정리 지도가 서로 맞물리는지 검토한다.
- 이 패치는 algorithm gating이 아니라 `정리의 정리`다.
- 세 evidence axis를 한 패널 단위로 합치고, evidence manifest가 BR-050까지 따라잡았는지 확인한다.

## Builder
- cross-axis review:
  - `research/prognostics/build_panel_day_engine_cross_axis_manifest_sync_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_cross_axis_manifest_sync_review_v1.py`
- manifest sync update:
  - `research/prognostics/build_panel_day_engine_evidence_manifest_v1.py`
  - `research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py`

## Inputs
- report-entry friction:
  - `/private/tmp/report_entry_friction_axis_sidecar_check`
- recovery/recurrence:
  - `/private/tmp/recovery_recurrence_axis_sidecar_check`
- common-cause synchrony:
  - `/private/tmp/common_cause_synchrony_axis_sidecar_check`
- evidence manifest:
  - `/private/tmp/evidence_manifest_pack_check`
- cleanup maps:
  - `/private/tmp/repo_role_boundary_manifest_check`
  - `/private/tmp/repo_mirror_boundary_manifest_check`
  - `/private/tmp/repo_active_builder_entrypoint_registry_check`

## Outputs
- `/private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_v1.csv`
- `/private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_review_summary_v1.csv`
- `/private/tmp/cross_axis_manifest_sync_review_check/panel_day_engine_cross_axis_manifest_sync_status_v1.csv`

## Real Data Result
- `detail_rows = 209`
- `summary_rows = 10`
- `sync_rows = 6`
- refreshed manifest rows:
  - `panel_day_engine_evidence_manifest_v1.csv = 23`
  - previous manifest lacked `common_cause_synchrony_axis`
  - refreshed manifest now has `common_cause_synchrony_axis` detail and summary rows

## Review Focus Counts
| review_focus_bucket | site | panels |
|---|---|---:|
| `local_signal_morphology_review` | `conalog` | 10 |
| `local_signal_morphology_review` | `gangui` | 9 |
| `local_signal_morphology_review` | `ktc_ess` | 2 |
| `single_or_weak_axis_context_review` | `conalog` | 2 |
| `single_or_weak_axis_context_review` | `gangui` | 10 |
| `strong_common_cause_hold_review` | `gangui` | 20 |
| `strong_common_cause_hold_review` | `ktc_ess` | 30 |
| `subgroup_or_breadth_context_review` | `conalog` | 73 |
| `subgroup_or_breadth_context_review` | `gangui` | 7 |
| `subgroup_or_breadth_context_review` | `ktc_ess` | 46 |

## Sync Status
| sync_item | sync_status | rows |
|---|---|---:|
| `report_entry_friction_axis` | `synced` | 49 |
| `recovery_recurrence_axis` | `synced` | 206 |
| `common_cause_synchrony_axis` | `synced` | 206 |
| `repo_role_boundary_manifest` | `available_cleanup_map` | 24 |
| `repo_mirror_boundary_manifest` | `available_cleanup_map` | 35 |
| `repo_active_builder_entrypoint_registry` | `available_cleanup_map` | 289 |

## Important Interpretation
- `strong_common_cause_hold_review` is prioritized before local morphology.
  - This prevents site/group/prefault overlap context from being accidentally read as individual panel precursor evidence.
- report-entry blocker information is not lost.
  - It remains counted inside each review bucket as `panels_with_report_entry_blocker`.
- `subgroup_or_breadth_context_review` is context, not a direct verdict.
  - It can guide later exact-family search but does not close it.
- `local_signal_morphology_review` is the safer next inspect pool.
  - It has recovery/persistence pressure while common-cause context is weak or local.
- cleanup maps are intentionally not evidence-family rows.
  - They stay as role/mirror/builder maps used to avoid scope confusion.

## Decision
- BR-051 completes the cross-axis + manifest sync review.
- The immediate cleanup/evidence map is now aligned enough to resume targeted evidence search.
- Next safe step:
  - exact-family missing seed re-search, starting from `local_signal_morphology_review` and excluding `strong_common_cause_hold_review` from promotion logic.
- Algorithm gating remains blocked.

## Repro Commands
```bash
python3 research/prognostics/build_panel_day_engine_evidence_manifest_v1.py --result-root /private/tmp/conalog_mlpe_seed_expand_check/result --group-off-root /private/tmp/group_off_report_lane_entry_blocker_check --opportunity-root /private/tmp/evidence_axis_expansion_opportunity_scan --report-entry-root /private/tmp/report_entry_friction_axis_sidecar_check --recovery-root /private/tmp/recovery_recurrence_axis_sidecar_check --common-cause-root /private/tmp/common_cause_synchrony_axis_sidecar_check --output-dir /private/tmp/evidence_manifest_pack_check --owner-branch codex/post-merge-base-j
python3 research/prognostics/build_panel_day_engine_cross_axis_manifest_sync_review_v1.py --friction-root /private/tmp/report_entry_friction_axis_sidecar_check --recovery-root /private/tmp/recovery_recurrence_axis_sidecar_check --common-cause-root /private/tmp/common_cause_synchrony_axis_sidecar_check --manifest-root /private/tmp/evidence_manifest_pack_check --role-root /private/tmp/repo_role_boundary_manifest_check --mirror-root /private/tmp/repo_mirror_boundary_manifest_check --builder-registry-root /private/tmp/repo_active_builder_entrypoint_registry_check --output-dir /private/tmp/cross_axis_manifest_sync_review_check
```

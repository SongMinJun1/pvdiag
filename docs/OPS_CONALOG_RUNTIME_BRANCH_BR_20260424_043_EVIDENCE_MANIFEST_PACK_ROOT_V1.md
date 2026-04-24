<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_043_EVIDENCE_MANIFEST_PACK_ROOT_V1

## Purpose
- 흩어진 evidence artifact를 `single manifest + consolidated pack root`로 묶어, 지금까지 만든 sidecar와 temp scan을 한 루트에서 읽을 수 있게 고정한다.

## Implementation
- added builder:
  - [build_panel_day_engine_evidence_manifest_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/build_panel_day_engine_evidence_manifest_v1.py)
- added smoke:
  - [smoke_test_panel_day_engine_evidence_manifest_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/smoke_test_panel_day_engine_evidence_manifest_v1.py)
- outputs:
  - `panel_day_engine_evidence_manifest_v1.csv`
  - `panel_day_engine_evidence_manifest_summary_v1.csv`
  - `panel_day_engine_evidence_pack_manifest_v1.json`
  - `evidence_pack_root/`

## Input Roots
- base result root:
  - [/private/tmp/conalog_mlpe_seed_expand_check/result](</private/tmp/conalog_mlpe_seed_expand_check/result>)
- blocker scan root:
  - [/private/tmp/group_off_report_lane_entry_blocker_check](</private/tmp/group_off_report_lane_entry_blocker_check>)
- opportunity scan root:
  - [/private/tmp/evidence_axis_expansion_opportunity_scan](</private/tmp/evidence_axis_expansion_opportunity_scan>)
- implemented sidecar roots:
  - [/private/tmp/report_entry_friction_axis_sidecar_check](</private/tmp/report_entry_friction_axis_sidecar_check>)
  - [/private/tmp/recovery_recurrence_axis_sidecar_check](</private/tmp/recovery_recurrence_axis_sidecar_check>)

## What The Manifest Solves
- artifact가 여러 temp root에 흩어져 있어도
  - `evidence_family`
  - `judgment_role`
  - `artifact_kind`
  - `artifact_path`
  - `canonical_or_temp`
  - `owner_branch`
  - `latest_decision_log`
  - `repro_command`
  를 한 줄에서 읽을 수 있다.
- 동시에 `evidence_pack_root/` 아래에 family별 symlink/copy tree를 만들어, 실제 읽는 경로도 하나로 줄인다.
- builder-backed artifact와 one-off temp scan artifact를 manifest 안에서 `repro_mode`로 분리한다.

## Actual Check Snapshot
- output root:
  - [/private/tmp/evidence_manifest_pack_check](</private/tmp/evidence_manifest_pack_check>)
- manifest:
  - [panel_day_engine_evidence_manifest_v1.csv](/private/tmp/evidence_manifest_pack_check/panel_day_engine_evidence_manifest_v1.csv)
  - [panel_day_engine_evidence_manifest_summary_v1.csv](/private/tmp/evidence_manifest_pack_check/panel_day_engine_evidence_manifest_summary_v1.csv)
  - [panel_day_engine_evidence_pack_manifest_v1.json](/private/tmp/evidence_manifest_pack_check/panel_day_engine_evidence_pack_manifest_v1.json)
- pack root:
  - [/private/tmp/evidence_manifest_pack_check/evidence_pack_root](</private/tmp/evidence_manifest_pack_check/evidence_pack_root>)

## Data Read
- indexed artifact rows: `21`
- existing artifacts: `21`
- indexed families: `7`
  - `report_lane_result_base = 6`
  - `runtime_summary_context = 5`
  - `operator_surface_preview = 3`
  - `group_off_report_lane_blocker = 2`
  - `report_entry_friction_axis = 2`
  - `recovery_recurrence_axis = 2`
  - `evidence_axis_opportunity_map = 1`
- `judgment_role` split:
  - `candidate_reservoir = 7`
  - `structural_blocker = 4`
  - `supportive_hint = 10`
- `repro_mode` split:
  - `runtime_run = 14`
  - `builder = 4`
  - `manual_oneoff = 3`

## Why This Matters
- 이제 다음 축을 추가해도 “근거가 어디 있었는지”를 다시 찾느라 흐트러질 가능성이 줄어든다.
- exact-family 재탐색이나 cross-axis review도 temp root를 직접 기억하는 대신, 먼저 manifest/pack root에서 시작할 수 있다.
- `manual_oneoff` scan artifact가 아직 남아 있다는 사실도 숨기지 않고 manifest에 그대로 남긴다.

## Decision
- this branch is `implemented`.
- next preferred evidence-axis sidecar is `common_cause_synchrony_axis`.

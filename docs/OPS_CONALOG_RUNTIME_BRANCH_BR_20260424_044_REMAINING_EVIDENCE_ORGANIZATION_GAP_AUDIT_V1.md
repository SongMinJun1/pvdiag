<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_044_REMAINING_EVIDENCE_ORGANIZATION_GAP_AUDIT_V1

## Purpose
- BR-043 manifest 이후에도 남아 있는 `organization gap`을 current evidence line과 분리해서 기록한다.
- 목적은 두 가지다.
  - 현재 order를 흔들지 않기
  - 나중에 “이것도 정리해야 했는데 잊었다”가 되지 않게 backlog를 보존하기

## What BR-043 Solved
- current Step 4C evidence line은 이제 아래 root들에서 `single manifest + pack root`로 읽힌다.
  - `conalog_mlpe_seed_expand_check`
  - `group_off_report_lane_entry_blocker_check`
  - `evidence_axis_expansion_opportunity_scan`
  - `report_entry_friction_axis_sidecar_check`
  - `recovery_recurrence_axis_sidecar_check`
  - `evidence_manifest_pack_check`

## Remaining Organization Gaps

### 1. historical BR temp roots are still docs-only archive
- runtime docs에 남아 있는 unique `/private/tmp` top roots는 `36`개다.
- 그중 `25`개는 `br004`~`br022` 계열 historical validation/review packet roots다.
- examples:
  - `br005_trigger_only_review_packet`
  - `br010_promotion_bucket_review_packet_v1`
  - `br012_g1_suppression_shadow_sim_v1`
  - `br019_tri_site_v3`
  - `br022_tri_site_v1`
- 현재 manifest는 이 historical roots를 index하지 않는다.
- 이유:
  - current Step 4 evidence line과 historical packet/archive line을 섞지 않기 위해서다.
- status:
  - `not blocking`
  - future `historical archive manifest` candidate

### 2. current manifest still contains manual-oneoff families
- BR-043 manifest 기준:
  - `manual_oneoff rows = 3`
  - families:
    - `group_off_report_lane_blocker`
    - `evidence_axis_opportunity_map`
- meaning:
  - 현재 current evidence line 안에도 아직 builder-backed가 아닌 temp scan 잔재가 남아 있다.
- status:
  - `known gap`
  - future builderization candidate if reused

### 3. builder inventory is much larger than current evidence pack coverage
- `research/prognostics/build_panel_day_engine_*` 중 audit/probe/axis/review 계열 builder candidate는 `47`개가 더 있다.
- examples:
  - `build_panel_day_engine_common_cause_routing_gap_audit_v1.py`
  - `build_panel_day_engine_common_cause_breadth_marker_audit_v1.py`
  - `build_panel_day_engine_local_precursor_eligibility_audit_v1.py`
  - `build_panel_day_engine_gpvs_mlpe_compatibility_audit_v1.py`
  - `build_panel_day_engine_operator_attention_policy_audit_v1.py`
- current manifest는 Step 4 evidence line에 직접 쓰는 artifact만 다루고, wider audit script inventory는 아직 registry화하지 않았다.
- status:
  - `not blocking`
  - future `audit script registry` candidate

### 4. bookkeeping/worktree references remain outside the manifest
- docs에는 아래 `4`개 bookkeeping/worktree path도 남아 있다.
  - `pvdiag_br005_trigger_review`
  - `pvdiag_dirty_status_after_br004_merge_20260423.txt`
  - `pvdiag_dirty_tracked_diff_after_br004_merge_20260423.patch`
  - `pvdiag_postmerge_j`
- 추가로 `conalog_counterexample_seed_check` 같은 single scan root도 `1`개 남아 있다.
- 이런 항목은 current evidence pack이라기보다 history/workspace note에 가깝다.
- status:
  - `non-pack reference`

## Interpretation
- 지금 current evidence line은 `정리된 것`이 맞다.
- 하지만 repo 전체 기준으로 보면 아직 `완전한 global organization`은 아니다.
- 더 정확히는 아래처럼 읽는 게 맞다.
  - current Step 4 evidence line: `organized`
  - historical BR temp packet/archive line: `documented but not re-indexed`
  - wider audit builder inventory: `present but not registry-managed`

## Decision
- next implementation order는 바꾸지 않는다.
- still next:
  - `common_cause_synchrony_axis`
- but keep the following backlog alive:
  1. `historical archive manifest`
  2. `manual_oneoff -> builder-backed conversion`
  3. `audit script registry`

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_047_ROLE_BOUNDARY_MANIFEST_V1

## Purpose
- BR-046에서 잠근 `mixed_scope_disentangle`를 실제 artifact로 내린다.
- 목표는 branch 수를 줄이는 것이 아니라, repo 안의 경로가 어떤 역할인지 기계적으로 읽히게 만드는 것이다.

## Builder
- script: `research/prognostics/build_repo_role_boundary_manifest_v1.py`
- smoke: `research/prognostics/smoke_test_repo_role_boundary_manifest_v1.py`

## Outputs
- `repo_role_boundary_manifest_v1.csv`
  - path pattern별 역할/소유/검증/정리 action 정의
- `repo_role_boundary_status_v1.csv`
  - 현재 `git status --short` entry별 role match 결과
- `repo_role_boundary_summary_v1.csv`
  - status/role/family/action별 count summary
- `repo_role_boundary_summary_v1.json`
  - downstream script가 바로 읽을 수 있는 summary payload

## Schema Lock
- manifest columns:
  - `role_id`
  - `path_pattern`
  - `role_family`
  - `artifact_layer`
  - `canonical_owner`
  - `source_of_truth`
  - `sync_direction`
  - `edit_policy`
  - `commit_policy`
  - `validation_required`
  - `cleanup_lane`
  - `cleanup_action`
  - `risk_if_mixed_ko`
  - `note_ko`
- status columns:
  - `status_code`
  - `path`
  - `top_level`
  - `role_id`
  - `role_family`
  - `artifact_layer`
  - `canonical_owner`
  - `cleanup_action`
  - `commit_policy`
  - `validation_required`
  - `matched_pattern`

## Real Data Result
- output root: `/private/tmp/repo_role_boundary_manifest_check`
- `manifest_role_total = 24`
- `dirty_entry_total = 106`
- `unclassified_dirty_entry_total = 0`
- dirty role family counts:
  - `docs = 41`
  - `release_package = 28`
  - `source_code = 24`
  - `final_delivery = 10`
  - `workspace_noncanonical = 2`
  - `repo_config = 1`

## Locked Interpretation
- `docs` dirty entries are not automatically cleanup clutter.
  - They are source docs unless the manifest says otherwise.
- `release/conalog_full_runtime_v1/package/research/prognostics/**` and `release/conalog_full_runtime_v1/package/pv_ae/**` are mirror lanes.
  - They should not be treated as first-write source unless a package hotfix is explicitly declared.
- `outputs/**` and nested `pvdiag/**` are workspace/non-canonical lanes.
  - They need explicit promote/move/ignore decisions before they can be treated as repo artifacts.
- `release/.../runtime/**` is a runtime bundle lane.
  - It should not be mixed with code cleanup review.

## Decision
- BR-047 completes the first confusion-reduction prelude step:
  - `mixed_scope_disentangle`
- Next practical lane:
  - `source_vs_packaged_mirror_boundary`
- The runtime evidence order remains unchanged:
  - `common_cause_synchrony_axis`
  - cross-axis review
  - exact-family re-search
  - algorithm gating last

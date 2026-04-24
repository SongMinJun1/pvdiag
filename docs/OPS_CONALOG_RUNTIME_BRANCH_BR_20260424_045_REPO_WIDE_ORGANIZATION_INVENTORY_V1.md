<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_045_REPO_WIDE_ORGANIZATION_INVENTORY_V1

## Purpose
- evidence line 바깥까지 포함한 repo-wide organization 상태를 한 번에 읽을 수 있게 inventory를 남긴다.
- 목표는 현재 cleanup pressure를 막연한 느낌이 아니라 `lane`으로 분리하는 것이다.

## Implementation
- added builder:
  - [build_repo_organization_inventory_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/build_repo_organization_inventory_v1.py)
- added smoke:
  - [smoke_test_repo_organization_inventory_v1.py](/private/tmp/pvdiag_postmerge_j/research/prognostics/smoke_test_repo_organization_inventory_v1.py)
- outputs:
  - `repo_organization_dirty_summary_v1.csv`
  - `repo_organization_surface_inventory_v1.csv`
  - `repo_organization_doc_tmp_root_inventory_v1.csv`
  - `repo_organization_cleanup_lanes_v1.csv`
  - `repo_organization_inventory_summary_v1.json`

## Actual Check Snapshot
- output root:
  - [/private/tmp/repo_organization_inventory_check](</private/tmp/repo_organization_inventory_check>)

## Data Read
- main dirty status entries:
  - `modified = 60`
  - `untracked = 43`
  - `deleted = 1`
  - `staged_modified = 2`
- top-level dirty concentration:
  - `docs = 40`
  - `release = 38`
  - `research = 22`
- surface inventory:
  - `source_docs = 222 files`
  - `source_research = 695 files`
  - `source_panel_engine = 30658 files`
  - `release_runtime_research = 18 files`
  - `release_runtime_panel_engine = 2 files`
  - `release_runtime_windows_bundle = 17924 files`
  - `final_delivery_docs = 9 files`
- current docs temp-root reference classes:
  - `historical_br = 5`
  - `current_evidence = 1`
- cleanup lanes declared:
  1. `main_dirty_disentangle`
  2. `source_release_finaldelivery_mirror_policy`
  3. `audit_builder_registry`
  4. `historical_tmp_archive`
  5. `runtime_bundle_hygiene`
  6. `workspace_clutter`

## Why This Matters
- 이제 repo-wide cleanup을 `뭉뚱그린 불안`이 아니라, current blocker와 backlog lane으로 나눠서 말할 수 있다.
- 특히 지금은 `main dirty`, `mirror surface`, `builder sprawl`가 가장 큰 구조적 축이라는 점이 숫자로 확인됐다.

## Recommended Order
1. `main_dirty_disentangle`
2. `source_release_finaldelivery_mirror_policy`
3. `audit_builder_registry`
4. `historical_tmp_archive`
5. `runtime_bundle_hygiene`
6. `workspace_clutter`

## Decision
- current runtime evidence line은 유지하되, user request 기준 next emphasis는 repo cleanup이다.
- immediate next cleanup target is `main_dirty_disentangle`.

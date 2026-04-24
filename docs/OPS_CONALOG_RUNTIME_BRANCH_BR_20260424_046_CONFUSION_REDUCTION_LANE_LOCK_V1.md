<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_046_CONFUSION_REDUCTION_LANE_LOCK_V1

## Purpose
- current priority를 `branch cleanup`이 아니라 `얽힌 역할/출력/스크립트가 서로 헷갈리는 상태를 줄이는 것`으로 다시 잠근다.

## Clarification
- 우리가 줄이려는 건 git branch 수가 아니라 아래 혼선이다.
  - source vs packaged mirror
  - current work vs historical archive
  - active builder vs old helper
  - runtime bundle vs code/doc lane
  - non-canonical workspace clutter vs real repo artifact

## Locked Lanes
1. `mixed_scope_disentangle`
2. `source_vs_packaged_mirror_boundary`
3. `active_builder_entrypoint_registry`
4. `historical_vs_current_boundary`
5. `runtime_bundle_boundary`
6. `workspace_boundary_cleanup`

## Why This Is Better
- `main_dirty_disentangle`라는 표현은 branch 정리처럼 들릴 수 있다.
- 실제로는 `무엇이 어떤 역할인지 빠르게 분리해서 읽게 만드는 것`이 목적이다.
- 그래서 lane 이름도 role/boundary 중심으로 다시 잠갔다.

## Decision
- next practical step is still the first lane:
  - `mixed_scope_disentangle`
- but this is not a git-only cleanup; it is a confusion-reduction prelude for the whole workstream.

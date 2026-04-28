<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_049_ACTIVE_BUILDER_ENTRYPOINT_REGISTRY_V1

## Purpose
- BR-048 다음 confusion-reduction step인 `active_builder_entrypoint_registry`를 실제 artifact로 내린다.
- 목표는 `research/prognostics`의 build/smoke script가 모두 같은 현재 진입점처럼 보이는 문제를 줄이는 것이다.

## Builder
- script: `research/prognostics/build_repo_active_builder_entrypoint_registry_v1.py`
- smoke: `research/prognostics/smoke_test_repo_active_builder_entrypoint_registry_v1.py`

## Outputs
- `repo_active_builder_entrypoint_registry_v1.csv`
  - build/smoke별 pair, package mirror, doc reference, dirty status, registry status
- `repo_active_builder_entrypoint_summary_v1.csv`
  - script kind, pair status, mirror status, registry status, recommended action별 count
- `repo_active_builder_entrypoint_summary_v1.json`
  - downstream script가 바로 읽을 수 있는 summary payload

## Real Data Result
- output root: `/private/tmp/repo_active_builder_entrypoint_registry_check`
- `entrypoint_total = 289`
- `builder_total = 140`
- `smoke_total = 149`
- `pair_missing_total = 25`
- `package_mirror_total = 8`
- `documented_total = 42`

## Registry Status Counts
- `packaged_runtime_entrypoint = 8`
- `documented_paired_entrypoint = 37`
- `documented_unpaired_entrypoint = 2`
- `paired_unreferenced_entrypoint = 223`
- `unpaired_builder_review = 2`
- `unpaired_smoke_review = 17`

## Important Interpretation
- `paired_unreferenced_entrypoint` is not deprecated by default.
  - It means the build/smoke pair exists but the exact filename was not found in current docs.
- `documented_unpaired_entrypoint` is not broken by default.
  - It means the expected name-based build/smoke pair is missing and should be explained or paired later.
- `unpaired_*_review` is a review queue.
  - It is not automatic deletion.
- `packaged_runtime_entrypoint` should be edited source-first and synced to package mirror.

## Decision
- BR-049 completes the third confusion-reduction prelude step:
  - `active_builder_entrypoint_registry`
- The practical cleanup prelude is now sufficient to resume the runtime evidence order.
- Next runtime evidence step:
  - `common_cause_synchrony_axis`

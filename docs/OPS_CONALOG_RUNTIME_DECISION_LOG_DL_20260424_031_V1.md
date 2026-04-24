<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_031_V1

## Decision
- Accept `repo_active_builder_entrypoint_registry_v1` as the concrete `active_builder_entrypoint_registry` artifact.

## Reason
- `research/prognostics` has many build/smoke scripts.
- Without a registry, current entrypoints, smoke fixtures, package mirrored builders, and archive candidates all look similar.
- The registry is intentionally conservative: it records evidence of current use instead of declaring unreferenced scripts deprecated.

## Evidence
- `repo_active_builder_entrypoint_summary_v1.json` reports:
  - `entrypoint_total = 289`
  - `builder_total = 140`
  - `smoke_total = 149`
  - `pair_missing_total = 25`
  - `package_mirror_total = 8`
  - `documented_total = 42`
- Review queues are now explicit:
  - `documented_unpaired_entrypoint = 2`
  - `unpaired_builder_review = 2`
  - `unpaired_smoke_review = 17`

## Consequence
- New builder work should check this registry before adding another adjacent script.
- Package mirrored builders should stay source-first.
- Unpaired scripts should be paired, explained, or later marked archive only.
- No runtime verdict, threshold, row universe, or operator-facing result semantics changed.

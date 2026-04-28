<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_DECISION_LOG_DL_20260424_030_V1

## Decision
- Accept `repo_mirror_boundary_manifest_v1` as the concrete `source_vs_packaged_mirror_boundary` artifact.

## Reason
- Release/package paths should not be read as one flat surface.
- Some paths are mirrors of source files.
- Some paths are package-specific entrypoints.
- Some paths are generated release/final-delivery artifacts.
- Treating all of them as source truth creates review and patch-scope confusion.

## Evidence
- `repo_mirror_boundary_summary_v1.json` reports:
  - `boundary_row_total = 35`
  - `source_only_scan_enabled = false`
  - `in_sync = 17`
  - `content_drift = 0` after generated pycache/noise exclusion
  - `packaged_only_no_source_pair = 4`
  - `package_surface_without_direct_source_pair = 2`
  - `generated_release_artifact = 8`
  - `generated_delivery_example = 4`

## Consequence
- Source mirror rows should be edited source-first and then synced.
- Package-only/generated rows should be validated as package surfaces or regenerated artifacts.
- The next confusion-reduction lane is `active_builder_entrypoint_registry`.
- No runtime verdict, threshold, row universe, or operator-facing result semantics changed.

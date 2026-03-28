# OPS Topology Inputs

## Purpose

Topology inputs matter because heuristic peer grouping is fragile. Real `string/mppt/inverter`
assignments are the minimum QA layer needed before topology-aware grouping can be enabled safely.

This patch does not change the core engine. It only measures how much usable topology coverage
already exists and where the gaps are.

## Expected CSV Schema

Manual input file:

- `data/manual/site_topology.csv`

Expected columns:

- `site`
- `panel_id`
- `string_id`
- `mppt_id`
- `inverter_id`
- `note`

One row should describe one panel topology assignment. Duplicate rows are allowed in the raw file,
but they will be flagged by the QA outputs.

## Inventory Source

Coverage is measured against currently active panels from stable outputs:

- `data/<site>/out/latest_panel_status.csv`

This keeps the QA target aligned with panels that are active in current scoring and evaluation.

## QA Outputs

Generated files:

- `_share/site_topology_coverage.csv`
- `_share/site_topology_missing.csv`
- `_share/site_topology_duplicates.csv`

### site_topology_coverage.csv

Minimum columns:

- `site`
- `total_panels`
- `matched_panels`
- `coverage_rate`
- `string_coverage_rate`
- `mppt_coverage_rate`
- `inverter_coverage_rate`

Coverage is computed over the active panel inventory, not over the raw topology file size.

### site_topology_missing.csv

Minimum columns:

- `site`
- `panel_id`
- `missing_string`
- `missing_mppt`
- `missing_inverter`

If a panel has no matched topology row for its site, all three missing flags are `1`.

### site_topology_duplicates.csv

Minimum columns:

- `panel_id`
- `row_count`
- `sites_seen`
- `string_ids_seen`
- `mppt_ids_seen`
- `inverter_ids_seen`

This output is used to flag:

- duplicate `panel_id` rows
- conflicting assignments for the same `panel_id`
- detectable site mismatches between the topology file and active inventory

## Missing Input Behavior

If `data/manual/site_topology.csv` does not exist, the builder still runs.

Expected behavior:

- `site_topology_coverage.csv` is still generated
- `site_topology_missing.csv` marks active panels as missing topology
- `site_topology_duplicates.csv` is generated with headers and no rows

## Why This Patch Stops Here

This patch does not yet change peer baselines, vbin grouping, or group-off logic.

That next step should happen only after topology coverage is acceptable and duplicate/conflict
issues are resolved. Until then, topology remains an input QA layer, not a live engine input.

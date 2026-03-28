# OPS Panel ID Hypothesis

## Purpose

Explicit topology truth is still missing. There is not yet a validated local mapping from `panel_id`
to true physical topology.

That does not make `panel_id` useless. The current inventory already shows stable internal structure,
and that structure can be decomposed into neutral tokens without asserting physical meaning.

This patch builds that neutral hypothesis layer so the team can decide whether later topology-aware
shadow integration is justified.

## Inputs

Primary active inventory source:

- `data/<site>/out/latest_panel_status.csv`

Target sites in this patch:

- `conalog`
- `gangui`
- `ktc_ess`
- `sinhyo`

Optional local reference:

- `data/manual/site_topology.csv`

The optional topology file is used only as a row-count reference by site. It is not used as
ground-truth semantics in this patch.

## Neutral Tokens

This patch assumes `panel_id` often resembles:

- `<uuid>.<token1>.<token2>`

It extracts:

- `token0_uuid`
- `token1_group`
- `token2_index`
- `token2_index_int`
- `panel_id_pattern_valid`
- `parse_note`

Important constraint:

- `token0`
- `token1`
- `token2`

are not yet asserted to mean inverter, string, or panel position.

They are only neutral structural tokens.

## Outputs

Generated files:

- `_share/site_panel_id_hypothesis_latest.csv`
- `_share/site_panel_id_hypothesis_summary.csv`

### site_panel_id_hypothesis_latest.csv

Minimum columns:

- `site`
- `panel_id`
- `token0_uuid`
- `token1_group`
- `token2_index`
- `token2_index_int`
- `panel_id_pattern_valid`
- `parse_note`

Additional diagnostics may also appear, such as inventory source and cross-site repeat flags.

### site_panel_id_hypothesis_summary.csv

Minimum columns:

- `site`
- `repo_panel_count`
- `valid_pattern_count`
- `pattern_valid_rate`
- `token0_unique_count`
- `token1_unique_count`
- `token2_min`
- `token2_max`
- `token2_unique_count`

The summary also carries lightweight diagnostics such as malformed row counts, token2 integer parse
failures, cross-site repeated `panel_id` rows, non-contiguous group counts, and optional topology
row-count reference by site.

### site_panel_id_group_stats.csv

Grouped by:

- `site`
- `token0_uuid`
- `token1_group`

Includes:

- `panel_count`
- `token2_min`
- `token2_max`
- `token2_unique_count`
- `token2_contiguous_flag`

`token2_contiguous_flag = 1` means the integer token2 values cover a gap-free contiguous range inside
that `(site, token0_uuid, token1_group)` group.

## Diagnostics

This patch identifies:

- malformed `panel_id` rows
- token2 values that are not parseable as integers
- repeated `panel_id` rows across sites
- groups where `token2_contiguous_flag = 0`

These are analysis diagnostics only. They do not change any engine behavior.

## Why This Stays Non-Core

This patch does not change grouping, thresholds, or any core engine behavior.

It is a decision-support layer for the next step:

1. check whether `panel_id` structure is stable enough by site
2. check whether group-level token2 behavior looks coherent enough
3. decide whether topology-aware shadow integration is justified

## Next Step

Core integration should wait until this hypothesis layer is checked against explicit topology truth
or at least against acceptable local coverage evidence.

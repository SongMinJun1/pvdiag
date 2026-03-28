# OPS Grouping Equivalence

## Purpose

This audit exists to answer one question before any core shadow integration:

Does the panel_id-derived hypothesis actually define a different grouping source than the current
heuristic `group_key_base` already used in stable outputs?

If the answer is "not really", then core integration is not yet justified.

## Inputs

- `_share/site_panel_id_hypothesis_latest.csv`
- `data/<site>/out/panel_day_risk_ensemble.csv`

The current grouping source is read from the stable `group_key_base` column in
`panel_day_risk_ensemble.csv`.

If that file or column is missing, the audit fails clearly. It does not silently guess another source.

## Candidate Groupings

Two neutral candidates are compared against current grouping:

- `candidate_group_token0 = token0_uuid`
- `candidate_group_token0_token1 = token0_uuid + "." + token1_group`

These are still neutral structural candidates. They are not asserted to be physical topology truth.

## Outputs

Generated files:

- `_share/site_grouping_equivalence_latest.csv`
- `_share/site_grouping_equivalence_summary.csv`
- `_share/site_grouping_mismatches.csv`

### site_grouping_equivalence_latest.csv

Minimum columns:

- `site`
- `panel_id`
- `current_group_key_base`
- `candidate_group_token0`
- `candidate_group_token0_token1`
- `match_token0`
- `match_token0_token1`

### site_grouping_equivalence_summary.csv

Minimum columns:

- `site`
- `total_panels`
- `current_unique_groups`
- `candidate_token0_unique_groups`
- `candidate_token0_token1_unique_groups`
- `match_rate_token0`
- `match_rate_token0_token1`
- `mismatch_panels_token0`
- `mismatch_panels_token0_token1`

### site_grouping_mismatches.csv

Rows where at least one candidate does not match current grouping.

## Decision Rule

Use this audit as a stop/go gate:

- if current grouping is already effectively equivalent to `token0.token1`, core integration is not yet justified
- if mismatch rates are materially large, then shadow integration may be worth testing later

This keeps the next step evidence-driven instead of assumption-driven.

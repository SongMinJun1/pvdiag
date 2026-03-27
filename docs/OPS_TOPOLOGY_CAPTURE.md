# OPS Topology Capture

## Purpose

Panel_id structure alone was not enough to establish explicit topology truth.

This patch turns manually saved webapp API responses into reproducible local inputs so the team can
check whether real topology mapping fields already exist in captured data.

## Capture Directory

Input directory:

- `data/manual/webapp_captures/`

Expected optional files per site:

- `<site>_reports.json`
- `<site>_latest_state.json`
- `<site>_panelmaps.json`
- `<site>_plant.json`
- `<site>_inverter.json`

Target sites:

- `conalog`
- `gangui`
- `ktc_ess`
- `sinhyo`

Missing files are allowed. The builder does not fail hard just because a capture is absent.

## Trust Rule

This patch only trusts explicit captured fields.

It looks for fields such as:

- `panel_id`, `panelPosition`, `map_id`
- `string`, `string_id`
- `mppt`, `mppt_id`
- `inverter`, `inverter_id`
- `channel`, `array`, `group`

It does not infer topology semantics from panel_id token structure.

## reports.json

`reports.json` is used only as metadata/reference if present:

- `panelCount`
- `inverterCount`
- `address`

It is not used as direct topology mapping.

## latest_state.json

`latest_state.json` may contain panel inventory.

Inventory extracted from `latest_state.json` is reference-only unless the same object also carries
explicit mapping fields.

## Candidate Rows

Generated file:

- `_share/site_topology_candidate_rows.csv`

Minimum columns:

- `site`
- `panel_id`
- `candidate_string_id`
- `candidate_mppt_id`
- `candidate_inverter_id`
- `source_kind`
- `source_field_path`
- `source_strength`
- `note`

## source_strength

Rules:

- `high`: explicit `panel_id` plus string/mppt/inverter trio or close equivalent
- `medium`: explicit `panel_id` plus inverter or explicit `panel_id` plus string
- `weak`: inventory-only or ambiguous mapping fields
- `none`: no usable candidate mapping

## Other Outputs

- `_share/site_topology_capture_summary.csv`
- `_share/site_topology_candidate_conflicts.csv`
- `_share/site_topology_missing_sources.csv`

`site_topology_candidate_conflicts.csv` lists panels whose candidate values disagree across capture
sources.

`site_topology_missing_sources.csv` is the per-site checklist for which capture files are still absent.

## Next Decision Rule

Use this patch as a gate:

- if strong or medium candidate coverage is substantial, proceed to topology shadow integration
- otherwise keep the core untouched and treat topology as unresolved

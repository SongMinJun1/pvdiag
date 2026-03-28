# OPS Topology Grouping

## Purpose

Heuristic `group_key` from `panel_id` is fragile.

It can mix panels that do not actually share the same:

- string
- MPPT
- inverter

That weakens peer baselines and can distort:

- peer power / voltage reference
- train-time `vbin` splitting
- group-off detection

## Topology-Aware Grouping

`panel_day_engine.py` can now load an optional topology CSV and use real topology IDs when available.

Supported grouping levels:

- `heuristic`
- `string`
- `mppt`
- `inverter`

CLI:

```bash
python pv_ae/panel_day_engine.py \
  --site conalog \
  --train-start 2024-09-06 \
  --train-end 2024-11-04 \
  --eval-start 2024-11-05 \
  --eval-end 2026-02-18 \
  --topology-csv path/to/topology.csv \
  --grouping-level string
```

## Topology CSV

Flexible column matching is supported.

Expected fields:

- `panel_id`
- `string_id` or `string`
- `mppt_id` or `mppt`
- `inverter_id` or `inverter`

Only `panel_id` is required.

## Fallback Semantics

Backward compatibility is preserved.

- if `--topology-csv` is absent, current heuristic grouping remains unchanged
- if a panel is missing from the topology map, that panel falls back to heuristic grouping
- if `--grouping-level heuristic` is selected, topology is ignored for grouping even if loaded

## Where It Matters

This patch changes the grouping source only.

It is now wired into:

- `load_day_curves(...)`
- `compute_event_features(...)`
- `build_vbin_map_from_train(...)`
- downstream `group_key_base` / `group_key` construction

That improves peer-comparison consistency when real topology is available.

## Diagnostics

Simple grouping diagnostics are persisted to log/meta outputs:

- `grouping_level`
- `topology_loaded`
- `panels_with_topology`
- `panels_without_topology`
- `fallback_to_heuristic_count`

## Scope

This patch does not change:

- thresholds
- alert logic
- event/weather/history sidecars
- canonical truth template contract

Only the grouping source changes.

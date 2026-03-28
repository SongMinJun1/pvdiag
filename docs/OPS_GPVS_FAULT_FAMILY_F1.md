# OPS GPVS Fault Family F1

## Purpose

This evaluator measures GPVS-based fault-family classification.

It is not routing F1.
It is not actionability F1.

The unit is panel-level coarse fault family on vendor-adjudicated rows.

## Inputs

- `_share/vendor_reply_adjudication_latest.csv`
- `_share/critical_actionability_shadow_v3_latest.csv`
- `_share/panel_onset_shadow_latest.csv`
- `data/<site>/out/panel_day_core.csv`

## Evaluation Scope

Use all vendor-adjudicated rows.

The current real set is 14 rows.

This keeps the evaluator focused on the question:

"How well does the current GPVS-derived classification recover coarse fault family?"

## Truth Mapping

Map `vendor_fault_family` to coarse truth labels:

- `diode_like` -> `electrical_fault_like`
- `module_damage_like` -> `electrical_fault_like`
- `open_or_device_issue_like` -> `open_or_device_issue_like`
- `group_or_inverter_side_like` -> `group_or_inverter_side_like`
- `none_visible` -> `none_visible`

Exclude rows where truth is blank, unknown, or otherwise not mapped.

## Prediction Mapping

Preferred source is current phenotype output:

- `electrical_fault_like` -> `electrical_fault_like`
- `open_or_device_issue_like` -> `open_or_device_issue_like`
- `group_or_inverter_side_like` -> `group_or_inverter_side_like`
- `common_cause_borderline` -> `group_or_inverter_side_like`
- `shape_only_monitor` -> `none_visible`
- `singleton_borderline_review` -> `uncertain`
- `weak_critical_candidate` -> `uncertain`

If a vendor-adjudicated panel is not present in current phenotype outputs, fall back to strict-day `panel_day_core` features:

- first compute zero-like strict-day evidence using existing fields only:
  - `mid_ratio <= 0.10`
  - `mid_i_ratio <= 0.10`
  - `coverage_mid >= 0.50`, or `coverage` if `coverage_mid` is unavailable
- then prefer same-day collapse evidence before isolated open/device fallback:
  - `group_or_inverter_side_like` if the target is zero-like and same-group zero-like count is at least 2, or same-site zero-like count is at least 3
  - `open_or_device_issue_like` if the target is zero-like and collapse evidence is absent
- if the target also trips the strict-day open/device shape, collapse evidence still wins before isolated open/device fallback
- otherwise fall back to the prior single-row feature checks:
  - `open_or_device_issue_like` if `mid_ratio <= 0.10` and `mid_v_ratio <= 0.10` and `v_drop >= 0.90`
  - `group_or_inverter_side_like` if `mid_ratio <= 0.10` and `mid_i_ratio <= 0.10` and `mid_v_ratio >= 1.05`
- otherwise `uncertain`

Group proxy for this fallback uses:

- `group_key_base` from `panel_day_core` when available
- otherwise deployed proxy from `panel_id` token0.token1

This precedence matters because same-day multi-panel collapse is operationally closer to a group or inverter-side issue than to an isolated open/device issue.
The refinement is intentionally narrow and safe: it targets the observed group-vs-open confusion without changing the currently disputed `uncertain` cases.

## Modes

### `closed_world`

`uncertain` stays in scoring as an ordinary wrong prediction.

This answers:

"How good is the classifier if abstention is not allowed?"

### `abstaining`

Rows predicted as `uncertain` are excluded from scoring.

Coverage is reported separately.

This answers:

"How good is the classifier on the cases where it makes a concrete family call?"

Current intentionally unchanged `uncertain` cases stay excluded only in this abstaining view.
They are not auto-promoted by the fallback refinement.

## Metrics

For each mode:

- `macro_f1`
- `weighted_f1`
- `accuracy`
- `coverage`

And class-wise:

- `precision`
- `recall`
- `f1`
- `support`

## Outputs

- `_share/gpvs_fault_family_eval_cases.csv`
- `_share/gpvs_fault_family_f1_summary.csv`
- `_share/gpvs_fault_family_confusion.csv`

`gpvs_fault_family_eval_cases.csv` also carries fallback diagnostics:

- `fallback_group_proxy`
- `same_group_zero_like_count`
- `same_site_zero_like_count`
- `fallback_rule_used`

`gpvs_fault_family_confusion.csv` uses coarse labels:

- `electrical_fault_like`
- `open_or_device_issue_like`
- `group_or_inverter_side_like`
- `none_visible`
- `uncertain` for `closed_world` prediction columns only

## Why This Is The Right F1

This is the correct answer to:

"What is the GPVS-based fault classification F1?"

Reason:

- truth is fault family, not actionability
- prediction is coarse family, not routing bucket
- packet routing and review packaging are downstream workflow layers

Those layers are useful operationally, but they are not the right unit for fault-family F1.

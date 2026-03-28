# OPS_MAINTENANCE_PROXY_CLUSTER_AUDIT_V1

## Purpose

`maintenance_proxy_shadow_f1_v1` looked numerically promising because the same-group shadow proxy recovered a portion of the current maintenance false-negative gap. But the same evaluator also selected 52 cases on the current full strict-case universe. That selected-case count is too large to interpret safely as panel-level maintenance promotion without another audit step.

This stage asks a narrower question:

- are these selected rows really panel-level maintenance candidates,
- or are they better understood as same-day group/common-cause incident signals?

This patch is audit-only. It does not modify any official prediction output.

## Why The Numeric Result Was Not Enough

A higher maintenance shadow F1 is not sufficient by itself.

If a truth-independent proxy selects many rows on the same site-day, the apparent gain may actually come from detecting a same-day event envelope rather than isolating panel-level maintenance targets. In that case, the signal may still be useful, but it belongs in common-cause review rather than direct maintenance promotion.

## Why Site Event vs Group Cluster Granularity Matters

This audit uses two aggregation levels.

### Site Event

`site_event_id = site + strict_trigger_date`

This answers:

- how many selected rows appeared on the same site-day?
- is the selection spread across many groups or concentrated inside one group?

### Group Cluster

`group_cluster_id = site + strict_trigger_date + fallback_group_proxy`

This answers:

- are selected rows concentrated in one same-day group?
- or are they distributed across many groups on the same site-day?

Those two views separate three different interpretations:

- broad site-day common-cause event
- concentrated same-group common-cause event
- true singleton/panel-level review signal

## Why This Is Not Another Maintenance Rule

The output labels from this audit are descriptive only.

They do not get written back into:

- `critical_actionability_shadow_v3_latest.csv`
- routing outputs
- packet outputs
- any canonical truth file

This stage is not a rule change. It is a reinterpretation audit of an existing shadow selection.

## Algorithm-Side Inputs Only

This audit keeps the same discipline as the proxy shadow evaluator.

The cluster structure is derived from:

- selected shadow rows
- strict-day `panel_day_core` grouping context
- same-day group proxy membership

Vendor and manual labels are included only as context flags for reading the output. They are not used as direct interpretation rules.

## Cluster Interpretation Rules

Each `group_cluster_id` is classified as one of:

- `broad_site_day_cluster`
- `concentrated_group_cluster`
- `singleton_cluster`
- `ambiguous_cluster`

Fixed audit rules:

1. `broad_site_day_cluster`
   - `site_event_selected_count >= 10`
   - and `group_cluster_share_of_site_event < 0.50`

2. `concentrated_group_cluster`
   - `member_panel_count >= 3`
   - and `group_cluster_share_of_site_event >= 0.50`

3. `singleton_cluster`
   - `member_panel_count == 1`

4. otherwise
   - `ambiguous_cluster`

Recommended interpretation:

- `broad_site_day_cluster -> common_cause_site_event_signal`
- `concentrated_group_cluster -> common_cause_group_signal`
- `singleton_cluster -> panel_level_review_signal`
- `ambiguous_cluster -> needs_manual_cluster_review`

## What Would Justify Redirecting The Signal

Results that support redirecting this proxy toward common-cause review rather than panel-level maintenance:

- most selected rows collapse into a small number of same-day clusters
- site-day selected counts are large
- cluster share indicates broad event structure rather than isolated panels
- vendor/manual context, when present, is consistent with group/common-cause interpretation

Results that would support keeping panel-level maintenance interpretation alive:

- selected rows mostly appear as singleton clusters
- or a small number of concentrated same-group clusters with limited site-wide spillover
- and selected-case count stays modest

## Outputs

- `_share/maintenance_proxy_cluster_audit_summary_v1.csv`
- `_share/maintenance_proxy_cluster_audit_clusters_v1.csv`
- `_share/maintenance_proxy_cluster_audit_cases_v1.csv`

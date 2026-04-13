# OPS_MAINTENANCE_PROXY_EVENT_OVERLAP_AUDIT_V1

## Purpose

`maintenance_proxy_cluster_audit_v1` changed the reading of the current maintenance-proxy shadow from panel-level maintenance promotion toward same-day common-cause signal. The next question is whether that signal is already covered by the existing site-day event / alert-episode layers.

This patch is audit-only. It does not modify any official prediction output.

## Why This Check Comes Next

Once the proxy is no longer interpreted as panel maintenance, the main risk changes.

- If the proxy mostly overlaps with the existing event-frame or alert-episode layers, it is probably redundant.
- If it appears just before an episode, it may still be useful as an early common-cause addon.
- If it misses both layers entirely, it may represent a novel common-cause candidate that deserves deeper review.

We need that answer before considering any upstream use of the signal.

## Audit Universe

The audit uses one row per group cluster from:

- `_share/maintenance_proxy_cluster_audit_clusters_v1.csv`

Case-level rows from:

- `_share/maintenance_proxy_cluster_audit_cases_v1.csv`

are used only to recover total selected-case counts for summary context.

## Event-Frame Overlap

The builder joins `_share/site_day_event_frame_latest.csv` on:

- `site`
- `strict_trigger_date == date`

Preferred same-day event columns:

- `event_day_flag`
- `site_event_flag`
- `event_flag`

If none of those exist, the builder falls back to the most inclusive available event-style binary column and records the chosen column in:

- `frame_event_column_used`

This makes the overlap decision auditable even when event-frame schemas vary.

## Alert-Episode Overlap

The builder joins `_share/site_day_alert_episodes_latest.csv` by site and then checks:

- whether `strict_trigger_date` falls inside `[episode_start_date, episode_end_date]`

If there is no window overlap, it also tracks the nearest future episode start. That allows a separate classification for signals that lead an episode by 1 to 3 days.

## Overlap Types

Each cluster is assigned exactly one `overlap_type`:

1. `exact_frame_event_overlap`
   - `frame_event_overlap_flag == 1`

2. `episode_window_overlap`
   - no exact frame overlap
   - and `episode_overlap_flag == 1`

3. `lead_before_episode`
   - no exact/frame overlap
   - no episode window overlap
   - nearest episode starts 1 to 3 days later

4. `no_existing_event_overlap`
   - none of the above

## Recommended Disposition

- `exact_frame_event_overlap -> redundant_with_existing_event_layer`
- `episode_window_overlap -> redundant_with_existing_episode_layer`
- `lead_before_episode -> potential_early_common_cause_signal`
- `no_existing_event_overlap -> novel_common_cause_candidate`

These labels are descriptive only. They are not written back into any official prediction layer.

## How To Read The Result

### Redundant

If most clusters land in:

- `redundant_with_existing_event_layer`
- or `redundant_with_existing_episode_layer`

then the current maintenance-proxy cluster signal is likely not adding much beyond the existing event/episode pipeline.

### Early Addon

If a meaningful share lands in:

- `potential_early_common_cause_signal`

then the signal may still be useful as an earlier common-cause warning layer.

### Novel Candidate

If many clusters land in:

- `novel_common_cause_candidate`

then the signal may be finding site-day/group failures that the current event/episode pipeline misses.

## What Would Justify Upstream Use

Results that could justify using this signal as an early/common-cause addon:

- low redundancy with same-day frame events
- low redundancy with episode windows
- repeated `lead_before_episode` behavior
- modest selected-cluster count with stable grouping structure

Results that argue against upstream use:

- near-total overlap with existing frame events
- near-total overlap with alert-episode windows
- inconsistent overlap behavior across sites
- broad activation without any timing advantage

## Outputs

- `_share/maintenance_proxy_event_overlap_summary_v1.csv`
- `_share/maintenance_proxy_event_overlap_clusters_v1.csv`
- `_share/maintenance_proxy_event_overlap_matches_v1.csv`

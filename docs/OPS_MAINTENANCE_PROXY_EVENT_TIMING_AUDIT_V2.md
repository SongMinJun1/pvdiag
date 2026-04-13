# OPS_MAINTENANCE_PROXY_EVENT_TIMING_AUDIT_V2

## Purpose

`maintenance_proxy_event_overlap_audit_v1` showed that the current maintenance-proxy cluster signal overlaps the existing event layer. But the real frame column used there was `event_within_7d`, which is a timing window, not an exact same-day event indicator.

That means `v1` can over-call redundancy.

This patch refines the timing semantics so we can separate:

- true exact same-day redundancy,
- loose frame-window overlap,
- 1 to 3 day lead behavior before an alert episode,
- and genuinely novel cases.

This stage is audit-only. It does not modify any official prediction output.

## Why Overlap V1 Could Over-Call Redundancy

If a cluster fires on day `D` and the frame layer says `event_within_7d = 1`, that only tells us an event exists somewhere in the following 7-day window. It does not prove the proxy cluster is redundant on day `D`.

That difference matters:

- same-day overlap suggests redundancy
- 1 to 3 day lead suggests possible early signal
- loose window overlap without same-day alignment is ambiguous

## Exact vs Window Semantics

This builder emits two separate frame indicators:

- `exact_same_day_event_flag`
- `within_frame_window_flag`

Rules:

- exact same-day uses only true same-day event columns when available
  - examples: `event_day_flag`, `site_event_flag`, `event_flag`, `event_today`
- broad timing-window columns such as `event_within_7d` are never treated as exact
- if only a window column exists, it contributes only to `within_frame_window_flag`

That is the core correction over `v1`.

## Timing Classification

Each cluster is assigned one `timing_overlap_type`:

1. `exact_same_day_event_overlap`
   - exact same-day event flag is on

2. `episode_window_overlap`
   - no exact same-day overlap
   - cluster date falls inside an episode window

3. `lead_before_episode`
   - no exact same-day overlap
   - not inside an episode window
   - nearest episode starts 1 to 3 days later

4. `within_frame_window_only`
   - no exact same-day overlap
   - no episode-window overlap
   - no 1 to 3 day lead
   - but a broad frame-window event flag is on

5. `no_existing_event_overlap`
   - none of the above

## Recommended Disposition

- `exact_same_day_event_overlap -> redundant_exact_event_signal`
- `episode_window_overlap -> redundant_episode_signal`
- `lead_before_episode -> potential_early_common_cause_signal`
- `within_frame_window_only -> ambiguous_event_window_signal`
- `no_existing_event_overlap -> novel_common_cause_candidate`

## What Would Justify Treating The Signal As Early Common-Cause

Evidence in favor:

- few or no exact same-day overlaps
- repeated `lead_before_episode` cases
- modest selected-cluster counts
- stable site/group concentration rather than diffuse spillover

That would support reading the signal as an early common-cause addon rather than a duplicate of the existing event layer.

## What Would Close This Line As Redundant

Evidence against further use:

- most clusters land in `exact_same_day_event_overlap`
- or most clusters fall directly inside existing episode windows
- and very few clusters show 1 to 3 day lead timing

In that case the proxy is mostly telling us what the existing event/episode pipeline already tells us.

## Outputs

- `_share/maintenance_proxy_event_timing_summary_v2.csv`
- `_share/maintenance_proxy_event_timing_clusters_v2.csv`
- `_share/maintenance_proxy_event_timing_matches_v2.csv`

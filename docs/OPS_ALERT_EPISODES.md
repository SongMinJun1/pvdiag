# OPS Alert Episodes

## Purpose

Day-level alert evaluation overstates operational burden because repeated alert days often correspond to one operational follow-up window, not many independent actions.

`site_day_alert_episodes_latest.csv` compresses day-level alert rows into event-level alert episodes.

`site_day_alert_episode_summary.csv` gives a first episode-level view of operational utility.

## Inputs

- `_share/site_day_event_frame_latest.csv`
- `_share/site_day_event_risk_latest.csv`
- `_share/site_event_groups_latest.csv`

## Trigger Modes

Two trigger modes are evaluated:

- `high_only`
- `medium_or_higher`

This lets operations compare stricter versus broader alerting without changing the underlying score.

## Episode Definition

Within each `site` and `trigger_mode`, consecutive alert days form one episode.

Initial version:

- `gap_tolerance_days = 0`

That means only directly consecutive calendar days are merged into one episode. A one-day gap starts a new episode.

## Episode Fields

Each episode records:

- episode start and end
- duration and number of alert days
- peak risk score, peak band, and peak date
- episode-start eligibility for 1d / 3d / 7d horizons
- episode-start future match flags
- next matched event and review group
- lead from episode start and lead from peak
- weather confound summary over the episode

## Matching Rule

This first version uses the episode start day as the primary evaluation anchor.

For each episode:

- read the frame row at `episode_start_date`
- use that row's `event_within_1d / 3d / 7d`
- use that row's `next_event_date`
- use that row's `next_review_group`

This is intentionally simple and interpretable.

## Episode Summary

The summary file reports:

- `total_episodes`
- eligibility-aware episode denominators for 1d / 3d / 7d
- matched episode counts and matched rates
- `false_episodes_7d`
- median duration
- median lead from start and from peak
- `alert_days`
- `compression_ratio`

Matched rates use eligibility-aware denominators only.

If a denominator is zero, the matched rate is left blank / `NaN`, not `0.0`.

## compression_ratio

`compression_ratio = alert_days / total_episodes`

Interpretation:

- larger ratio means more day-level alerts are being compressed into fewer operational episodes
- value near `1.0` means alert days are mostly isolated and compress poorly
- blank / `NaN` means `total_episodes = 0`, so the ratio is not defined

## Caveat

This is the first episode-level operational view.

It is useful for measuring operational burden and early utility, but it is not yet a fully optimized alert policy.

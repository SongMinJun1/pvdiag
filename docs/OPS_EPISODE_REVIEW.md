# OPS Episode Review

## Purpose

Episode-level truth closure is the next operational step after day-level and episode-level alert compression.

The goal is simple:

- reduce repeated alert days into compact review units
- hand reviewers a bounded episode list instead of more threshold tuning
- collect episode-level adjudication that can guide the next iteration

This layer is for manual review support, not automated scoring.

## Inputs

- `_share/site_day_alert_episodes_latest.csv`
- `_share/site_day_alert_episode_summary.csv`
- `_share/site_event_dataset_latest.csv`
- `_share/field_truth_template.csv`
- `_share/field_truth_template_meta.csv`

## Selection Rules

`episode_review_pack_latest.csv` is intentionally compact.

Selection rule:

- include all `high_only` episodes
- include `medium_or_higher` episodes only when their date range does not overlap any `high_only` episode from the same site

This keeps both trigger modes visible while avoiding obvious duplicate review rows.

## Review Pack Fields

`episode_review_pack_latest.csv` contains the selected episode rows with:

- episode timing and duration
- peak risk band and score
- matched review group and next event date
- lead from episode start
- `likely_common_issue`
- `event_confidence_level`
- event-day `weather_tag`
- episode-level `weather_confound_any`
- `review_priority`

`likely_common_issue`, `event_confidence_level`, and `weather_tag` come from the matched event dataset when a matched review group exists.

## review_priority

Priority is annotation only for human triage.

- `P1`: `high_only` and episode-start eligible
- `P2`: selected `medium_or_higher` and `event_confidence_level != low`
- `P3`: all remaining selected rows

Episode-start eligible means at least one of:

- `eligible_1d = 1`
- `eligible_3d = 1`
- `eligible_7d = 1`

## Episode Truth Template

`episode_truth_template.csv` is separate from the panel-level `field_truth_template.csv`.

It is intentionally smaller and episode-oriented:

- one row per selected episode
- `episode_id` is a review-row identifier derived from `trigger_mode + original episode_id` so it stays unique within each site
- matched review group carried forward when available
- `our_interpretation` populated from existing panel-level truth-template interpretation when that review group already exists
- manual truth columns left blank for reviewer entry

This file does not change the canonical panel-level truth template contract.

## Manual Adjudication Use

Reviewers should use the episode template to capture:

- detected date
- estimated started date
- actual issue type
- actual primary view
- action taken
- manual episode match decision
- free-form notes

This is a truth-closure workflow, not an automated evaluation layer.

## Why This Layer Exists

Downstream tuning without reviewed episode closure has a hard limit.

This patch shifts the workflow toward:

- compact reviewable operational units
- lower duplicate review burden
- cleaner feedback for the next iteration

That is the intended next step before more score tuning or more topology/weather embellishment.

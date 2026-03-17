# OPS Event Dataset

## Purpose

`site_event_dataset_latest.csv` is an event-level sidecar dataset for review and annotation. It summarizes each existing `review_group` from `_share/site_event_groups_latest.csv` and attaches provenance/confidence aggregation from `_share/field_truth_template_meta.csv` plus optional manual weather notes.

This file is annotation-only. It does not change alert thresholds, candidate selection, or the stable validation scaffold outputs.

## Inputs

Required:

- `_share/site_event_groups_latest.csv`
- `_share/field_truth_template_meta.csv`

Optional manual input:

- `data/manual/site_weather_daily.csv`

## Manual Weather Schema

`site_weather_daily.csv` uses this schema:

- `site`
- `date`
- `weather_tag`
- `sun_hours`
- `rain_flag`
- `cloud_flag`
- `weather_confidence`
- `note`

A blank template is generated automatically at `_share/site_weather_daily_template.csv` with one row per unique `(site, representative_date)` from the current event groups.

If the manual file is absent, `site_event_dataset_latest.csv` is still generated with:

- `weather_available = 0`
- weather fields blank
- `weather_confound_flag` blank

## Provenance / Confidence Aggregation

`site_event_dataset_latest.csv` aggregates `_share/field_truth_template_meta.csv` by `(site, review_group)`.

Count columns:

- `n_alert_history_temporal`
- `n_historical_reconstruction`
- `n_row_evidence_fallback`
- `n_current_review_fallback`
- `n_guard_applied`
- `n_low_confidence`
- `n_medium_confidence`
- `n_high_confidence`
- `n_abstain`

These counts are descriptive. They do not filter rows.

## event_confidence_level Rule

`event_confidence_level` uses this exact annotation-only rule:

- `high` if `n_alert_history_temporal > 0` and `n_guard_applied == 0`
- `medium` if `n_row_evidence_fallback > 0` or `n_historical_reconstruction > 0`
- `low` if `n_abstain == panel_count`
- otherwise `unknown`

This is an annotation label, not a predictive score.

## weather_confound_flag Rule

`weather_confound_flag` uses this exact annotation-only rule:

- `1` if `rain_flag == 1`
- `1` if `weather_tag in {cloudy, mixed}` and `cloud_flag == 1`
- `0` otherwise
- blank if weather is unavailable

## Output Columns

`site_event_dataset_latest.csv` includes at least:

- event identity: `site`, `review_group`, `representative_date`, `event_start_date`, `event_end_date`
- event scope: `panel_count`, `panel_ids`, `likely_common_issue`, `summary`
- provenance/confidence counts listed above
- `event_confidence_level`
- weather columns: `weather_available`, `weather_tag`, `sun_hours`, `rain_flag`, `cloud_flag`, `weather_confidence`, `weather_confound_flag`, `weather_note`

## Scope and Caveats

- This patch is sidecar-only. It does not modify stable validation outputs.
- Weather values are manual annotations, not automated meteorological joins.
- `event_confidence_level` is a summary label of provenance quality, not a calibrated risk model.
- This dataset is not yet a predictive event-risk model. It is a review/analysis scaffold for later validation or confound checks.

# OPS Weather History

## Purpose

`site_weather_history_latest.csv` is a full score-window weather sidecar. It tracks daily weather annotations for each site from the beginning of the score window through the current latest raw date.

This is separate from the stable validation scaffold. It does not change alert thresholds, candidate selection, or the canonical field-truth contract.

## Why Score Window Only

This first version uses the score window only:

- start: `train_end + 1`
- end: `site_latest_raw_date`

Baseline train days are excluded on purpose. The immediate goal is to annotate the same date range that can affect operational scoring and event review, without expanding into healthy-baseline backfill yet.

## Inputs

Required operational/config inputs:

- `configs/sites/*.yaml`
- `data/<site>/out/latest_site_summary.csv`

Manual inputs:

- `data/manual/site_addresses.csv`
- `data/manual/site_weather_daily.csv`

## Address File Schema

`site_addresses.csv` columns:

- `site`
- `address`
- `weather_enabled`
- `note`

If this file is missing or the site address is blank, the history still builds and marks missing reason accordingly.

## Manual Weather Daily Schema

`site_weather_daily.csv` columns:

- `site`
- `date`
- `weather_tag`
- `sun_hours`
- `rain_flag`
- `cloud_flag`
- `weather_confidence`
- `note`

## Merge Priority

For each `(site, date)` in the score window:

1. if `site_weather_daily.csv` has a matching row with usable weather content, use it
2. else `weather_available = 0`
3. if address is missing, `weather_missing_reason = missing_address`
4. else if `weather_enabled = 0`, `weather_missing_reason = address_disabled`
5. else `weather_missing_reason = missing_weather_row`

`weather_source` values:

- `observed_api`
- `manual_entry`
- `unknown`

The source is derived from the manual weather row note when possible. Filled rows without a recognizable source marker use `unknown`.

## Outputs

### `_share/site_weather_history_latest.csv`

At minimum:

- `site`
- `date`
- `score_window_flag`
- `weather_available`
- `weather_tag`
- `sun_hours`
- `rain_flag`
- `cloud_flag`
- `weather_confidence`
- `weather_source`
- `weather_missing_reason`
- `note`

### `_share/site_weather_history_coverage.csv`

At minimum:

- `site`
- `score_window_days`
- `weather_available_days`
- `missing_weather_days`
- `coverage_rate`
- `missing_address_flag`

### `_share/site_weather_request_template.csv`

Operator work queue columns:

- `site`
- `address`
- `date`
- `reason`

This file lists score-window dates where weather is still missing.

## Event Dataset Integration

`build_site_event_dataset.py` now prefers joining event rows from `_share/site_weather_history_latest.csv` on `(site, representative_date)` when the weather-history workflow is available.

If the history sidecar is not available, the existing direct daily weather fallback remains in place. Event output schema does not change.

## Scope and Caveats

- This is an annotation/history sidecar, not a predictive event-risk model.
- Missing weather rows are expected in early passes; coverage is reported separately.
- `site_weather_request_template.csv` is intentionally operational. It is a fill queue, not a model artifact.

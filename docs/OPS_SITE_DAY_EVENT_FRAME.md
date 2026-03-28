# OPS Site-Day Event Frame

## Purpose

`site_day_event_frame_latest.csv` builds one row per `(site, date)` across the full score window. It is a leakage-safe analysis frame for weak event-risk baselines and future site-level validation work.

`site_day_event_risk_latest.csv` adds a simple heuristic risk score and band on top of that frame.

This is a first baseline only. It does not modify core scoring, canonical truth templates, or stable operational outputs.

The score formula itself is unchanged. Only the `risk_band` calibration is updated.

## End-of-Day Decision-Time Assumption

This frame assumes end-of-day decision time:

- same-day operational counts may be available
- future event labels are defined strictly after the current date

Because of this, `event_today` is a label only and is not used directly as a model feature.

## Label Definitions

Event labels come from `_share/site_event_dataset_latest.csv`.

- `event_today = 1` if `date == representative_date`
- `event_within_1d = 1` if an event occurs on the next day
- `event_within_3d = 1` if an event occurs within 1-3 days after the current date
- `event_within_7d = 1` if an event occurs within 1-7 days after the current date

Also included:

- `next_event_date`
- `next_review_group`
- `next_event_confidence_level`
- `future_event_low_confidence_flag`

These are labels / reference columns only. They are not leakage-safe features.

## Horizon Eligibility and Right-Censoring

Site-tail rows near the latest raw date cannot validly evaluate future horizons. The frame therefore adds:

- `eligible_1d = 1` iff `date + 1 day <= site_latest_raw_date`
- `eligible_3d = 1` iff `date + 3 days <= site_latest_raw_date`
- `eligible_7d = 1` iff `date + 7 days <= site_latest_raw_date`

The stored labels remain unchanged and binary. Right-censoring is handled in evaluation by using only eligible rows for the corresponding horizon.

This patch fixes horizon evaluation before any score-threshold tuning.

`site_day_event_risk_summary.csv` now reports:

- overall `eligible_days_1d`, `eligible_days_3d`, `eligible_days_7d`
- per-band `high_eligible_days_*`, `medium_eligible_days_*`, `low_eligible_days_*`
- horizon positive rates computed only on the corresponding eligible rows

If a band has zero eligible days for a horizon, the corresponding positive rate is left blank / `NaN`.
That means not evaluable, not zero performance.

## Features

The frame uses only same-day or past-available quantities:

- weather fields from `_share/site_weather_history_latest.csv`
- stable site rollup counts when available from `data/<site>/out/site_daily_rollup.csv`
- past-only recency features:
  - `days_since_last_event`
  - `recent_event_count_30d`

Current rollup inputs are sparse in this repo state, so most historical site-count features are zero except where a stable daily rollup row exists.

## Leakage-Safe Feature Policy

Do not use the following as model features:

- `next_event_date`
- `next_review_group`
- `next_event_confidence_level`
- `future_event_low_confidence_flag`
- `event_today`
- `event_within_1d`
- `event_within_3d`
- `event_within_7d`
- any manual truth columns
- any future-derived quantities

`days_since_last_event` and `recent_event_count_30d` are computed from strictly past event dates only.

Site-tail rows with `eligible_* = 0` are not valid evaluation rows for the corresponding future horizon.

## weather_confound_flag_calc

If weather is available:

- `1` if `rain_flag == 1`
- `1` if `weather_tag in {cloudy, mixed}` and `cloud_flag == 1`
- `0` otherwise

If weather is unavailable, the value is blank.

## Weak Baseline Risk Score

`site_day_event_risk_latest.csv` adds:

- `risk_score_heuristic`
- `risk_band` in `{high, medium, low}`

The heuristic uses:

- same-day site counts when available
- past-only event recency features
- weather only as a weak adjustment term

Weather is not a hard gate.

## Risk Band Calibration

`risk_band` is now calibrated from eligible rows only.

Define:

- `eligible_any = eligible_1d == 1 or eligible_3d == 1 or eligible_7d == 1`

Thresholds are computed on `risk_score_heuristic` over `eligible_any` rows only:

- `q98` for `high`
- `q90` for `medium`

Assignment rule:

- `high` if `score >= q98`
- `medium` if `q90 <= score < q98`
- `low` otherwise

The calibrated thresholds are then applied to all rows, including ineligible site-tail rows.

Fixed thresholds were replaced because the previous `high` band could collapse to only horizon-ineligible tail rows. The score formula is unchanged; only the band calibration changed.

The risk file keeps the horizon labels for later enrichment checks, but the labels are not used as baseline features.

In the summary file, a blank `*_positive_rate_*` means the band had no eligible rows for that horizon.
Do not read that case as "failed" or "0.0".

## Scope and Caveat

- This is a first weak baseline, not a calibrated predictive model.
- It is intended for framing and enrichment checks, not deployment decisions.
- Stable validation scaffold outputs remain unchanged.

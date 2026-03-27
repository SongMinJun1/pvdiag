# OPS Panel Onset Shadow

## Purpose

Current strict trigger dates are useful for conservative alerting, but they are often too late for gradual degradation cases.

This shadow layer estimates a more useful retrospective onset date for panels that are already strict cases in current outputs.

It does not create new candidates.

## Candidate Conservation

This patch is strict-case preserving by design.

- current strict cases are identified from existing latest panel status outputs
- only those panels are processed
- one strict case yields at most one shadow onset row
- no new panel candidates are introduced

## Key Dates

Each shadow row carries three dates:

- `strict_trigger_date`
- `first_warning_date`
- `retrospective_onset_date`

Interpretation:

- `strict_trigger_date` is the first strict day reconstructed from current day-level core outputs
- `first_warning_date` is the earliest weak warning within the lookback window
- `retrospective_onset_date` is the earliest persistent low-threshold onset that survives recovery-break and confound checks

## Why This Is Needed

Abrupt faults often have little useful lead time.

Gradual degradation can show:

- weaker ratio drift
- repeated small voltage-drop style evidence
- persistent but sub-trigger abnormality

This patch tries to recover that earlier onset retrospectively without changing the current engine.

## Signals Used

Only existing `panel_day_core.csv` fields are used when available:

- `mid_ratio`
- `last_ratio`
- `v_drop`
- `v_ref_ok`
- `coverage_mid`
- `shadow_like`
- `group_off_like`
- `recon_error` as an AE-like error proxy when available

Signals are smoothed with a 7-day rolling window.

## Onset Rule

Current shadow rule:

- use past `60` days by default
- compute a low-threshold onset score from smoothed panel-day signals
- require persistence on at least `5` of `7` days
- reset early onset if there is a long full recovery of at least `10` consecutive normal days before the strict trigger
- do not trust early onset when the pattern is primarily explained by `shadow_like` or `group_off_like`

If no reliable earlier onset is found, the shadow row falls back to the strict trigger date and marks confidence accordingly.

## Confidence

Confidence is annotation only:

- `high`
- `medium`
- `low`

Typical meaning:

- `high`: persistent earlier onset with low confound fractions
- `medium`: usable but weaker or shorter earlier onset
- `low`: fallback or strongly confounded case

Low-confidence rows are still emitted because the point of this patch is visibility, not filtering.

## Suspicious Rows

`panel_onset_shadow_suspicious.csv` isolates rows that need extra caution:

- low confidence
- high shadow/group-off fractions
- implausibly early lead
- recovery-break inconsistency

## Scope Guard

This is a shadow-only analysis layer.

It does not change:

- `pv_ae/panel_day_engine.py`
- current strict candidate generation
- current weather/event/frame/episode outputs
- canonical panel-level field truth contract

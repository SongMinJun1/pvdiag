# OPS Critical Phenotype Shadow V2

## Purpose

Single-day anchor classification was too brittle for critical cases.

This v2 shadow layer reclassifies existing `critical_fault_flag` cases using window consensus, while separating:

- electrical evidence that may justify maintenance review
- shape-only anomaly evidence that should remain monitor-only

It does not change the current core engine.

## Why Single-Day Anchor Was Insufficient

A single local peak day can be misleading because:

- one noisy day can dominate `v_drop`
- one-day confounds can distort the phenotype
- the strongest operational signal may be the window pattern, not the single most extreme point

So v2 uses `strict_trigger_date ± 7 days` as the primary classification window.

`anchor_date` is still emitted, but only as a representative date.

## Window Consensus

Definitions:

- `valid_day`
  - `v_ref_ok == True`
  - `coverage_mid >= 0.85`
  - `shadow_like == False`
  - `group_off_like == False`

- `diode_evidence_day`
  - `mid_v_ratio <= 0.75`
  - `v_drop >= 0.28`
  - `mid_i_ratio >= 0.85`

The v2 classifier uses:

- `valid_days`
- `evidence_days`
- `evidence_ratio`
- window medians of the main electrical features

## Phenotypes

Current v2 phenotypes:

- `electrical_fault_like`
- `open_or_device_issue_like`
- `group_or_inverter_side_like`
- `borderline_electrical_review`
- `shape_only_monitor`
- `weak_critical_candidate`

## Actionability Separation

This is the key v2 change.

Strong AE / DTW / relative shape anomaly alone must not directly promote a maintenance phenotype.

Reason:

- shape anomaly can be operationally interesting
- but without stable electrical evidence it is not yet a strong maintenance candidate

So v2 keeps those rows as:

- `shape_only_monitor`

not as electrical maintenance phenotypes.

## Shape Support

`shape_support_flag` is raised when relative shape anomaly is strong, for example:

- high same-day `recon_error` percentile
- high same-day `dtw_dist` percentile

This flag is supportive context only.

It is not enough by itself to create a maintenance-oriented electrical class.

## Cluster Guard

`cluster_guard_flag` is a safety diagnostic.

It is raised when same-day evidence prevalence within the site is high.

This may indicate:

- site-wide disturbance
- shared operating context
- broader cluster behavior

It is not the main decision rule.

## Vendor Labels

Vendor labels remain audit-only inputs.

They are useful for review, but they are not direct classification rules.

This patch does not let vendor labels override the phenotype rules.

## Scope Guard

This patch does not change:

- `pv_ae/panel_day_engine.py`
- current critical trigger generation
- weather/event/frame/episode logic
- vendor adjudication builder
- canonical truth template contract

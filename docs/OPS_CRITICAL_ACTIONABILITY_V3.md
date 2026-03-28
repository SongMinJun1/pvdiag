# OPS Critical Actionability V3

## Purpose

V2 already solved the most important split:

- electrical evidence that may justify maintenance review
- shape-only anomaly evidence that should remain monitor-only

The remaining ambiguity is inside:

- `borderline_electrical_review`

Some borderline rows look like common-cause or cluster behavior.
Others still look like singleton review candidates.
And a smaller remaining subset of singleton review candidates look too early and too isolated to escalate operationally.

V3 separates those two cases without changing the core engine.

## Scope Guard

This patch does not change:

- `pv_ae/panel_day_engine.py`
- weather, event, frame, episode generation logic
- vendor adjudication builder outputs
- `critical_phenotype_shadow_v2` outputs in place
- canonical truth template contract

It only re-buckets existing v2 rows.

## Candidate Conservation

V3 is candidate-conserving.

- input rows come from `_share/critical_phenotype_shadow_v2_latest.csv`
- no new panel candidates are created
- each v2 row produces at most one v3 row

## What Changes From V2

These v2 phenotypes stay unchanged:

- `electrical_fault_like`
- `open_or_device_issue_like`
- `group_or_inverter_side_like`
- `shape_only_monitor`
- `weak_critical_candidate`

Only this phenotype is split:

- `borderline_electrical_review`

into:

- `common_cause_borderline`
- `singleton_borderline_review`
- `singleton_monitor_hold`

## Borderline Common-Cause Signals

For each v2 borderline row, v3 computes anchor-date context:

- `same_site_borderline_count_anchor_date`
- `same_site_borderline_rate_anchor_date`
- `same_group_borderline_count_anchor_date`
- `same_group_borderline_rate_anchor_date`

Primary group source:

- `group_key_base` from `data/<site>/out/panel_day_core.csv`

Fallback if unavailable:

- current deployed proxy based on `panel_id` token0.token1

## Reclassification Rule

`common_cause_borderline` if:

- `cluster_guard_flag == 1`
- and:
  - `same_site_borderline_count_anchor_date >= 3`
  - or `same_group_borderline_count_anchor_date >= 2`

Otherwise:

- `singleton_borderline_review`

## Isolated Long-Horizon Singleton Hold

V3 common-cause splitting was not enough.

There is still a narrow false-positive pattern inside singleton borderline rows:

- isolated row
- not cluster-like
- very early relative to strict trigger
- persistent enough to look suspicious
- but too long-horizon to route as an operational singleton review by default

For rows that would otherwise become `singleton_borderline_review`, V3 now checks onset-shadow context from `_share/panel_onset_shadow_latest.csv`.

Use:

- `days_earlier_than_trigger`
- `onset_confidence`
- `onset_method`
- parsed `strict_method` from onset-shadow `reason_summary`

Hold rule:

- `cluster_guard_flag == 0`
- `parsed_strict_method == critical_fault_flag`
- `days_earlier_than_trigger >= 30`
- `onset_confidence == high`
- `onset_method == persistent_5of7`

If all are true:

- `critical_phenotype_v3 = singleton_monitor_hold`
- `actionability_v3 = monitor_only`

Otherwise the existing mapping stays:

- `singleton_borderline_review -> singleton_review`

If onset-shadow context is missing or the token parse fails:

- do not crash
- do not activate the hold rule
- preserve the existing singleton review behavior

## Actionability

V3 emits `actionability_v3`:

- `maintenance_candidate`
  - `electrical_fault_like`
  - `open_or_device_issue_like`
  - `group_or_inverter_side_like`
- `common_cause_review`
  - `common_cause_borderline`
- `singleton_review`
  - `singleton_borderline_review`
- `monitor_only`
  - `shape_only_monitor`
  - `weak_critical_candidate`
  - `singleton_monitor_hold`

## Why This Patch Is Safe

This patch does not promote borderline rows into hard positive maintenance cases.
It only demotes a narrow subset of singleton borderline rows to monitoring.

If the common-cause judgment is wrong, the row still remains inside the review bucket.
If the singleton long-horizon hold is wrong, the row is still retained as a monitored candidate, not relabeled as a false positive.

So the failure mode is limited:

- review routing may be imperfect
- but the patch does not create a false maintenance-positive class

Vendor labels are not used as direct decision rules here.

They remain audit context only.

The hold rule is based only on:

- existing actionability context
- onset-shadow context already generated on our side

## Interpretation

Use `actionability_v3` as routing guidance:

- `maintenance_candidate`
  - strong enough for maintenance-oriented review
- `common_cause_review`
  - likely cluster/common-cause context; avoid over-treating as singleton maintenance
- `singleton_review`
  - keep as per-panel review candidate
- `monitor_only`
  - monitor, contextualize, and do not escalate directly to maintenance
  - includes long-horizon isolated singleton borderline holds that are too weak for immediate operational singleton review

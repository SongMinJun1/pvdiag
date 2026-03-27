# OPS Critical Case Routing V4

## Purpose

V3 already solved the phenotype and actionability split.

V4 does not add another model tweak.

It converts existing v3 rows into operational routing outputs:

- outbound maintenance candidates
- cluster-level common-cause review
- singleton internal review
- monitor archive

## Scope Guard

This patch does not change:

- `pv_ae/panel_day_engine.py`
- weather, event, frame, episode generation logic
- vendor adjudication builder
- `critical_actionability_shadow_v3` outputs in place
- canonical truth template contract

It only routes current v3 rows.

## Candidate Conservation

V4 is candidate-conserving.

- input rows come from `_share/critical_actionability_shadow_v3_latest.csv`
- no new panel candidates are created
- each v3 row is routed exactly once

## Routing Semantics

### Outbound

`actionability_v3 == maintenance_candidate`

These rows go to:

- `_share/critical_outbound_candidates_v4.csv`

This is the panel-level outbound maintenance queue.

### Common-Cause Review

`actionability_v3 == common_cause_review`

These rows are not sent panel-by-panel.

They are aggregated into cluster rows in:

- `_share/critical_cluster_review_v4.csv`

Cluster key:

- `site`
- `anchor_date`
- `group_key_base` if available from `panel_day_core`
- otherwise fallback proxy based on `panel_id` token0.token1

This is important because common-cause rows should be reviewed as shared context, not as many separate outbound panel cases.

### Singleton Internal Review

`actionability_v3 == singleton_review`

These rows go to:

- `_share/critical_internal_review_v4.csv`

Additional routing field:

- `internal_review_priority`

Priority rule:

- `high` if `vendor_reply_class` is `vendor_rejected` or `vendor_pattern_positive`
- `medium` otherwise

### Monitor Archive

`actionability_v3 == monitor_only`

These rows go to:

- `_share/critical_monitor_archive_v4.csv`

This keeps them visible without sending them to outbound or internal singleton review.

## Why V4 Is Routing, Not Model Tuning

V4 does not change:

- candidate generation
- phenotype rules
- thresholds

It only changes how already-classified rows are organized for operations.

That makes the patch low-risk.

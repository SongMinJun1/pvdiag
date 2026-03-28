# OPS Critical Case Packets V5

## Purpose

V5 is a packaging layer, not a new model layer.

It turns current routing outputs into shareable or reviewable case packets for:

- outbound review
- common-cause cluster review
- internal singleton review

## Scope Guard

This patch does not change:

- `pv_ae/panel_day_engine.py`
- weather, event, frame, episode generation logic
- vendor adjudication builder
- `critical_actionability_shadow_v3` outputs
- `critical_case_router_v4` outputs
- canonical truth template contract

It only packages current routed rows and adds two sanity flags.

## Why V5 Exists

V4 already answered the routing question.

V5 answers the packaging question:

- what should be shared outward
- what should stay at cluster-review level
- what should stay internal

## Sanity Flags

### `cluster_leakage_flag`

Applied to outbound candidates.

Set to `1` when an outbound row appears to overlap with a common-cause cluster on:

- same `site`
- same `anchor_date`
- same recoverable group proxy family

This is a safety diagnostic only.

It does not automatically remove the outbound row.

Purpose:

- prevent over-trusting outbound routing when there is nearby common-cause context

### `vendor_positive_hold_flag`

Applied to internal singleton review rows.

Set to `1` when:

- vendor feedback is positive or likely positive
- the row is still in internal review rather than outbound

This is another safety diagnostic.

Purpose:

- surface cases where operational routing may be too conservative

## Packet Semantics

### Outbound Pack

Panel-level shareable review packet for current outbound maintenance candidates.

### Cluster Pack

One row per common-cause cluster.

These should not be sent panel-by-panel.

They are meant for grouped review of same-date, same-group common-cause context.

### Internal Review Pack

Panel-level internal review packet for singleton review cases.

### Summary

High-level count table for:

- outbound
- outbound leakage flags
- clusters
- internal rows
- internal vendor-positive holds
- monitor rows

## Recommended Check Items

The packet adds simple operational check text only.

This is not new model logic.

It is a packaging convenience layer for review workflows.

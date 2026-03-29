# OPS_COMMON_CAUSE_INCIDENT_REGISTRY_V1

## Purpose

This patch materializes `common_cause_incident_registry_v1` from `panel_day_evidence_matrix_v1` as the first executable human-facing anomaly-registry layer.

It does not change:

- official prediction output,
- official scoring logic,
- canonical truth,
- or raw strict-row generation.

It only groups panel-day evidence into site-level common-cause incidents using evidence aggregation.

## Why Incident Registry Is Implemented Before Panel-Local Episode Registry

The current common-cause question is already visible in grouped panel-day evidence:

- multiple panels in the same group collapse together,
- multiple groups collapse on the same site/day,
- and those grouped patterns can persist across consecutive days.

That makes the incident layer a good first human-facing registry layer because it can be built directly from evidence without needing panel-local episode semantics first.

## Why Event/Episode Layers Are Not Used As Primary Incident Generators

Existing event or episode layers may still be useful later as context.

But they are not used here as primary incident generators because this v1 registry is meant to answer:

- what grouped common-cause evidence is present in the evidence matrix itself,
- and how it persists across site-days.

Using prior event/episode layers as the primary generator would mix two different abstractions too early.

## How Candidate Days Are Formed From Grouped Zero-Like Evidence

For each `site + date + group_proxy_value`, the builder counts:

- panels that are `zero_like`
- panels that are `group_like_zero_like`

where `group_like_zero_like` means:

- `coverage_ok_flag == 1`
- `mid_ratio <= 0.10`
- `mid_i_ratio <= 0.10`
- `mid_v_ratio >= 1.05`

Those grouped counts are then rolled up to the site/day level.

A site/day becomes an incident candidate when it has either:

- enough qualifying groups,
- or enough total affected panels with sufficient site-affected share.

## How Day-To-Day Group Overlap Controls Incident Merging

Candidate days do not automatically belong to the same incident just because they are consecutive.

Within each site, two consecutive candidate days merge only when their qualifying-group overlap share is high enough.

In v1, that overlap share is computed from the adjacent days' qualifying-group sets, and the merge threshold stays fixed at `0.50`.

If the overlap falls below that threshold, the builder starts a new incident.

## Why This Is A Human-Facing Incident Layer, Not A Replacement For Raw Strict Rows

Raw strict rows still matter as fine-grained anchors.

But they are too low-level for most common-cause review.

This registry is therefore a human-facing incident layer:

- it summarizes multi-panel evidence,
- it groups candidate days into incidents,
- and it exposes review-friendly fields like scope, confidence, and recommended action.

It does not replace raw strict rows or claim to be the only canonical unit.

## Outputs

- `_share/common_cause_incident_registry_v1.csv`
- `_share/common_cause_incident_days_v1.csv`
- `_share/common_cause_incident_summary_v1.csv`

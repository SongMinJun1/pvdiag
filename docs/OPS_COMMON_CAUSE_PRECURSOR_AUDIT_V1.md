# OPS_COMMON_CAUSE_PRECURSOR_AUDIT_V1

## Purpose

The maintenance-proxy line no longer looks like panel-level maintenance promotion. After the cluster and timing audits, it looks more like a broad same-group/site-day collapse signal that can lead a medium-or-higher alert episode by about 2 days.

That is encouraging, but one-site evidence is not enough for official adoption.

This audit asks the next required question:

- does the same precursor pattern appear across the full site-day history,
- and does it meaningfully lead medium-or-higher alert episodes across sites?

This stage is audit-only. It does not modify any official output.

## Why One-Site Evidence Is Not Enough

The conalog slice can show that a signal is possible. It cannot show that the signal generalizes.

For official use, we need to know whether the same pattern:

- appears elsewhere,
- leads target episodes often enough to matter,
- and does so without exploding into too many low-value candidate days.

## Full Site-Day Universe

The builder scans every available `site + date` row derivable from:

- `data/<site>/out/panel_day_core.csv`

for:

- `conalog`
- `gangui`
- `ktc_ess`
- `sinhyo`

This avoids cherry-picking from the earlier maintenance-shadow slice.

## Precursor Features

The audit uses only `panel_day_core` fields.

Panel-day precursor flags:

- `zero_like_flag`
  - `mid_ratio <= 0.10`
  - `mid_i_ratio <= 0.10`
  - `coverage_mid >= 0.50`

- `group_like_zero_like_flag`
  - `zero_like_flag == 1`
  - `mid_v_ratio >= 1.05`

Site-day aggregation then counts:

- how many panels are zero-like,
- how many are group-like zero-like,
- how many fallback groups contain at least 2 such panels,
- how large the biggest qualifying group is,
- and how much of the site-day is covered by those qualifying groups.

## Fixed Audit Tiers

The audit does not tune thresholds from truth.

Fixed tiers:

1. `broad_3g_10p`
   - at least 3 qualifying groups
   - at least 10 total panels in qualifying groups

2. `medium_2g_5p`
   - at least 2 qualifying groups
   - at least 5 total panels in qualifying groups

3. `narrow_1g_3p`
   - at least 1 qualifying group
   - largest qualifying group size at least 3

These are fixed audit slices only.

## Timing Interpretation

Each candidate day is matched to the best same-site target episode, preferring:

- `trigger_mode == medium_or_higher`

when that trigger mode exists.

Candidate timing classes:

- `exact_same_day_episode`
- `in_episode_window`
- `lead_1_to_3_days`
- `lead_4_to_7_days`
- `no_episode_within_7d`

## How To Read Tier Precision vs Episode Recall

### Precision

Precision answers:

- if a tier fires, how often is it near a target episode?

Important columns:

- `lead_1_to_3_precision`
- `lead_1_to_7_precision`
- `exact_or_lead_1_to_3_precision`

Higher precision means fewer wasted candidate days.

### Episode Recall

Recall answers:

- how many target episodes are preceded by at least one `lead_1_to_3_days` candidate?

Important column:

- `episode_lead_1_to_3_recall`

Higher recall means broader coverage of real episode starts.

We need both. High precision with near-zero recall is not enough. High recall with massive low-value firing is not enough either.

## What Would Justify An Early-Warning Addon

Evidence in favor:

- `broad_3g_10p` or `medium_2g_5p` shows meaningful `lead_1_to_3_precision`
- target-episode recall is non-trivial
- the signal appears across more than one site
- exact same-day firing does not dominate

That would support further work on a common-cause precursor addon.

## What Would Close The Line As Non-Generalizing

Evidence against further use:

- candidate-day counts are high but `lead_1_to_3_precision` is weak
- almost all hits are exact same-day or in-window rather than leading
- `episode_lead_1_to_3_recall` stays very low
- useful behavior appears only in one site slice

That would argue that the signal does not generalize well enough for official adoption.

## Outputs

- `_share/common_cause_precursor_audit_summary_v1.csv`
- `_share/common_cause_precursor_candidate_days_v1.csv`
- `_share/common_cause_precursor_episode_matches_v1.csv`

# OPS_COMMON_CAUSE_PRECURSOR_CASE_FORENSICS_V1

## Purpose

`common_cause_precursor_audit_v1` showed a promising pattern in `conalog`, but it still was not enough to justify any addon.

That earlier audit told us:

- which site-days matched fixed precursor tiers,
- how often those site-days led medium-or-higher episodes,
- and that the encouraging behavior was concentrated in one narrow slice.

It did not explain whether the candidate days themselves looked like:

- short, plausible precursor runs that sit just ahead of an episode,
- or persistent site-specific collapse patterns that happen to satisfy the tier thresholds.

This audit fills that gap with case-by-case forensics. It stays audit-only and does not change any official output.

## Why Precursor Audit V1 Was Not Enough

`precursor_audit_v1` was a population-level screen.

That is useful for deciding whether the line is worth deeper inspection, but it is not enough for adoption because it cannot distinguish:

- a brief lead-up sequence that looks operationally meaningful,
- from a recurring site pattern that is probably not a transferable warning signal.

The current real-data question is exactly that split:

- `conalog 2024-12-06~09` looks like a plausible short precursor sequence,
- while `ktc_ess 2025-10-25~28` looks more like a non-generalizing site pattern.

## Why Case-By-Case Forensics Is The Right Next Step

At this stage we do not need a new rule. We need an explanation.

The builder recomputes each candidate day from `panel_day_core` and adds three kinds of diagnostics:

1. Same-day aggregate severity
   - panel counts
   - zero-like counts
   - qualifying same-group collapse counts
   - share of the site-day covered by qualifying groups

2. Local baseline comparison
   - a `±7` calendar-day window around the candidate day
   - local medians excluding the candidate day itself
   - ratios against that local baseline

3. Candidate-run structure
   - run length
   - run start/end
   - position of the day inside the run

Together those diagnostics let us separate brief precursor-like runs from persistent or sparse patterns.

## Forensic Hypotheses

Each unique candidate `site + date` is classified into one fixed label:

1. `plausible_precursor_day`
2. `episode_aligned_day`
3. `likely_persistent_site_pattern`
4. `likely_sparse_site_pattern`
5. `ambiguous_case`

### Plausible Precursor Day

`plausible_precursor_day` is intentionally narrow.

It requires:

- `lead_1_to_3_days` timing,
- qualifying-group panel share of at least `0.10`,
- run length no more than `4`,
- and a site-day panel count that is broadly stable versus the local median, or no usable local baseline denominator.

This is meant to capture a short, operationally plausible build-up rather than a drifting site mode.

### Episode Aligned Day

`episode_aligned_day` covers:

- `exact_same_day_episode`
- `in_episode_window`

These are useful context days, but they are not precursor evidence anymore because the episode has already started.

### Likely Persistent Site Pattern

`likely_persistent_site_pattern` requires:

- `no_episode_within_7d`
- and a candidate run length of at least `2`

This is the key bucket for slices like `ktc_ess 2025-10-25~28`. The signal is repeating, but not near a target episode. That makes it look more like a site-specific operating mode, persistent collapse state, or coverage artifact than a transferable early-warning pattern.

### Likely Sparse Site Pattern

`likely_sparse_site_pattern` catches days where:

- `qualifying_group_panel_share < 0.05`
- or `max_group_cluster_size < 3`

These are too thin to support a robust common-cause precursor interpretation.

## How To Use This Audit

This audit is for decision support, not rule generation.

Recommended use:

- keep the line open only if the plausible bucket is concentrated in a small number of believable lead days,
- close the line if non-episode persistent or sparse patterns dominate,
- or keep a site-specific note if the behavior looks real in one site but does not generalize.

## What Would Support Keeping The Line Open

Evidence in favor:

- most `lead_1_to_3_days` candidates fall into `plausible_precursor_day`
- episode-adjacent days behave like short runs rather than long drifting sequences
- non-episode days do not accumulate in the persistent-pattern bucket

That would support further site-specific or cross-site follow-up.

## What Would Support Closing The Line

Evidence against the line:

- `likely_persistent_site_pattern` dominates outside the episode-aligned slice
- candidate days recur in long or repeated runs without nearby episodes
- sparse low-share days make up a meaningful fraction of the candidate universe

That would argue the line is better treated as site-specific background behavior, not a precursor addon.

## Outputs

- `_share/common_cause_precursor_case_forensics_summary_v1.csv`
- `_share/common_cause_precursor_case_forensics_days_v1.csv`
- `_share/common_cause_precursor_case_forensics_groups_v1.csv`

# OPS_COMMON_CAUSE_PRECURSOR_DECISION_PACK_V1

## Purpose

This decision pack closes the current precursor audit line into a final go/no-go artifact.

It answers three operational questions:

1. Should we adopt a global common-cause early-warning addon now?
2. Should we keep a site-specific precursor note for `conalog`?
3. Should `ktc_ess` be interpreted as persistent or sparse site-pattern behavior instead of precursor behavior?

This stage is decision-only. It does not modify any official prediction, routing, or actionability output.

## Why The Line Moved From Maintenance To Common-Cause Precursor

The original maintenance-shadow path looked numerically promising, but the later audits changed the interpretation:

- the same-group maintenance proxy expanded too broadly,
- cluster audit showed it looked more like same-day common-cause structure than panel-level maintenance,
- timing audit showed the strongest real slice behaved like a `+2 day` lead before a medium-or-higher episode,
- and full-history precursor audit showed that this behavior did not generalize cleanly across sites.

At that point the right output was no longer another maintenance rule. It was a decision artifact.

## Decision Basis

The decision pack uses:

- `common_cause_precursor_audit_v1`
  - primary global generalization tier: `broad_3g_10p`
- `common_cause_precursor_case_forensics_v1`
  - site/day interpretation
- `maintenance_proxy_event_timing_clusters_v2`
  - timing context only

The fixed decision thresholds are intentionally conservative.

## Why Global Adoption Is Not Justified Yet

Global adoption requires all of the following:

- `broad_3g_10p lead_1_to_3_precision >= 0.50`
- `broad_3g_10p episode_lead_1_to_3_recall >= 0.20`
- plausible precursor evidence spanning at least `2` sites

Current real data does not meet that bar.

What we have instead is:

- a promising narrow slice in `conalog`
- but weak cross-site generalization
- and a second site slice that looks more like persistent or sparse site-pattern behavior

That supports observation, not adoption.

## Why Conalog May Still Deserve A Site-Specific Precursor Note

`conalog` is the cleanest remaining positive slice because it has:

- at least `2` plausible precursor days
- at least `1` episode-aligned day
- and no persistent-pattern days in the forensic split

That combination does not justify a global addon, but it is enough to keep a site-specific note that this site has shown a short precursor-like sequence ahead of an episode.

## Why KTC_ESS Should Be Treated As Site-Pattern / Artifact Candidate For Now

`ktc_ess` does not show plausible precursor days in the forensic output.

Instead it shows:

- persistent-pattern days
- sparse-pattern days
- and no clean plausible precursor slice

That is the wrong shape for an early-warning adoption path. For now it is more defensible to interpret this site as a site-pattern or coverage-artifact candidate rather than a precursor signal.

## How To Read The Outputs

### Summary

`common_cause_precursor_decision_summary_v1.csv` is the single global recommendation row.

Allowed global decisions:

- `do_not_adopt_global_addon_yet`
- `keep_under_observation`
- `consider_shadow_addon_next`

### Sites

`common_cause_precursor_decision_sites_v1.csv` gives the site-level interpretation.

Allowed site recommendations:

- `keep_site_specific_precursor_note`
- `likely_site_pattern_not_generalizable`
- `no_precursor_signal`
- `ambiguous_site_signal`

### Cases

`common_cause_precursor_decision_cases_v1.csv` maps each candidate day to the site recommendation and flags whether it should be included in a site-specific note.

## What Evidence Would Reopen This Line Later

The line should only be reopened for official adoption if a later rerun shows:

- `broad_3g_10p` precision at or above `0.50`
- recall at or above `0.20`
- plausible precursor days across at least `2` sites
- and less dependence on one narrow site slice

If that happens, the next step would be a shadow-only addon evaluation.

If not, the correct posture is:

- keep the `conalog` note if it remains stable,
- keep `ktc_ess` under site-pattern interpretation,
- and do not promote the line into the official pipeline.

## Outputs

- `_share/common_cause_precursor_decision_summary_v1.csv`
- `_share/common_cause_precursor_decision_sites_v1.csv`
- `_share/common_cause_precursor_decision_cases_v1.csv`

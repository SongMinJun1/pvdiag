# OPS PANEL DAY ENGINE RUN RANKER COMPLEMENT AUDIT V1

## Why V3 Was Not Enough As A Primary Scorer
- `logistic_v3_intersection_holdout` improved over the earlier v2 logistic baseline.
- It still did not beat `electrical_core_minus_broadshape_050` as the main run scorer.
- That means the next question is not "can we force learned to replace deterministic right now?" but:
  - does learned ranking still add useful secondary discovery value?

## Why Complementarity Is The Right Next Question
- Primary scoring and secondary discovery are different jobs.
- The deterministic reference is currently strongest at stable top-k retrieval.
- A learned scorer can still be useful if it surfaces extra positive-like runs that the reference leaves out,
  while not adding too many extra negative-like runs.

## What This Audit Measures
- Recreate the same v3 label universe from `run_label_pack_v3_intersection.csv`
- Recreate the same holdout folds:
  - leave-one-site-out
  - time_holdout_70_30
- Compare top-20 sets from:
  - `reference_only = electrical_core_minus_broadshape_050`
  - `logistic_v3_intersection_holdout`

## How To Read Incremental Positive And Negative Counts
- `positive_logistic_only_count`
  - positive-like runs that appear only in learned top-20
- `negative_logistic_only_count`
  - negative-like runs that appear only in learned top-20
- `logistic_incremental_positive_minus_negative`
  - `positive_logistic_only_count - negative_logistic_only_count`
- Interpretation:
  - positive value means learned ranking adds net discovery signal beyond the deterministic reference
  - zero or negative value means learned ranking is not adding enough clean extra value

## Disagreement Classes
- `positive_logistic_only`
  - learned top-20 finds a positive-like run that reference top-20 misses
- `positive_reference_only`
  - deterministic reference keeps a positive-like run that learned top-20 misses
- `negative_logistic_only`
  - learned top-20 adds contamination not present in reference top-20
- `negative_reference_only`
  - deterministic reference adds contamination that learned top-20 does not

## Operational Meaning Of The Two Recommendations
- `use_logistic_as_secondary_discovery_lane`
  - keep deterministic reference as primary scorer
  - keep learned v3 only as a secondary panel for extra review candidates
- `stop_learned_scorer_for_now`
  - do not keep a separate learned lane
  - freeze scorer search until stronger labels or a clearer modeling gain appears

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.

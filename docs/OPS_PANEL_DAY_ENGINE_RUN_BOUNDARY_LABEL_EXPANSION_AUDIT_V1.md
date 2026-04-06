# OPS PANEL DAY ENGINE RUN BOUNDARY LABEL EXPANSION AUDIT V1

## Why This Patch Exists
- `run_label_expansion_audit_v1` was useful for broad scouting, but score-only expansion stayed too loose for the next scorer iteration.
- The deterministic reference gap audit already exposed two high-value boundary regions:
  - missed positive-like runs that the current reference almost catches
  - hard negative-like runs that the current reference still promotes too high
- This patch turns those boundary patterns into a narrower label-expansion queue, without changing detector logic.

## Core Idea
- Build a `positive_boundary_prototype_pool` from reference-gap cases in:
  - `positive_top50_global_not_top20`
  - `positive_below_top50_global`
- Build a `hard_negative_prototype_pool` from:
  - `negative_top20_global`
- Measure each currently excluded run against both prototype pools in a shared robust-scaled feature space.
- Use the distance margin:
  - `boundary_margin = hard_negative_distance - positive_boundary_distance`
- Interpret the margin as:
  - positive margin: closer to missed-positive boundary than hard-negative boundary
  - non-positive margin: closer to hard-negative boundary or not clearly positive-like

## Why Boundary-Based Selection Is The Next Step
- Broad expansion pulled many high-score runs, but many of them were still heterogeneous and hard to adjudicate.
- Boundary-based selection is narrower because it asks a stricter question:
  - is this excluded run shaped more like known missed positives, or more like known hard negatives?
- This keeps the next review batch closer to the actual ranking failure surface instead of simply chasing score tails.

## Why Missed Positives And Hard Negatives Are Both Needed
- Missed-positive prototypes define where the current scorer under-retrieves fault-like runs.
- Hard-negative prototypes define where aggressive promotion risks contaminating the positive pool.
- Using both simultaneously prevents “high score == promote” from becoming the only rule.

## Candidate Classes
- `positive_promotion_candidate`
  - excluded run
  - not `monitor_like` or `common_cause_like`
  - positive boundary margin is favorable
  - and score rank is still operationally meaningful
- `hard_negative_review_candidate`
  - excluded run
  - closer to hard-negative boundary
  - but still globally high-scoring enough to matter
- `monitor_or_common_cause_holdout`
  - `monitor_like` or `common_cause_like`
  - retained as holdout review tracks, not positive promotion targets
- `low_priority_unlabeled`
  - everything else

## Priority Bands
- `P1`
  - positive promotion candidate from a site with zero current positive training labels
- `P2`
  - positive promotion candidate whose positive boundary margin is in the upper half of the positive candidate set
- `P3`
  - hard negative review candidate
- `P4`
  - holdout or low-priority rows

## What Would Justify A Narrow V3 Label Update
- `P1` and `P2` rows form a small, interpretable batch rather than another broad score tail.
- The batch is clearly separated from hard-negative boundary candidates by positive margin.
- Site-positive gaps are reduced using a handful of boundary-aligned additions rather than large weak-label promotion.

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.
- `monitor_like` and `common_cause_like` rows remain explicit holdouts, not positive promotion targets in this step.

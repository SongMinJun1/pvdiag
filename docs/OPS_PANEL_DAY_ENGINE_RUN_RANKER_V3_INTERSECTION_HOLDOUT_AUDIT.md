# OPS PANEL DAY ENGINE RUN RANKER V3 INTERSECTION HOLDOUT AUDIT

## Why This Patch Exists
- Raw boundary-distance expansion was rejected because it stayed too broad even after hygiene checks.
- Clipped boundary variants also did not narrow the candidate set enough to justify using them directly as weak labels.
- The hygiene audit therefore recommended the stable fallback:
  - `use_boundary_intersection_with_review_batch`

## Why Boundary ∩ Review Batch Was Chosen
- The boundary method contributes prototype awareness:
  - runs closer to missed-positive boundary than to hard-negative boundary
- The review batch contributes operational curation:
  - already filtered to small, high-value positive review runs
- Their intersection is the narrowest strategy that still keeps some prototype-grounded signal.

## What This Audit Tests
- Start from `run_label_pack_v2`
- Promote only the intersection runs to weak positives
- Build `run_label_pack_v3_intersection`
- Re-run holdout with:
  - `logistic_v3_intersection_holdout`
  - `electrical_core_score`
  - `electrical_core_minus_broadshape_050`

## Why This Is The Next Narrow V3 Test
- It is smaller and more stable than raw boundary promotion.
- It is still more informative than doing nothing, because it adds a curated set of new positive examples.
- It answers the key practical question:
  - does the narrow, hygiene-approved promotion set actually beat the existing v2 logistic and close the gap to the deterministic reference?

## What Would Justify Moving To Run Ranker V3 Proper
- `logistic_v3_intersection_holdout` improves top-k positive-minus-negative over `logistic_v2_holdout`
- and does not lose clearly to `electrical_core_minus_broadshape_050`
- and the gain appears in both LOSO and time holdout, not only in one split

## What Would Justify Freezing Scorer Search At Deterministic Reference
- The intersection-v3 scorer still fails to beat `electrical_core_minus_broadshape_050`
- or only matches it in narrow folds without consistent improvement
- or the new weak positives change label count but not retrieval quality

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.

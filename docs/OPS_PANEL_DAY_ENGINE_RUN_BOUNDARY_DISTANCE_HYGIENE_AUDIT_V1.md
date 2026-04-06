# OPS PANEL DAY ENGINE RUN BOUNDARY DISTANCE HYGIENE AUDIT V1

## Why This Patch Exists
- `run_boundary_label_expansion_audit_v1` proved that a pure boundary-distance expansion can become too broad even when it is prototype-grounded.
- The raw result was already a warning sign:
  - many positive-promotion candidates
  - no meaningful hard-negative review slice
- Before any `run_ranker_v3` step, we need to decide whether this boundary method is salvageable after clipping and hygiene, or whether we should fall back to the narrower curated review batch.

## Why Raw Boundary Was Judged Too Broad
- The raw method used a clean idea:
  - compare excluded runs against missed-positive boundary prototypes
  - compare them against hard-negative boundary prototypes
  - keep runs with positive margin
- But the result can still become operationally loose if:
  - extreme feature values dominate the distance space
  - upper-tail score runs are promoted too easily
  - the hard-negative pool is too small to carve out a meaningful rejection frontier

## Why Outlier And Clipping Diagnosis Is Required Before V3
- If the boundary space is being distorted by a few extreme runs, then a v3 scorer built on those promoted labels would inherit unstable supervision.
- This patch therefore checks:
  - suspicious raw candidates
  - global p99 upper clipping
  - site-aware p99 upper clipping
  - whether either clipped variant materially narrows the candidate pool

## Mode Definitions
- `raw_boundary`
  - the current raw boundary-distance method reconstructed from the same feature set
- `clipped_global_boundary`
  - same method, but all distance inputs upper-clipped at global p99 before robust scaling
- `clipped_site_boundary`
  - same method, but site p99 upper clipping is used when the site has enough rows; otherwise global clipping is used
- `boundary_intersection_with_review_batch`
  - only keep raw positive-promotion candidates that also appear in the existing `positive_review_batch`

## Why Intersection With Review Batch Is A Valid Fallback
- The review batch is already a narrower, curated shortlist built from score/rank/operator context.
- If the raw or clipped boundary method remains too broad, their intersection with the review batch gives a conservative hybrid:
  - prototype-aware
  - but still operationally curated

## Recommended Strategy Meanings
- `use_clipped_global_boundary`
  - the global p99 clipped boundary method is narrow and stable enough to use as the next label-expansion source
- `use_clipped_site_boundary`
  - site-wise upper-tail clipping stabilizes the boundary method better than the global version
- `use_boundary_intersection_with_review_batch`
  - boundary method alone is still too broad, but its overlap with the curated review batch is narrow enough to keep
- `use_review_batch_only`
  - all boundary variants remain unstable, so we should ignore them and use only the curated review batch

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.
- Any site-conditioned clipping in this audit is only a method-hygiene search step, not a final claim about unbiased label quality.

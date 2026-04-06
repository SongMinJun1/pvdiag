# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY V1

## Why Learned Scoring Is Not Replacing The Baseline
- The current deterministic operator baseline remains the primary queue because it is still the strongest and most stable top-k retriever.
- The learned v3 scorer did not beat that baseline as a primary operator score.
- This patch therefore does not change the current operator baseline, digest, or attention pipeline.

## Why Learned Scoring Is Still Useful As A Secondary Discovery Lane
- Complement audit showed that learned v3 sometimes surfaces positive-like runs not already captured by the deterministic top-20.
- That means learned scoring can still add value as a separate discovery lane:
  - not as the default operator queue
  - but as an analyst-facing source of hidden candidates worth extra review

## Why Only `unlabeled_other` And Non-Attention Panels Are Included
- `unlabeled_other`
  - avoids reusing already labeled positive, negative, monitor, or common-cause runs
  - keeps this lane focused on discovery rather than relabeling known buckets
- non-attention panels only
  - avoids duplicating panels that already appear in `operator_attention_now`
  - keeps the file focused on hidden opportunities, not re-showing the same baseline attention

## What This Patch Builds
- Train the same online-safe logistic v3 model on:
  - `training_label_v3 in {positive, negative}`
- Score the full run universe
- Filter to hidden discovery candidates:
  - `training_label_v3 == exclude`
  - `label_bucket_v3 == unlabeled_other`
  - `(site, panel_id)` not already present in `operator_attention_now`
- Emit a narrow operator-facing discovery lane:
  - top 5 per site
  - plus top 20 overall
  - deduplicated by run key

## How Operators And Analysts Should Read The Discovery File
- This file is not the baseline operator queue.
- It is a separate learned-score lane for secondary review.
- Higher rows mean:
  - the learned v3 model sees stronger positive-like structure
  - on a panel that the current operator baseline is not already surfacing
- Analysts should treat these runs as:
  - candidate discovery leads
  - useful for label expansion, side review, or manual pattern inspection
  - not as automatic replacements for the current deterministic queue

## Scope Notes
- This is a non-core operator-facing patch.
- Detector logic is unchanged.
- Current operator baseline files and pipeline scripts remain unchanged.
- Canonical truth template contract is unchanged.

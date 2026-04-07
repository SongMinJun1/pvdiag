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
- The lane was therefore retained separately instead of being merged into the baseline queue.

## Why A Value Vs Monitor Split Is Now Justified
- Follow-up threshold-split audit showed that the retained secondary lane does not need to stay fully undifferentiated.
- A simple current-state split rule can separate:
  - stronger hidden-value candidates
  - from monitor-burden or noisier candidates
- This patch applies that split only inside the secondary discovery lane and keeps the main operator baseline unchanged.

## Why The Value Lane Still Needed A Panel-Level Rollup
- The value lane remained promising after the split, but it was still too wide at run level because the same hidden panel could appear multiple times through repeated runs.
- That makes the lane less operator-friendly:
  - repeated hidden runs from one panel can occupy multiple top-level rows
  - while the operational question is often panel-level follow-up first
- This patch therefore keeps the run-level files, but adds a separate panel-level value rollup for operator use.

## Why The Selected Split Rule Is Currently Deterministic / Electrical
- The completed threshold-split audit selected a deterministic electrical rule as the best simple splitter.
- That outcome means the learned scorer is still useful for discovering the hidden candidate pool, but the strongest current operational split inside that pool is driven by electrical severity.
- In other words:
  - learned scoring finds the lane
  - deterministic/electrical severity currently splits the lane more cleanly into value vs monitor candidates
- The new panel rollup follows the same principle:
  - keep the learned lane discovery logic
  - but present the value side in a tighter, operationally simpler panel-first view

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
- Read the completed threshold split recommendation and partition the discovery lane into:
  - `value_candidate_lane`
  - `monitor_candidate_lane`
- Emit:
  - the original discovery file with added split columns
  - a value-lane file
  - a monitor-lane file
  - a panel-level value rollup file
  - a panel-level value summary file

## How Representative Value Runs Are Chosen
- Value panel rollup is built only from the existing `value_candidate_lane` rows.
- Runs are collapsed by:
  - `site`
  - `panel_id`
- The representative run is chosen by this priority:
  - highest `electrical_core_minus_broadshape_050`
  - then highest `logistic_v3_discovery_score`
  - then latest `run_end_date`
  - then larger `run_day_count`
  - then earliest `run_start_date`
- This keeps the strongest and most recent electrical value signal visible, while still preserving how many hidden value runs were seen for that panel.

## How Operators And Analysts Should Read The Discovery File
- This file is not the baseline operator queue.
- It is a separate learned-score lane for secondary review.
- Higher rows mean:
  - the learned v3 model sees stronger positive-like structure
  - on a panel that the current operator baseline is not already surfacing
- The new split columns should be interpreted as:
  - `value_candidate_lane`
    - stronger current hidden-value candidate inside the learned discovery lane
  - `monitor_candidate_lane`
    - still potentially useful, but more consistent with monitor burden or weaker/noisier review priority
- The new value-panel rollup should be interpreted as:
  - one operator-facing row per hidden value panel
  - with repeated value runs collapsed underneath that representative row
  - while `future_*` linkage fields remain retrospective reference only and are not used to create the split or the rollup itself
- Analysts should treat these runs as:
  - candidate discovery leads
  - useful for label expansion, side review, or manual pattern inspection
  - not as automatic replacements for the current deterministic queue

## Scope Notes
- This is a non-core operator-facing patch.
- Detector logic is unchanged.
- Current operator baseline files and pipeline scripts remain unchanged.
- The main operator baseline is not re-ranked, replaced, or expanded by this patch.
- Canonical truth template contract is unchanged.
- `future_*` linkage fields in summaries or panel rollups are retrospective reference only:
  - they help validate whether the lane is finding hidden value
  - but they are not used in the current-state split or representative-run selection

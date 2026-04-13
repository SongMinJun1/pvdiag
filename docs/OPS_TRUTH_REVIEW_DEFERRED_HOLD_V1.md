# OPS_TRUTH_REVIEW_DEFERRED_HOLD_V1

## Purpose

This patch formalizes a deferred-hold registry for currently excluded high-actionability rows and produces a clean active review queue.

It does not change:

- official scoring,
- canonical truth,
- or any prediction output.

It only changes packaging around the review workflow.

## Why This Exists

We already made the scoring boundary explicit in the score-scope manifest.

That showed two important facts at the same time:

- some scored rows still exist on the affected site,
- and some unresolved high-actionability rows are intentionally deferred.

Without a hold registry, those same unresolved rows can keep reappearing in the active review queue even though the current governance decision is to wait for better field evidence.

This patch makes that hold decision operational.

## Deferred-Hold Universe

The deferred-hold registry is selected from:

- `score_scope_manifest_cases_v1.csv`
- `score_scope_manifest_sites_v1.csv`

Selection rule:

1. `scope_class == deferred_unlabeled_high_actionability`
2. the row's site has `recommended_site_handling == score_with_deferred_note`

This is deliberate.

The logic is not keyed to a site name.
It is keyed to the governance state already expressed by the score-scope manifest.

## What The Hold Registry Means

Each hold row receives fixed governance fields:

- `hold_reason = deferred_high_actionability_without_field_evidence`
- `hold_status = on_hold`
- `reactivation_condition = field_or_OM_evidence_available`

Interpretation:

- the row is unresolved,
- the row is still operationally notable,
- but current evidence is not strong enough to justify active review pressure right now.

## Why Deferred-Hold Rows Stay Excluded From Official Scoring

These rows are already excluded from official scoring before this patch.

That is the key governance point.

This patch does not move them into score and does not move them closer to canonical truth.
It only records that they should stay on hold until stronger evidence arrives.

## Why This Patch Does Not Change Score

The score boundary remains whatever `score_scope_manifest_v1` already says.

This patch reads that boundary.
It does not rewrite it.

So:

- no official F1 logic changes,
- no truth precedence changes,
- no truth labels are synthesized,
- and no canonical truth file is touched.

## Why The Active Review Queue Should Exclude Hold Rows

The active queue should represent work that is actionable now.

If a row is already governed as "defer until field or O&M evidence arrives," repeatedly surfacing it in the active queue creates churn rather than progress.

That is why `truth_review_active_batch_v2.csv` is built by taking `truth_review_batch_v1.csv` and removing only the exact deferred-hold keys.

Everything else stays in the same order and keeps the same columns.

## Why The Entire Site Must Not Be Dropped

The affected site may still contain validly scored rows.

Dropping the whole site would erase legitimate scored evidence and distort the benchmark more than the unresolved hold rows do.

So the correct governance action is:

- keep scored rows in score,
- keep deferred rows in an explicit hold registry,
- and remove only those hold rows from the active review queue.

That is why this patch separates:

- score inclusion,
- deferred hold,
- and active review packaging.

## How To Read The Outputs

### `truth_review_deferred_hold_v1.csv`

This is the registry of currently deferred high-actionability rows.

Use it as:

- the list of rows intentionally held back from active review,
- plus the fixed reason and reactivation condition.

### `truth_review_active_batch_v2.csv`

This is the clean reviewer worklist.

It preserves the original `truth_review_batch_v1.csv` schema and ordering, except that deferred-hold rows are removed.

### `truth_review_deferred_summary_v1.csv`

This summarizes:

- the original batch size,
- how many rows moved to hold,
- how many rows remain active,
- and which sites currently carry deferred-hold status.

## Outputs

- `_share/truth_review_deferred_hold_v1.csv`
- `_share/truth_review_active_batch_v2.csv`
- `_share/truth_review_deferred_summary_v1.csv`

# OPS Score Scope Manifest V1

## Purpose

This patch makes the current scoring scope explicit without changing any official prediction output or evaluation logic.

It answers three governance questions:

- which strict cases are currently scored by the existing `full_algorithm_f1_v3` truth rules,
- which rows are excluded because the current truth is explicitly unusable,
- and which remaining unlabeled rows, especially gangui high-actionability rows, are intentionally deferred instead of being force-labeled.

## Why This Manifest Exists

The current baseline is already usable, but the score boundary is easy to misunderstand if someone only looks at top-line F1.

In particular:

- some rows are scored because they already have manual truth,
- some rows would be scorable because vendor truth is usable,
- some rows are still unresolved and should stay outside the official score,
- and some of those unresolved rows are operationally interesting enough that they are already sitting in the review queue.

This manifest makes that boundary visible in one place.

## Base Universe

The base universe is `panel_date_reaudit_working.csv`.

One row in the manifest is one strict case:

- `site`
- `panel_id`
- `strict_trigger_date`

Nothing is added to or removed from that universe.

## Truth Availability Flags

Each case gets three flags:

- `manual_truth_present_flag`
- `vendor_truth_present_flag`
- `official_scored_flag`

Interpretation:

- `manual_truth_present_flag = 1` means `candidate_validity` is nonblank
- `vendor_truth_present_flag = 1` means `vendor_reply_class` is nonblank after the same coalescing used by the evaluator
- `official_scored_flag = 1` means the current hybrid truth logic would actually score the row

That last point matters.

A row can have manual truth present and still not be officially scored if the manual label is `needs_more_info`.
Likewise, a row can have vendor context present and still stay excluded if the vendor class is not currently usable truth.

## Scope Classes

The manifest assigns every strict case to one explicit scope class:

- `manual_scored`
- `vendor_scored`
- `deferred_unlabeled_high_actionability`
- `deferred_unlabeled_other`
- `excluded_labeled_needs_more_info`
- `excluded_vendor_no_info`
- `excluded_other`

This is not a new evaluation rule.
It is only an audit view over the current rule boundary.

## Why Unresolved Gangui High-Actionability Rows Are Already Excluded

The unresolved gangui rows in question do not currently have usable manual truth or usable vendor truth.

That means they are already outside the official scoring boundary today.

They may still look operationally important because `truth_coverage_priority_cases_v1.csv` places them in `high_actionability_unlabeled`, but that review priority does not make them scoreable truth.

So the right governance label is not "positive" or "negative".
It is "deferred until truth exists".

## Why Dropping The Entire Site Would Be A Mistake

A site can contain both:

- cases that are already validly scored, and
- cases that are still deferred

If we drop the whole site because some rows are deferred, we would throw away legitimate scored evidence and distort the current baseline more than the deferred rows do.

That is why the site manifest uses:

- `continue_scoring_normally`
- `score_with_deferred_note`
- `do_not_drop_site_only_defer_rows`

The goal is to keep valid scored rows in scope while making the unresolved remainder explicit.

## How To Read `official_scored_count` Versus Deferred Counts

`official_scored_count` tells you how many strict cases currently enter the official hybrid-truth scoring universe.

Deferred counts tell you how many cases are still outside that universe because they remain unlabeled.

Interpretation:

- high `official_scored_count` and zero deferred rows means the site is currently clean from a scope-governance perspective
- high `official_scored_count` and nonzero deferred high-actionability rows means keep scoring, but annotate that some important rows remain intentionally unresolved
- zero `official_scored_count` with deferred high-actionability rows means do not erase the site; the correct statement is that it is deferred, not absent

## Why This Supports Moving On Without Distorting The Baseline

This manifest lets us separate two activities:

- keeping the existing benchmark stable,
- and continuing manual review on unresolved rows

That helps because we do not need to choose between:

- pretending unresolved rows are solved,
- or pausing all progress until every deferred case is labeled

Instead we can:

- keep the current baseline exactly as-is,
- carry an explicit note about deferred scope,
- and move other work forward without silently changing what the score means.

## Current Review Queue Context

The cases output also includes `in_truth_review_batch_v1_flag`.

That flag is audit-only.
It shows whether a case already appears in the current truth review batch, which helps distinguish:

- rows that are deferred and already queued for review,
- from rows that are merely outside score scope without current batch assignment.

## Outputs

- `_share/score_scope_manifest_summary_v1.csv`
- `_share/score_scope_manifest_sites_v1.csv`
- `_share/score_scope_manifest_cases_v1.csv`

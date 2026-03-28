# OPS Maintenance Gap Audit V1

## Why This Exists

`full_algorithm_f1_v3` already makes the current scored subset operationally clean. The remaining gap is in the narrower maintenance definition: some positive strict cases are still routed to review instead of maintenance.

That does not automatically mean the current behavior is wrong. It means we need an audit layer that separates:

- clean review gaps that may deserve a later maintenance shadow promotion
- review cases that should stay review because they are primary singleton cases or confounded cases
- anything else that still needs rule review

This patch is intentionally audit-only. It does not change any current prediction, routing, or packet output.

## Why Maintenance Still Has FN Rows

The current algorithm keeps maintenance deliberately narrow. In `full_algorithm_f1_v3`, maintenance false negatives mostly come from two shapes:

- clean `confirmed_fault_flag` rows that currently fall back to `singleton_review`
- current primary `singleton_review` rows that were intentionally kept below maintenance

Operational is already clean on the currently scored subset, so the remaining question is not "is the current routing broken?" but "which review cases, if any, are clean enough to justify a future maintenance shadow?"

## Audit Universe

The audit only reads current maintenance false negatives from:

- `_share/full_algorithm_case_errors_v3.csv`

Filters:

- `prediction_mode == maintenance`
- `source_split == overall`
- `error_type == fn`

One audit row is one unique strict case:

- `site`
- `panel_id`
- `strict_trigger_date`

If the same strict case appears in both strict and lenient truth modes, the audit collapses it into one row and emits:

- `appears_in_strict`
- `appears_in_lenient`

## Joined Context

The audit joins context from current outputs only:

- `full_algorithm_case_errors_v3.csv`
- `critical_actionability_shadow_v3_latest.csv`
- `panel_onset_shadow_latest.csv`
- `vendor_reply_adjudication_latest.csv`

Vendor columns are context only. They are not direct decision rules.

## Gap Buckets

### `clean_confirmed_fault_review_gap`

All of the following must hold:

- `prediction_source == confirmed_fault_clean`
- `parsed_strict_method == confirmed_fault_flag`
- `parsed_shadow_frac == 0`
- `parsed_group_off_frac == 0`
- `parsed_recovery_reset == no`

This is the cleanest current maintenance gap bucket.

### `primary_singleton_review_gap`

All of the following must hold:

- `prediction_source == primary_actionability_v3`
- `final_actionability_v3 == singleton_review`

These are current primary review rows. They remain review by design.

### `confounded_review_gap`

Any of the following is enough:

- `prediction_source == confirmed_fault_confounded`
- `parsed_shadow_frac > 0`
- `parsed_group_off_frac > 0`
- `parsed_recovery_reset == yes`

These should stay review unless a later rule change is justified.

### `other_gap`

Anything that does not fit the buckets above.

## Promotion Hypothesis

This audit emits a hypothesis only. It does not change any actionability output.

- `candidate_for_maintenance_shadow`
  - only for `clean_confirmed_fault_review_gap`
- `keep_as_review`
  - for `primary_singleton_review_gap`
  - for `confounded_review_gap`
- `needs_rule_review`
  - for `other_gap`

## Why This Is A Definition Audit, Not A Bug Fix

The current maintenance definition is intentionally conservative. A maintenance false negative is not automatically a defect. Some are expected review cases.

That is why this patch does not write back into:

- `critical_actionability_shadow_v3`
- `critical_case_router_v4`
- `critical_case_packets_v5`
- `evaluate_full_algorithm_f1_v3`

The point is to quantify the gap before proposing any maintenance-promotion patch.

## Why Vendor Labels Are Context Only

Vendor reply columns are helpful for understanding whether the missed case later looked electrical, group-side, or none-visible. But they are not used here as direct promotion rules.

That keeps this audit upstream and definition-focused, instead of overfitting to sparse external labels.

## Outputs

- `_share/maintenance_gap_audit_cases_v1.csv`
- `_share/maintenance_gap_audit_summary_v1.csv`
- `_share/maintenance_gap_promotion_candidates_v1.csv`

## How To Read The Outputs

`maintenance_gap_audit_cases_v1.csv`

- one row per unique strict case in the current maintenance FN universe
- includes strict/lenient appearance flags
- shows gap bucket and promotion hypothesis

`maintenance_gap_promotion_candidates_v1.csv`

- only `candidate_for_maintenance_shadow`
- this is the clean shortlist for any future shadow maintenance rule discussion

`maintenance_gap_audit_summary_v1.csv`

- top summary row with counts
- repeated crosstab rows by `gap_bucket` and `vendor_fault_family`
- includes current operational F1 and effective coverage from `full_algorithm_f1_v3` for context

## Next Step

If the promotion-candidate set is small and structurally clean, the next patch can test a maintenance shadow promotion on those cases only. If the candidate set is mixed, the correct next step is a tighter rule review rather than a promotion patch.

# OPS Maintenance Shadow F1 V1

## Why This Exists

`maintenance_gap_audit_v1` tells us where current maintenance false negatives are coming from. The next question is not "should we change the upstream rule immediately?" but:

- how much maintenance F1 would improve under a conservative shadow promotion
- how much of that gain comes from strict-backed cases
- how much comes only from lenient-only cases

This patch answers that question without touching any official output.

## Shadow-Only, Not An Upstream Rule Change

This evaluator does not write back into:

- `critical_actionability_shadow_v3_latest.csv`
- routing outputs
- packet outputs

It creates evaluation-only shadow actionability:

- baseline official actionability stays unchanged
- promoted shadow rows get `maintenance_candidate_shadow`

For scoring only:

- maintenance positive = `maintenance_candidate` or `maintenance_candidate_shadow`

That keeps the exercise decision-safe. We can measure the upside before deciding whether any upstream promotion rule is justified.

## Why Maintenance Gap Audit Came First

The audit narrows the candidate set before any shadow scoring happens. Promotion source is restricted to:

- rows already present in `maintenance_gap_audit_cases_v1.csv`
- rows whose `promotion_hypothesis == candidate_for_maintenance_shadow`

No new promotion candidates are inferred outside the audit file.

## Truth Logic

This evaluator reuses the same hybrid truth basis as `full_algorithm_f1_v3`.

Truth precedence:

- manual truth if `candidate_validity` is nonblank
- otherwise vendor truth if `vendor_reply_class` is nonblank
- otherwise exclude

Manual truth:

- positive = `true_positive`, `group_side`
- negative = `false_positive`
- exclude = `needs_more_info`, blank

Vendor truth, strict:

- positive = `field_confirmed_positive`, `vendor_pattern_positive`
- negative = `vendor_rejected`
- exclude = `vendor_likely_positive`, `vendor_no_info`, blank

Vendor truth, lenient:

- positive = `field_confirmed_positive`, `vendor_pattern_positive`, `vendor_likely_positive`
- negative = `vendor_rejected`
- exclude = `vendor_no_info`, blank

Vendor labels still remain context only as decision rules. They only participate in scoring when manual truth is absent, exactly as in `full_algorithm_f1_v3`.

## Scenarios

### `baseline_v3`

No shadow promotion.

### `strict_backed_shadow`

Promote only audit candidates where:

- `promotion_hypothesis == candidate_for_maintenance_shadow`
- `appears_in_strict == 1`

This is the most conservative shadow scenario.

### `full_candidate_shadow`

Promote all audit candidates where:

- `promotion_hypothesis == candidate_for_maintenance_shadow`

This includes both:

- strict-backed candidates
- lenient-only candidates

## Why Strict-Backed vs Lenient-Only Matters

Strict-backed candidates already appear in the stricter scored subset, so promotion gains there are easier to defend.

Lenient-only candidates may still be useful, but they rely on weaker truth support. Separating them lets us answer two different questions:

- what is the gain if we stay maximally conservative?
- what is the additional gain if we also trust lenient-only audit candidates?

## How To Read Scenario Differences

If `strict_backed_shadow` gains most of the available F1 improvement, that suggests a narrow, defensible shadow rule may be enough.

If only `full_candidate_shadow` shows large gains, that means the upside depends on lenient-only rows and therefore deserves extra caution before any upstream change.

## Outputs

- `_share/maintenance_shadow_f1_summary_v1.csv`
- `_share/maintenance_shadow_case_changes_v1.csv`
- `_share/maintenance_shadow_promotion_sets_v1.csv`

`maintenance_shadow_f1_summary_v1.csv`

- one row per `scenario x truth_mode x source_split`
- includes confusion counts and F1
- includes how many promotions were active in that scenario

`maintenance_shadow_case_changes_v1.csv`

- one row per promoted case per scenario
- shows baseline vs shadow actionability
- marks promotion tier:
  - `strict_backed`
  - `lenient_only`

`maintenance_shadow_promotion_sets_v1.csv`

- all shadow-promotion candidates from the audit
- adds scenario membership flags

## What This Evaluator Is For

This is the right tool for the question:

"If we only promoted current maintenance-gap audit candidates in shadow mode, how much maintenance F1 would improve?"

It is intentionally not the right tool for:

- changing official actionability
- changing routing
- treating vendor fault families as direct promotion rules

Those decisions should only come after the shadow deltas are clear.

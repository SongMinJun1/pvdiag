# OPS Vendor Reply Adjudication

## Purpose

Vendor email feedback is useful supervision, but it is not gold truth by itself.

This patch turns mailed candidate replies into a structured audit layer so the next tuning step can use:

- confirmed positives
- softer vendor pattern feedback
- disagreements that need explicit review

without collapsing everything into hard labels.

## Inputs

Manual input file:

- `data/manual/vendor_reply_cases.csv`

Minimum schema:

- `site`
- `panel_id`
- `vendor_reply_class`
- `vendor_fault_family`
- `field_confirmed_flag`
- `adjudication_weight`
- `vendor_note`

Joined context:

- `_share/panel_onset_shadow_latest.csv`

## Evidence Tiers

Operationally, vendor reply evidence is tiered:

- `field_confirmed_positive`
  - strongest evidence
- `vendor_pattern_positive`
  - useful positive supervision, often closer to pattern/group issue than exact panel truth
- `vendor_likely_positive`
  - weaker positive evidence
- `vendor_rejected`
  - strong counter-evidence, but not definitive gold negative by default
- `vendor_no_info`
  - weak supervision only

## Why vendor_rejected Is Not Absolute Gold Negative

Many vendor rejects are not date-anchored adjudications.

That matters because our side may carry:

- strict trigger dates
- earlier retrospective onset dates
- panel-level evidence that predates the vendor's review window

So `vendor_rejected` is important, but without explicit date anchoring it should not be converted into unconditional hard negative truth.

## Output Files

- `vendor_reply_adjudication_latest.csv`
- `vendor_reply_confusion_summary.csv`
- `vendor_reply_disputes.csv`

## dispute_type Semantics

Current structured dispute labels:

- `agree_positive`
- `agree_group_issue`
- `ours_positive_vendor_rejected`
- `ours_positive_vendor_no_info`
- `vendor_positive_not_in_ours`
- `needs_date_anchor_review`

Interpretation:

- `agree_positive`
  - strongest aligned positive case
- `agree_group_issue`
  - vendor sees a positive pattern/group signal and we also have the panel in our positive set
- `ours_positive_vendor_rejected`
  - real disagreement worth audit
- `ours_positive_vendor_no_info`
  - our side positive, vendor side inconclusive
- `vendor_positive_not_in_ours`
  - vendor-side positive signal with no current matching panel in our onset shadow set
- `needs_date_anchor_review`
  - disagreement cannot be cleanly resolved without explicit temporal anchoring

## Missing Vendor Input

If `data/manual/vendor_reply_cases.csv` is absent, the build writes empty-but-valid outputs.

That keeps the audit layer non-blocking while making the missing manual input explicit.

## How To Use This Audit

This layer should inform:

- threshold review
- phenotype review
- onset shadow confidence review

It should not be treated as final truth ingestion.

The intended next step is to use disputes and field-confirmed positives to decide where model or phenotype tuning is actually justified.

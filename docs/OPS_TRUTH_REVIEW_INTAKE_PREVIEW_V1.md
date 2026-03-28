# OPS_TRUTH_REVIEW_INTAKE_PREVIEW_V1

## Purpose

`truth_review_batch_v1` exists so reviewers can work through the highest-value round-1 strict cases first.

That still leaves one important operational problem:

- reviewers need a safe place to type proposed labels,
- we need to validate those proposals before copyback,
- and we should not overwrite the canonical truth file too early.

This intake-preview step solves that problem.

It validates reviewer-filled round-1 rows, shows what would be copied back, and flags problems without modifying `panel_date_reaudit_working.csv`.

## Why This Step Is Preview-Only

The copyback template is intentionally a sidecar file.

That matters because direct overwrite is risky when:

- a reviewer mistypes `candidate_validity`,
- duplicate submissions exist for the same strict case,
- a row outside the round-1 batch is added by mistake,
- or supporting notes are filled but the actual label is still blank.

This preview step lets us catch those issues first.

## Reviewer-Editable Columns

The editable columns in `truth_review_copyback_template_v1.csv` are:

- `candidate_validity`
- `date_judgement`
- `note`
- `review_owner`
- `review_status`

For v1:

- `candidate_validity` is the only strictly validated field
- `date_judgement` is carried through as free text
- `note`, `review_owner`, and `review_status` are operational context fields

Allowed `candidate_validity` values:

- `true_positive`
- `group_side`
- `false_positive`
- `needs_more_info`
- blank

## How To Read `intake_row_status`

Possible statuses:

- `untouched_blank`
- `ready_for_copyback_preview`
- `incomplete_missing_candidate_validity`
- `invalid_candidate_validity`
- `duplicate_submission`
- `unexpected_key`

Interpretation:

- `untouched_blank`: reviewer has not really started this row yet
- `ready_for_copyback_preview`: key matches round-1 and `candidate_validity` is valid
- `incomplete_missing_candidate_validity`: reviewer filled supporting fields but left the main label blank
- `invalid_candidate_validity`: reviewer entered a label outside the allowed set
- `duplicate_submission`: the same strict case appears more than once in the template
- `unexpected_key`: template row is not part of the round-1 batch

## When A Row Is Safe To Copy Back

A row is safe to copy back manually only when:

- the key is part of the round-1 batch,
- `intake_row_status == ready_for_copyback_preview`,
- and the reviewer note is good enough to defend the proposed label later.

Rows with any other status should be resolved before manual copyback into canonical truth workflow.

## Outputs

- `_share/truth_review_intake_summary_v1.csv`
- `_share/truth_review_intake_preview_v1.csv`
- `_share/truth_review_intake_issues_v1.csv`

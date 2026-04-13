# OPS_TRUTH_REVIEW_BATCH_V1

## Purpose

Truth coverage is now the main bottleneck in the strict-case universe.

We already have a priority audit. What we need next is a practical round-1 manual review batch that:

- stays focused on the highest-yield unlabeled cases,
- avoids spending early effort on low-yield backlog rows,
- and gives reviewers a clean sidecar file to work in without touching canonical truth files too early.

This patch does that packaging only. It does not change any official prediction output.

## Why Round-1 Excludes Precursor Note Context And Monitor-Only Backlog

Round-1 is intentionally narrow.

It includes only:

1. `urgent_official_error_context`
2. `vendor_backed_unlabeled`
3. `high_actionability_unlabeled`

It excludes:

- `precursor_note_context`
- `monitor_only_backlog`
- `already_labeled`

That is deliberate because round-1 should maximize immediate label value.

`precursor_note_context` is still useful, but it is not directly pressuring the current official baseline the way official-error rows do.

`monitor_only_backlog` is lower-yield by definition, so it should not compete with higher-value unlabeled rows in the first pass.

## How To Use `truth_review_batch_v1.csv`

Use `truth_review_batch_v1.csv` as the main reviewer worklist.

It provides:

- stable round-1 ordering,
- bucket rank,
- current algorithm context,
- vendor context,
- and a short review checklist telling the reviewer what to focus on first.

Review focus meanings:

- `official_error_reaudit`
- `vendor_field_log_compare`
- `actionability_sanity_check`

The intended workflow is simple:

1. start from the top of the batch,
2. review within site and bucket order,
3. collect enough evidence to support a defensible human label,
4. record that decision in the sidecar copyback template first.

## How To Use `truth_review_copyback_template_v1.csv`

`truth_review_copyback_template_v1.csv` is a sidecar template only.

It is intentionally blank in:

- `candidate_validity`
- `date_judgement`
- `note`
- `review_owner`
- `review_status`

This is important because we do not want to touch canonical truth files prematurely.

Recommended process:

1. fill the sidecar template during review,
2. resolve disagreements or incomplete notes,
3. only then decide what should be copied into the canonical truth workflow.

That keeps the official truth contract cleaner and reduces accidental overwrite risk.

## What A Good Round-1 Manual Review Outcome Looks Like

A good round-1 outcome is not just “more labels.”

It should produce:

- defensible `candidate_validity` decisions on the highest-value unlabeled cases,
- clearer interpretation of current official error rows,
- cleaner comparison between vendor context and algorithm output,
- and fewer ambiguous maintenance/actionability disputes.

If round-1 is successful, the next iteration should be driven by improved truth coverage, not by another blind round of heuristic tuning.

## Outputs

- `_share/truth_review_batch_v1.csv`
- `_share/truth_review_site_packets_v1.csv`
- `_share/truth_review_copyback_template_v1.csv`

# OPS_TRUTH_REVIEW_EVIDENCE_PACK_V1

## Purpose

Truth coverage is still the current bottleneck.

We already have:

- a priority audit
- a round-1 review batch
- an intake preview

That is enough for queueing and validation, but not enough for fast human review.

Reviewers still need a compact case-by-case evidence pack that tells them:

- why the row is in round-1,
- what question they are supposed to answer,
- and which evidence sources to open first.

This patch creates that reviewer-facing pack. It does not change any official output.

## Why Batch + Intake Preview Were Not Enough

`truth_review_batch_v1.csv` gives priority and context, but it is still closer to an operations queue than a review workbook.

`truth_review_intake_preview_v1.csv` is useful after a reviewer fills the sidecar template, but it does not help much with the initial decision itself.

The missing layer was a compact evidence-oriented view that makes manual review faster and more consistent before copyback.

## How To Use `truth_review_evidence_pack_v1.csv`

Use `truth_review_evidence_pack_v1.csv` as the main reviewer worksheet.

It combines:

- round-1 ordering
- actionability / phenotype context
- vendor context
- onset context
- official error context
- precursor/site-note context when relevant
- short Korean evidence summaries and review questions

The intent is simple:

1. open the row
2. read `evidence_summary_ko`
3. answer `review_question_ko`
4. use `recommended_sources_ko` to decide which supporting records to inspect next
5. then write the final proposal into the copyback sidecar

## How To Use `truth_review_case_prompts_v1.csv`

`truth_review_case_prompts_v1.csv` is the compact human-review view.

It is optimized for actual review sessions and handoff, not for diagnostics.

Use it when:

- a reviewer wants a short checklist,
- work is being done live with someone else,
- or cases are being split quickly across people.

It keeps only the essentials:

- case key
- order
- review focus
- candidate-validity axis
- date-judgement axis
- review question
- recommended sources

## How Site Packets Help Split Work

`truth_review_site_packets_detailed_v1.csv` groups the same round-1 universe by site and priority bucket.

That helps when:

- work needs to be split by site owner,
- one reviewer is better suited for vendor reconciliation,
- or another reviewer is better suited for actionability sanity checks.

Each packet includes a short Korean summary telling the reviewer what to inspect first for that site/bucket slice.

## Outputs

- `_share/truth_review_evidence_pack_v1.csv`
- `_share/truth_review_site_packets_detailed_v1.csv`
- `_share/truth_review_case_prompts_v1.csv`

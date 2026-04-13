# OPS_PANEL_DAY_CORE_DUPLICATE_AUDIT_V1

## Purpose

This patch audits duplicate raw keys in `panel_day_core.csv` before any dedupe or normalization policy is chosen.

It does not change:

- official prediction output,
- official scoring logic,
- canonical truth,
- or the source `panel_day_core.csv` files.

It only classifies duplicate `site + panel_id + date` groups so we can decide later whether any dedupe or upstream fix is safe.

## Why The Evidence-Matrix Build Failed Loudly

`panel_day_evidence_matrix_v1` was designed to preserve exactly one row per:

- `site`
- `panel_id`
- `date`

That builder must fail loudly when duplicate raw keys appear, because otherwise it would silently choose one row, merge rows, or overwrite conflicting evidence.

The loud failure is therefore a governance safeguard, not a bug.

## Why Silent Dedupe Is Unsafe Before Classification

Not every duplicate key means the same thing.

Some duplicate groups may be harmless repeats of the exact same raw row.
Other duplicate groups may contain conflicting values in non-key columns.

If we silently dedupe before classifying them, we lose the chance to answer:

- whether the group is an exact replay,
- whether values conflict,
- and whether the right fix belongs in downstream normalization or upstream data generation.

That is why this audit runs first and writes the raw duplicate groups and raw duplicate rows back out for inspection.

## What `exact_duplicate_group` And `conflicting_duplicate_group` Mean

`exact_duplicate_group` means:

- the duplicate rows share the same `site + panel_id + date`,
- and every non-key column matches after comparison normalization.

Comparison normalization here is intentionally narrow:

- blank and `NaN` are treated consistently,
- strings are trimmed,
- numeric-looking values are compared after numeric coercion where possible.

`conflicting_duplicate_group` means:

- the duplicate rows share the same key,
- but at least one non-key column differs after that normalization.

Those groups should not be silently deduped.

## What Evidence Is Needed Before Choosing A Normalization Policy

Before choosing any dedupe or normalization rule, we need to know:

- which duplicate groups are exact repeats,
- which groups have conflicting evidence fields,
- which columns conflict,
- and whether those conflicts come from an upstream generator issue or from a downstream interpretation problem.

Only after that review can we safely choose between options such as:

- allowing exact dedupe only,
- adding a rule-based collapse policy,
- or fixing the upstream data build that produced the duplicates.

## Outputs

- `_share/panel_day_core_duplicate_audit_summary_v1.csv`
- `_share/panel_day_core_duplicate_groups_v1.csv`
- `_share/panel_day_core_duplicate_rows_v1.csv`

# OPS_PANEL_DAY_CORE_DUPLICATE_RESOLUTION_AUDIT_V2

## Purpose

This patch refines the `panel_day_core` duplicate audit with an evidence-matrix-aware comparison frame before any dedupe policy is chosen.

It does not change:

- official prediction output,
- official scoring logic,
- canonical truth,
- or the source `panel_day_core.csv` files.

It only asks a narrower governance question:

- do duplicate rows differ in ways that materially affect `panel_day_evidence_matrix_v1`,
- or do they differ only in provenance, auxiliary fields, or tiny numeric jitter.

## Why V1 Duplicate Audit Was Necessary But Insufficient

The v1 audit was needed because it proved the evidence-matrix build was right to fail loudly.

Without that first step, we did not know whether duplicate keys were:

- exact repeats,
- or conflicting rows.

But v1 still treated every non-key difference as the same kind of conflict.

That is not enough to choose a safe dedupe policy, because a source-file name difference is not the same as a `mid_ratio` difference.

## Why All Non-Key Differences Are Not Equally Important

Some columns are just provenance or ingestion lineage.
Some are auxiliary diagnostics that do not feed `panel_day_evidence_matrix_v1`.
Some directly control the evidence layer that later episode and incident logic will rely on.

Those categories have different governance meaning:

- provenance-only differences may justify dropping an extra export copy,
- auxiliary-only differences may justify keeping one row after equivalence review,
- tiny critical numeric jitter may still need tolerance review,
- and evidence-critical conflicts may require an upstream fix or an explicit rule.

## Why Evidence-Critical Columns Are The Right Comparison Frame

The v2 audit centers the comparison on the fields that directly feed `panel_day_evidence_matrix_v1`, including:

- `coverage_mid`
- `mid_ratio`
- `last_ratio`
- `mid_v_ratio`
- `mid_i_ratio`
- `v_drop`
- `shadow_like`
- `group_off_like`
- `group_key_base`
- and shape/instability raw columns when present

That frame is the right one because the immediate governance question is not:

- are these rows identical everywhere,

but rather:

- would choosing one raw row over the other change the evidence matrix.

## Why `numeric_jitter_duplicate` Should Not Be Auto-Collapsed Yet

Tiny numeric drift can look harmless, but it still needs explicit review.

Even when the drift is within the conservative `1e-6` tolerance used here, auto-collapsing it would quietly turn an audit judgment into a normalization policy.

So v2 only labels those groups as `numeric_jitter_duplicate` and emits:

- the differing critical fields,
- and `max_abs_diff_critical_numeric`

for downstream review.

That makes the potential safe-to-collapse cases visible without committing the project to that policy yet.

## What Results Justify A Safe Pre-Normalizer Vs An Upstream Export Fix

A safe pre-normalizer becomes more plausible when duplicate groups are dominated by:

- provenance-only differences,
- or evidence-equivalent auxiliary-only differences,
- with no material evidence-critical conflicts.

An upstream export fix is the stronger candidate when duplicate groups show:

- material changes in evidence-critical fields,
- or mixed patterns that cannot be explained as provenance copies or tiny jitter.

The point of this audit is to separate those cases before anyone chooses a collapse rule.

## Outputs

- `_share/panel_day_core_duplicate_resolution_summary_v2.csv`
- `_share/panel_day_core_duplicate_resolution_groups_v2.csv`
- `_share/panel_day_core_duplicate_resolution_critical_diffs_v2.csv`

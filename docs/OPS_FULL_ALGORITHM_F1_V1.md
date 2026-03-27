# OPS Full Algorithm F1 V1

## Purpose

This evaluator measures full strict-case algorithm F1.

This is the right answer to:

"What is the current full algorithm F1 over all strict cases?"

The unit is one strict case row from `_share/panel_date_reaudit_working.csv`.

## Why This Differs From Vendor-Only F1

Vendor-only family F1 is still useful.

It answers a narrower question:

- how well the current GPVS-derived family classifier matches vendor-adjudicated family labels

That is not enough for full algorithm F1 because:

- the full algorithm covers all current strict cases
- the truth source is `candidate_validity`
- the prediction target is actionability, not vendor family

## Inputs

- `_share/panel_date_reaudit_working.csv`
- `_share/critical_actionability_shadow_v3_latest.csv`
- optional v5 packet outputs for offline reconciliation only

This evaluator prefers `actionability_v3` directly.

Packet outputs are not the primary prediction layer.

## Truth Mapping

Map `candidate_validity` as:

- positive: `true_positive`, `group_side`
- negative: `false_positive`
- exclude: `needs_more_info`, blank

## Prediction Modes

### `maintenance`

Positive:

- `maintenance_candidate`

Negative:

- everything else

### `operational`

Positive:

- `maintenance_candidate`
- `common_cause_review`
- `singleton_review`

Negative:

- `monitor_only`
- blank or unmatched `actionability_v3`

## Join Rule

Join predictions on:

- `site`
- `panel_id`
- `strict_trigger_date`

This avoids mixing retrospective onset dates with the strict-case evaluation unit.

## Metrics

For each prediction mode:

- `tp`
- `fp`
- `fn`
- `tn`
- `precision`
- `recall`
- `f1`
- `excluded_rows`
- `scored_rows`
- `coverage`

Coverage is the fraction of scored rows that have a matched `actionability_v3` row.

Rows without a matched actionability row still count as negative predictions.

## Diagnostic Source Split

The summary also emits source splits:

- `overall`
- `vendor_reply_present`
- `vendor_reply_absent`

This is diagnostic only.

It helps distinguish:

- strict cases already touched by vendor review
- strict cases that currently have no vendor feedback

## Outputs

- `_share/full_algorithm_f1_summary.csv`
- `_share/full_algorithm_confusion.csv`
- `_share/full_algorithm_case_errors.csv`

`full_algorithm_case_errors.csv` carries panel-level false positives and false negatives with:

- truth fields from `panel_date_reaudit_working.csv`
- current `actionability_v3`
- review priority
- vendor context when present

## Current Real-Data Caveat

If `candidate_validity` is still blank for most or all rows, the evaluator will exclude those rows.

That is expected.

This evaluator is still the correct layer because it is tied to the intended full strict-case truth table.

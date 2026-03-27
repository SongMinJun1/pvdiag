# OPS Full Algorithm F1 V2

## Purpose

This evaluator measures full strict-case algorithm F1 with hybrid truth.

It is the right answer to:

"What is the current full algorithm F1 under today's actual truth availability?"

The evaluation unit is still one strict case row from `_share/panel_date_reaudit_working.csv`.

## Why V1 Was Not Enough

V1 depended only on manual `candidate_validity`.

That was structurally correct, but it under-scored the real system because the current real dataset still has blank manual truth on most rows.

Under the current data state:

- manual re-audit truth is the preferred source
- vendor reply exists for a smaller but still useful subset
- rows with neither source should stay excluded

So V2 keeps the strict-case universe from the re-audit table, but uses hybrid truth precedence.

## Why Hybrid Truth Is Necessary

Hybrid truth means:

1. use manual re-audit truth when it exists
2. otherwise fall back to vendor truth
3. otherwise exclude

This is the only way to answer "full algorithm F1" without pretending that blank manual columns are real negatives.

Vendor-only family F1 is still useful, but it is not sufficient:

- it evaluates GPVS fault-family classification
- it does not evaluate strict-case actionability predictions
- it does not cover the full strict-case universe

## Inputs

- `_share/panel_date_reaudit_working.csv`
- `_share/vendor_reply_adjudication_latest.csv`
- `_share/critical_actionability_shadow_v3_latest.csv`
- optional v5 packet outputs for offline diagnostics only

This evaluator uses `actionability_v3` as the prediction layer.

Packet/routing outputs are not the primary prediction source.

## Hybrid Truth Precedence

### A. Manual Truth

If `candidate_validity` is nonblank, use it first.

Mapping:

- positive: `true_positive`, `group_side`
- negative: `false_positive`
- exclude: `needs_more_info`, blank

### B. Vendor Truth

If manual truth is blank, use `vendor_reply_class`.

#### `strict`

- positive: `field_confirmed_positive`, `vendor_pattern_positive`
- negative: `vendor_rejected`
- exclude: `vendor_likely_positive`, `vendor_no_info`, blank

#### `lenient`

- positive: `field_confirmed_positive`, `vendor_pattern_positive`, `vendor_likely_positive`
- negative: `vendor_rejected`
- exclude: `vendor_no_info`, blank

### C. No Usable Truth

If neither manual nor vendor truth is usable, exclude the row.

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

Join prediction rows on:

- `site`
- `panel_id`
- `strict_trigger_date`

This keeps the evaluation aligned to the strict-case unit, not to retrospective onset dates or routing packets.

## Metrics

For each combination of:

- `truth_mode` in `{strict, lenient}`
- `prediction_mode` in `{maintenance, operational}`
- `source_split` in `{overall, manual_truth, vendor_truth}`

emit:

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

Coverage is:

- matched `actionability_v3` rows / scored rows

Rows without a matched actionability row still count as negative predictions.

That is intentional.

Coverage is diagnostic, not a substitute for F1.

## How To Read `source_split`

- `overall`: the full strict-case universe after hybrid truth precedence
- `manual_truth`: rows scored from manual `candidate_validity`
- `vendor_truth`: rows scored from vendor truth because manual truth was absent

This split helps separate:

- genuinely reviewed manual truth coverage
- provisional vendor-supervised coverage

## Outputs

- `_share/full_algorithm_f1_summary_v2.csv`
- `_share/full_algorithm_confusion_v2.csv`
- `_share/full_algorithm_case_errors_v2.csv`

`full_algorithm_case_errors_v2.csv` carries panel-level false positives and false negatives with:

- truth source
- hybrid truth label
- current `actionability_v3`
- review priority
- vendor context when present
- re-audit note

## Interpretation

This is the correct answer to "full algorithm F1" under current data availability because it:

- preserves the strict-case universe
- prefers manual truth whenever it exists
- still scores the vendor-backed subset instead of discarding it
- reports coverage explicitly so we do not over-read sparse prediction joins

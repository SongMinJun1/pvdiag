# OPS Critical Actionability F1

## Purpose

This is a critical-lane F1 evaluation.

It is not a full engine F1.

Reason:

- it evaluates only the vendor-adjudicated critical subset
- it evaluates panel-level `actionability_v3`
- it does not evaluate packet routing or downstream review packaging

## What Is Being Evaluated

Algorithm prediction source:

- `_share/critical_actionability_shadow_v3_latest.csv`
- field used: `actionability_v3`

Truth source:

- `_share/vendor_reply_adjudication_latest.csv`
- field used: `vendor_reply_class`

## Truth Modes

### `strict`

Positive:

- `field_confirmed_positive`
- `vendor_pattern_positive`

Negative:

- `vendor_rejected`

Excluded:

- `vendor_likely_positive`
- `vendor_no_info`
- blank

### `lenient`

Positive:

- `field_confirmed_positive`
- `vendor_pattern_positive`
- `vendor_likely_positive`

Negative:

- `vendor_rejected`

Excluded:

- `vendor_no_info`
- blank

## Prediction Modes

### `maintenance`

Positive:

- `maintenance_candidate`

Negative:

- everything else

### `operational_review`

Positive:

- `maintenance_candidate`
- `common_cause_review`
- `singleton_review`

Negative:

- `monitor_only`
- blank or unmatched algorithm output

## Why Packet Routing Is Not Used

Packet outputs are operational packaging layers.

They are useful for sharing and review workflow, but they are not the right unit for F1.

This evaluator stays at the panel-level actionability decision so that:

- truth and prediction stay aligned at the same unit
- routing aggregation does not distort classification metrics

## Outputs

- `_share/critical_actionability_f1_summary.csv`
- `_share/critical_actionability_confusion.csv`
- `_share/critical_actionability_case_errors.csv`

`case_errors` contains panel-level false positives and false negatives for each `(truth_mode, prediction_mode)` pair.

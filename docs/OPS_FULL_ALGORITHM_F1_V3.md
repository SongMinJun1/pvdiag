# OPS Full Algorithm F1 V3

## Purpose

This evaluator measures full strict-case algorithm F1 with:

- the same hybrid truth used in V2
- a conservative fallback prediction layer for unmatched strict cases

It answers:

"What is the current full strict-case F1 if we safely extend prediction coverage without changing the core engine?"

## Why V2 Under-Covered Prediction Space

V2 fixed the truth problem.

It used:

- manual re-audit truth when available
- vendor truth when manual truth was missing

That was the right truth layer.

But prediction coverage still stayed limited because many strict cases had blank `actionability_v3`.

In current real data, that gap is mostly unmatched `confirmed_fault_flag` rows.

## What V3 Changes

V3 keeps hybrid truth unchanged.

Only the prediction layer changes:

1. use original `actionability_v3` first
2. if it is blank, derive a conservative fallback from algorithm-side fields already present in `panel_date_reaudit_working.csv`
3. never synthesize `maintenance_candidate`

This makes V3 a coverage patch, not a truth patch.

## Hybrid Truth Precedence

Exactly the same as V2:

1. manual truth from `candidate_validity` if nonblank
2. otherwise vendor truth from `vendor_reply_class`
3. otherwise exclude

### Manual Truth Mapping

- positive: `true_positive`, `group_side`
- negative: `false_positive`
- exclude: `needs_more_info`, blank

### Vendor Truth Mapping

#### `strict`

- positive: `field_confirmed_positive`, `vendor_pattern_positive`
- negative: `vendor_rejected`
- exclude: `vendor_likely_positive`, `vendor_no_info`, blank

#### `lenient`

- positive: `field_confirmed_positive`, `vendor_pattern_positive`, `vendor_likely_positive`
- negative: `vendor_rejected`
- exclude: `vendor_no_info`, blank

## Why Fallback Uses Only Algorithm-Side Fields

Fallback uses only fields already produced on our side:

- `reason_summary`
- `onset_confidence`

Parsed from `reason_summary`:

- `strict_method`
- `shadow_frac`
- `group_off_frac`
- `recovery_reset`

This is deliberate.

V3 should not become dependent on:

- vendor routing outputs
- packet builders
- external truth files

It is meant to extend prediction coverage safely, using information the algorithm already emitted.

## Why Fallback Is Limited To `confirmed_fault_flag`

Fallback is intentionally narrow.

Only unmatched `confirmed_fault_flag` rows can be mapped.

### `confirmed_fault_clean`

Emit `singleton_review` only if all of the following hold:

- `strict_method == confirmed_fault_flag`
- `onset_confidence in {high, medium}`
- `recovery_reset == no`
- `shadow_frac <= 0.20`
- `group_off_frac <= 0.20`

### `confirmed_fault_confounded`

Emit `monitor_only` if:

- `strict_method == confirmed_fault_flag`
- and recovery/confound evidence suggests caution

That means:

- `recovery_reset == yes`
- or `shadow_frac > 0.20`
- or `group_off_frac > 0.20`

### Unmatched `critical_fault_flag`

Leave it blank.

Do not auto-promote it.

This is intentional.

Critical rows already have a separate interpretation lane, and V3 should not guess their actionability when the main actionability output is missing.

## Final Prediction Layer

`final_actionability_v3` is:

- original `actionability_v3` if present
- otherwise `derived_actionability_v3`

Fallback may emit only:

- `singleton_review`
- `monitor_only`
- blank

It never emits:

- `maintenance_candidate`

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
- blank

## Coverage Interpretation

V3 reports two coverages.

### `primary_coverage`

Rows with nonblank original `actionability_v3` / scored rows

This tells us how much of the evaluation is covered by the existing primary actionability lane.

### `effective_coverage`

Rows with nonblank `final_actionability_v3` / scored rows

This tells us how much of the evaluation becomes scorable after conservative fallback.

Interpretation:

- if `effective_coverage` rises while F1 remains reasonable, fallback is helping
- if `effective_coverage` rises but F1 degrades badly, fallback is too aggressive

## Outputs

- `_share/full_algorithm_f1_summary_v3.csv`
- `_share/full_algorithm_confusion_v3.csv`
- `_share/full_algorithm_case_errors_v3.csv`

`full_algorithm_case_errors_v3.csv` includes:

- original and derived actionability
- final prediction source
- parsed strict-evidence tokens
- truth source
- vendor context
- review priority and note

## Why This Is Safe

V3 does not:

- change hybrid truth
- change the core engine
- invent maintenance candidates
- auto-promote unmatched critical rows

It only fills a narrow gap for clean confirmed-fault strict cases, and pushes confounded confirmed-fault rows toward `monitor_only` instead of aggressive action.

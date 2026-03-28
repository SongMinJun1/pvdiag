# OPS_TRUTH_COVERAGE_PRIORITY_AUDIT_V1

## Purpose

Truth coverage is now the main bottleneck in the strict-case universe.

At this point, further heuristic tuning is less valuable than targeted manual truth collection because:

- the official baseline already depends heavily on vendor-backed truth where manual truth is absent,
- the remaining disagreements are concentrated in a small number of cases and contexts,
- and future baseline trustworthiness will improve faster if humans re-audit the right unlabeled cases first.

This audit creates that manual-review queue. It does not change any official prediction output.

## Why Truth Coverage Is The Main Bottleneck

The current strict-case universe has many cases but very little manual truth.

That means:

- evaluation quality is limited by missing human labels,
- official error rows cannot always be interpreted as model defects versus truth gaps,
- and maintenance-definition questions can look like algorithm problems when they are really labeling problems.

Because of that, the next useful move is not more tuning. It is better manual review prioritization.

## Why The Official Baseline Should Not Be Tuned Further First

If we keep tuning on top of sparse manual truth, we risk:

- overfitting to vendor-backed labels,
- encoding unresolved definition disputes into heuristics,
- and improving proxy metrics without improving trustworthiness.

Targeted manual review is a cleaner next step because it raises the quality of the evaluation target itself.

## Priority Buckets

The audit assigns each strict case to one fixed bucket.

Priority order:

1. `urgent_official_error_context`
2. `maintenance_definition_gap`
3. `vendor_backed_unlabeled`
4. `high_actionability_unlabeled`
5. `precursor_note_context`
6. `monitor_only_backlog`
7. `already_labeled`

### Urgent Official Error Context

These are unlabeled rows that already appear in the official `full_algorithm_f1_v3` error context.

This is the highest priority because manual truth here can change how we interpret current benchmark failures.

### Maintenance Definition Gap

These are unlabeled rows that appear in the maintenance-gap audit and already look like:

- candidate maintenance shadow promotions
- or cases that should remain review-only

These matter because they can resolve whether a remaining maintenance FN is a definition issue or an algorithm issue.

### Vendor-Backed Unlabeled

These rows do not yet have manual truth, but they do have vendor context.

They are good candidates for review because a human can compare:

- the site data,
- vendor response,
- and any available field log context

without starting from nothing.

### High Actionability Unlabeled

These rows already sit in a higher operational/actionability tier but still lack manual truth.

They deserve attention, but they remain below official-error and maintenance-gap contexts because the benchmark interpretation pressure is weaker there.

### Precursor Note Context

These rows sit inside the current site-specific precursor note context.

They are still useful, but they are lower priority than official-error contexts because:

- they are not directly defining the current official baseline error interpretation,
- and the precursor line is already in observation mode rather than adoption mode.

### Monitor-Only Backlog

These are unlabeled rows without higher-value context.

They should stay in backlog review unless higher-priority queues have been worked down.

## How To Use The Queue

Recommended review actions are fixed:

- `manual_reaudit_first`
- `compare_with_vendor_and_field_logs`
- `inspect_actionability_definition`
- `defer_until_backlog_review`
- `no_action_needed`

Use the cases output to work panel-by-panel.
Use the site queue output to assign review batches by site.

## What Evidence To Collect During Manual Re-Audit

For each reviewed case, collect enough evidence to support a stable manual truth label:

- whether the panel fault is real, not real, or still unresolved
- whether the case is panel-level, group/common-cause, or external/system-side
- whether the trigger timing is consistent with the observed traces
- any field maintenance log or vendor confirmation that materially changes interpretation
- a short note describing why the chosen manual label is defensible

That evidence should improve future baseline trustworthiness more directly than another round of heuristic tuning.

## Outputs

- `_share/truth_coverage_priority_summary_v1.csv`
- `_share/truth_coverage_priority_cases_v1.csv`
- `_share/truth_coverage_site_review_queue_v1.csv`

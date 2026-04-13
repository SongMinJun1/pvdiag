# OPS_COMMON_CAUSE_INCIDENT_GATE_AUDIT_V1

## Purpose

This patch audits why `common_cause_incident_registry_v1` yields zero real incidents before changing any incident thresholds.

It does not change:

- official prediction output,
- official scoring logic,
- canonical truth,
- or the incident registry builder itself.

It only compares fixed gate tiers against the current evidence matrix and optional precursor candidate days.

## Why Zero Real Incidents Is A Critical Diagnostic Result

A synthetic fixture can show that the incident registry code path works.

But a real build with zero incidents is still a critical result because it means one of three things may be true:

- current defaults are too strict,
- precursor candidate logic and incident logic are describing different layers,
- or the underlying feature definition does not create the grouped signal the incident layer expects.

That distinction matters before anyone changes defaults.

## Why Synthetic Pass Is Not Enough

Synthetic pass only proves:

- the builder can create candidate days,
- merge overlapping days,
- and write registry rows.

It does not prove that the real evidence matrix has site/day patterns that satisfy the default incident gates.

That is why this audit recomputes real site/day evidence and evaluates several fixed tiers side by side.

## How `schema_default` Differs From The Precursor-Like Tiers

`schema_default` keeps the current registry posture:

- grouped signal must clear both a panel-count threshold and a `group_share` threshold,
- and the site/day must then pass the multi-group or site-wide incident gate.

The precursor-like tiers loosen that posture in two ways:

- they remove the grouped-share requirement,
- and they mirror the broader precursor candidate logic more closely.

This lets us see whether zero incidents is mainly a threshold issue or whether the incident logic is genuinely asking for a different kind of grouped evidence.

## What Result Would Justify Changing Defaults

A threshold change becomes more justifiable if the audit shows that:

- many real site/days fail only on `group_share`,
- relaxed tiers recover a meaningful number of candidate days,
- and those recovered days overlap strongly with precursor candidate days.

That pattern would suggest the default gate is filtering out evidence that may already be operationally interesting.

## What Result Would Justify Keeping Defaults And Treating Precursor Logic As A Separate Layer

Keeping defaults is more justified if the audit shows that:

- relaxed tiers recover few real days,
- or recovered days do not overlap well with precursor candidates,
- or failures are dominated by `no_signal` / `no_qualifying_groups` rather than a single tight threshold.

That would support the idea that the precursor logic and incident logic are different layers rather than the same layer under different constants.

## Outputs

- `_share/common_cause_incident_gate_audit_summary_v1.csv`
- `_share/common_cause_incident_gate_days_v1.csv`
- `_share/common_cause_incident_gate_comparison_v1.csv`

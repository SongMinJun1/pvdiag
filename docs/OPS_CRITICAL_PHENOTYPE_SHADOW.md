# OPS Critical Phenotype Shadow

## Purpose

`critical_fault_flag` is operationally useful but too broad to explain what kind of critical case we are seeing.

This shadow layer reclassifies only existing critical strict cases into a small set of more interpretable phenotypes.

It is shadow-only and does not modify the current core engine.

## Candidate Conservation

This patch does not create new candidates.

Only onset-shadow rows whose reconstructed strict method is:

- `critical_fault_flag`

are processed.

Every processed row stays tied to an already existing strict panel case.

## Local Peak Anchor

Each critical case is anchored locally, not globally.

Anchor window:

- `strict_trigger_date ± 7 days`

Anchor selection rule:

1. maximum `v_drop`
2. tie-break minimum `mid_v_ratio`
3. tie-break nearest to `strict_trigger_date`

This keeps the phenotype readout attached to the locally strongest critical signature.

## Phenotypes

Current shadow phenotypes:

- `diode_or_module_damage_like`
- `open_or_device_issue_like`
- `group_or_inverter_side_like`
- `weak_critical_candidate`

These are descriptive shadow buckets, not final ground-truth labels.

## Initial Rule Intent

`diode_or_module_damage_like`

- voltage side depressed
- current side comparatively preserved
- good reference quality
- not primarily shadow or group-off

`open_or_device_issue_like`

- near-collapse level ratios
- extreme `v_drop`

`group_or_inverter_side_like`

- near-collapse current side
- comparatively elevated voltage side

`weak_critical_candidate`

- current rule set does not cleanly support the stronger buckets

## Confidence

`phenotype_confidence` is annotation only:

- `high`
- `medium`
- `low`

Stronger confidence generally means:

- the anchor row cleanly matches one rule
- confound flags are low
- coverage is adequate

Weak or confounded rows stay visible as shadow outputs rather than being hidden.

## Vendor Matrix

`critical_phenotype_vendor_matrix.csv` provides a simple cross-tab by:

- `site`
- `critical_phenotype`
- `vendor_reply_class`
- `vendor_fault_family`

This is intended for supervision review only.

It does not make vendor replies gold truth.

## Scope Guard

This patch does not change:

- `pv_ae/panel_day_engine.py`
- strict trigger generation
- current weather/event/frame/episode outputs
- vendor adjudication builder outputs
- canonical panel-level truth template contract

# OPS Maintenance Promotion Proxy Audit V1

## Why This Exists

`maintenance_shadow_f1_v1` showed that maintenance-shadow promotion could improve F1 materially. That is promising, but it is not enough to justify an official rule.

We still need to answer a harder question:

- can the current shadow-promotion candidates be separated by algorithm-side features alone?

This patch is an audit for that question.

## Why Strict-Backed Shadow Cannot Be Copied Directly Into Official Rules

`strict_backed_shadow` is an offline evaluation scenario. It uses scored truth-backed membership from the maintenance-gap audit. That makes it useful for evaluation, but not safe to copy directly into an operational rule.

If we want an official maintenance-promotion patch later, we need a proxy that can be computed from algorithm-side features only.

## Audit Universe

This audit only inspects rows from:

- `_share/maintenance_shadow_promotion_sets_v1.csv`

filtered to:

- `promotion_hypothesis == candidate_for_maintenance_shadow`

That keeps the audit narrow. It does not invent new candidates outside the current shadow-promotion shortlist.

## `target_proxy_tier` Is Audit-Only

The audit labels each candidate with:

- `strict_backed_candidate`
- `lenient_only_candidate`

based on current shadow set membership:

- `strict_backed_candidate` if `in_strict_backed_shadow == 1`
- `lenient_only_candidate` if `in_full_candidate_shadow == 1` and `in_strict_backed_shadow == 0`

This label is only an offline comparison target. It must never be written back as an algorithm rule and must never change any official prediction output.

## Why This Stage Uses Algorithm-Side Features Only

The purpose here is to test whether any future promotion rule could stand on its own in production. That means the audit must use:

- current algorithm outputs
- onset-shadow context
- strict-day `panel_day_core` features
- same-day collapse counts derived from `panel_day_core`

It must not use vendor labels or truth labels as direct rule inputs.

## Derived Proxy Features

The audit computes, among others:

- `strict_day_zero_like_flag`
- `strict_day_open_like_flag`
- `strict_day_group_like_flag`
- `strict_day_electrical_like_flag`
- `onset_recent_flag`
- `onset_long_horizon_flag`
- `clean_confirmed_flag`
- `same_group_zero_like_count`
- `same_site_zero_like_count`

These are all algorithm-side proxies.

## Fixed Proxy Rules

The audit evaluates five fixed rule candidates:

### `recent_clean_confirmed`

- `clean_confirmed_flag == 1`
- `onset_recent_flag == 1`

### `long_horizon_clean_confirmed`

- `clean_confirmed_flag == 1`
- `onset_long_horizon_flag == 1`

### `strict_day_open_like`

- `strict_day_open_like_flag == 1`

### `strict_day_group_collapse`

- `same_group_zero_like_count >= 2`
- or `same_site_zero_like_count >= 3`

### `electrical_like_clean`

- `clean_confirmed_flag == 1`
- `strict_day_electrical_like_flag == 1`

## How To Read Rule Precision / Recall

The rule table reports:

- `precision_for_strict_backed`
- `recall_for_strict_backed`

Interpretation:

- precision answers: among rows selected by this proxy, how many belong to the offline `strict_backed_candidate` tier?
- recall answers: among all offline `strict_backed_candidate` rows, how many does this proxy recover?

High precision with weak recall means a narrow but clean proxy.
High recall with weak precision means the proxy is broad and leaks into lenient-only candidates.

## Why A Clean Proxy May Fail To Exist

This candidate set is small and heterogeneous. It is entirely possible that:

- some strict-backed rows look like group collapse
- some lenient-only rows look like isolated open/device behavior
- no single proxy rule cleanly separates them

If that happens, the right conclusion is not to force a rule. The right next step is to keep the official maintenance rule unchanged and treat the shadow gain as informative but not deployment-ready.

## Outputs

- `_share/maintenance_promotion_proxy_cases_v1.csv`
- `_share/maintenance_promotion_proxy_summary_v1.csv`
- `_share/maintenance_promotion_proxy_rules_v1.csv`

These outputs are audit-only and do not modify any official prediction layer.

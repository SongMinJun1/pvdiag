# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY FATE AUDIT V1

## Why Secondary Discovery Needed Retrospective Validation
- The learned secondary discovery lane was intentionally separated from the deterministic operator baseline.
- That separation makes sense only if the extra lane surfaces hidden value later:
  - later fault linkage
  - later truth linkage
  - or at least recurring monitor burden
- Without retrospective fate checks, the lane could simply be adding noisy short runs.

## Why The Current Lane Looked Potentially Noisy
- The first secondary discovery export was dominated by `short_alert_run`.
- Short runs can still be valuable, but they are also the most likely to be unstable or nuisance-like.
- This audit therefore asks whether those short learned discoveries later turn into:
  - real fault follow-up
  - later truth rows
  - recurring burden
  - or nothing useful

## Discovery Fate Classes
- `future_fault_linked`
  - later confirmed/critical/final fault appears on the same panel within 30d or 60d
- `future_truth_linked`
  - no future fault flag yet, but later `reaudit` truth row appears on the same panel within 30d or 60d
- `recurring_monitor_like`
  - no later fault/truth, but helper-derived alert runs recur within 60d
- `isolated_unexplained`
  - no later fault, truth, or recurrence is found

## What Would Justify Keeping Secondary Discovery As-Is
- meaningful `future_fault_or_truth_linked_rate`
- and acceptable short-run linkage rate
- and limited `isolated_unexplained_rate`

## What Would Justify Adding Short-Run Suppression Or A Minimum Run-Length Filter
- discovery lane remains heavily short-run dominated
- and short runs are mostly `isolated_unexplained`
- while longer runs show better later linkage

## What Would Justify Stopping Secondary Discovery Lane
- most selected runs end up `isolated_unexplained`
- fault/truth linkage is weak
- recurrence signal is also low, so the lane adds little operator or analyst value

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.

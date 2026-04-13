# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY THRESHOLD SPLIT AUDIT V1

## Why Short-Run Suppression Alone Was Rejected
- The retrospective fate audit showed that many short discovery runs are noisy, but some short runs later linked to real faults.
- That means a simple minimum-length filter would throw away some hidden-value cases together with nuisance-like cases.
- The next step therefore tests whether a small set of current-state thresholds can separate value-like cases from recurring monitor burden more cleanly.

## Why Threshold Split Is The Next Simple Policy Test
- The separability audit suggested that a few current-state features have non-trivial gaps between `future_fault_linked` and `recurring_monitor_like`.
- Before trying anything more complex, the most operationally useful check is:
  - can a simple rule family recover at least half of hidden-value cases
  - while keeping recurring or isolated contamination acceptably low
- This audit sweeps only a fixed, small set of threshold rules so the result stays interpretable.

## Why `cond_evt_only_day_ratio` Is Not Used As A Positive Selector Here
- `cond_evt_only_day_ratio` can rise both in useful linked cases and in noisy or recurring short-alert patterns.
- In the current lane it is not a clean “positive-only” discriminator.
- The simple split audit therefore prioritizes features that already showed clearer separability hints:
  - learned discovery score
  - electrical severity score
  - low AE corroboration
  - low recon error

## Recommended Next Directions
- `split_secondary_discovery_into_value_vs_monitor`
  - at least one simple rule keeps meaningful hidden-value capture with net positive precision over recurring plus isolated negatives
- `keep_secondary_discovery_as_analyst_only`
  - even the best simple rule is too weak, so the lane should remain a manual review lane rather than an operational split

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.

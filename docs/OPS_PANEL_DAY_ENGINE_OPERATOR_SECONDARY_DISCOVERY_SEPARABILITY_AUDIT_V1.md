# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY SEPARABILITY AUDIT V1

## Why Short-Run Suppression Is Not The Next Step
- The fate audit showed that the lane is short-run heavy, but not all short runs are noise.
- Some short runs later linked to real fault outcomes, so length alone is too blunt as the next filter.
- The next question is whether current-state signals can separate hidden value from recurring burden before any hard suppression rule is added.

## Why Current-State Separability Is The Key Question Now
- Operators need to decide whether the learned lane can be split operationally at review time.
- That requires testing only what is visible at the time of discovery:
  - learned score
  - deterministic electrical score
  - run length and shape
  - voltage-ratio, event-ratio, signal-count, and recon-error features
- Future fault and recurrence fields are used only as retrospective labels, not as split features.

## Why Site Effect And Feature Effect Must Be Separated
- A discovery lane can look useful for the wrong reason if one site happens to dominate later linked outcomes.
- Site effect asks:
  - does the lane behave very differently by site?
- Feature effect asks:
  - within the lane, do current-state features already separate hidden-value cases from recurring monitor burden?
- Both checks are needed before deciding whether to add thresholds or site-conditioned policy.

## Recommended Next Directions
- `try_site_conditioned_discovery_policy`
  - site mix explains the fate split more than current-state feature gaps, so site-aware handling should be tested first
- `try_feature_threshold_split`
  - one or more current-state features show a clear robust gap between `future_fault_linked` and `recurring_monitor_like`, so a simple split policy is testable
- `keep_secondary_discovery_as_analyst_only`
  - neither site effect nor feature effect is decisive enough, so the lane should remain a manual analyst aid

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Canonical truth template contract is unchanged.

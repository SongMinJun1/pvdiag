# OPS PANEL DAY ENGINE OPERATOR SECONDARY DISCOVERY INCREMENTAL VALUE AUDIT V1

## Why Panel Rollup Alone Was Not Enough
- Rolling the secondary discovery value lane up to one row per panel made the artifact more operator-friendly.
- But panel rollup by itself does not answer the key operational question:
  - are these value panels actually adding coverage beyond what operators already see in the current attention baseline?
- This audit therefore measures the value lane against the existing attention baseline at the same panel granularity.

## Why Incremental Coverage Versus Current Attention Is The Key Next Question
- The secondary discovery lane is only useful operationally if it contributes panels that are not already present in `operator_attention_now`.
- A panel that appears in both places may still be interesting, but it is not incremental coverage.
- The most important quantity is therefore:
  - secondary-only panels
  - that later show retrospective fault or truth linkage
- That is the cleanest current measure of hidden panel-level value beyond the baseline.

## Why Retrospective Fault / Truth Reference Is Used Here
- This audit is intentionally retrospective.
- It does not change detection logic, baseline attention logic, or operator ranking.
- Instead it asks:
  - among panels already surfaced by either lane,
  - which ones later looked justified by future-linked reference evidence?
- Using retrospective fault / truth reference is appropriate here because the goal is not online scoring fairness, but ex-post coverage value.

## How To Interpret The Result
- Keep as analyst lane:
  - if there are some secondary-only panels with retrospective linkage,
  - but the incremental rate is modest or overlap with baseline is still high
- Integrate more tightly into operator workflow:
  - if secondary-only linked panels are frequent enough to represent meaningful extra coverage beyond baseline attention
- Drop due to low incremental value:
  - if secondary-only panels rarely show retrospective fault or truth linkage,
  - so the lane mostly duplicates baseline attention or adds weak/noisy panels

## Scope Notes
- This is a non-core audit patch.
- Detector logic is unchanged.
- Current operator baseline is unchanged.
- Canonical truth template contract is unchanged.

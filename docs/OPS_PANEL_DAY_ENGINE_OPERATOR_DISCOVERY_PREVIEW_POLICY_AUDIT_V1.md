# OPS PANEL DAY ENGINE OPERATOR DISCOVERY PREVIEW POLICY AUDIT V1

## Why The Current Preview Is Valuable But Still Too Wide / Site-Skewed
- The current preview shows that secondary discovery can add retrospective fault-linked value beyond the baseline.
- But the full 12-panel discovery preview is still wider than what operators may want to scan every cycle.
- It is also site-skewed, with a large share of preview panels concentrated in one site.
- That means the next step is not more modeling, but a simpler question:
  - can we keep most of the retrospective value
  - while narrowing the preview and reducing site concentration?

## Why A Simple Current-State Preview Policy Is The Next Correct Step
- The value-panel rollup already gives a panel-level universe.
- Before integrating anything more tightly into workflow, the most practical test is a small set of deterministic current-state policies:
  - score threshold
  - top-K per site
  - score threshold plus top-K per site
- This keeps the preview policy easy to explain, stable to audit, and operationally cheap.

## Why Future References Are Evaluation-Only Here
- Future fault / truth-linked reference is used only to measure whether a narrower policy would have kept useful panels retrospectively.
- It is not used to select panels in the policy itself.
- Selection is restricted to current-state fields, mainly representative electrical severity and within-site rank.

## What Results Mean Operationally
- Integrate a narrower discovery preview into operator workflow:
  - if a small policy keeps at least most of the linked panels while materially reducing selected count or site skew
- Keep discovery preview analyst-only:
  - if narrowing loses too much linked coverage
  - or if the remaining policies still look too site-skewed or too wide to justify routine operator exposure

## Scope Notes
- This is a non-core operator-facing audit patch.
- Detector logic is unchanged.
- Existing baseline artifacts are unchanged.
- Canonical truth template contract is unchanged.

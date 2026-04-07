# OPS PANEL DAY ENGINE OPERATOR ATTENTION PLUS DISCOVERY PREVIEW V1

## Why The Secondary Discovery Value Lane Now Looks Worth Preserving
- The secondary discovery lane was not strong enough to replace the deterministic operator baseline.
- But later audits showed that its value-panel rollup can still add hidden panels with retrospective fault-linked evidence beyond the current attention baseline.
- That makes the lane useful enough to preserve as an auxiliary operator-facing artifact.

## Why Preview Integration Comes Before Baseline Replacement
- Replacing the baseline would be a stronger operational claim than the evidence supports today.
- The safer next step is to build a preview artifact that lets operators or analysts inspect:
  - current baseline queue rows
  - current baseline watch-now rows
  - non-overlapping secondary discovery value panels
- This keeps the baseline files unchanged while still making the potential additive coverage visible.
- The full preview remains unchanged even after the later policy audit.
- Instead, a second narrower preview variant is added side by side so we can compare:
  - the full exploratory preview
  - the recommended current-state narrowed preview
  before changing any operator-facing baseline behavior.

## Why Queue / Watch Remain The Primary Baseline
- Queue and watch-now rows remain the primary operator baseline because they are the existing, deterministic, already-adopted attention surfaces.
- The preview therefore preserves them first and only appends discovery panels that are not already present.
- In other words:
  - baseline rows stay authoritative
  - discovery rows are additive preview only
- This remains a preview-layer integration only:
  - detector logic is unchanged
  - scorer logic is unchanged
  - baseline artifacts are unchanged

## How To Interpret `secondary_value_panel` Rows
- `secondary_value_panel` means:
  - a panel from the rolled-up secondary discovery value lane
  - not already present in the current operator attention baseline
- These rows should be read as:
  - hidden-value candidates worth side review
  - not automatic replacements for queue or watch-now attention
- Retrospective future fault / truth flags remain reference-only context:
  - useful for audit and calibration
  - not an online input to the preview creation logic

## Why The Current Narrow Recommendation Is Score-Threshold Based
- The completed preview policy audit found that a simple threshold on `representative_electrical_core_minus_broadshape_050` preserved most linked retrospective value while trimming preview load.
- That means the currently recommended narrow preview is deterministic and electrical-score based, not a new learned selector.
- The narrow preview should therefore be interpreted as:
  - the same operator-facing preview concept
  - with a stricter discovery append policy
  - not as a replacement for queue/watch baseline attention

## Why Panel-Level Discovery Preview Was Still Too Wide
- Even after panel rollup and score-threshold narrowing, one active site could still contribute many separate secondary rows.
- That keeps operator load higher than necessary and can still make the discovery side of the preview feel site-skewed.

## Why Cluster Rollup Looked Promising
- The cluster rollup audit showed that nearby secondary discovery value panels can be compressed into site-time clusters with a meaningful reduction in row count.
- That makes cluster compression a good side-by-side operator preview candidate:
  - same baseline queue/watch rows
  - same discovery evidence family
  - but fewer appended discovery items

## Why Cluster Preview Is Added Side By Side
- The cluster preview is added next to the existing panel-based previews instead of replacing them immediately.
- This keeps three operator-facing views available for comparison:
  - the original full panel preview
  - the narrowed panel preview
  - the new cluster preview
- The baseline attention files themselves still do not change.

## How To Interpret `secondary_value_cluster` Rows
- `secondary_value_cluster` means:
  - a site-level temporal cluster built from secondary discovery value panels
  - compressed from nearby representative intervals within the same site
- These rows should be read operationally as:
  - a discovery burst worth one grouped review step
  - not as a detector or scorer change
  - not as a replacement for baseline queue/watch attention
- `member_overlap_with_attention_count` is a validation field only:
  - it checks whether any member panel inside the cluster is already present in current operator attention
  - expected current value is zero
  - but it is still reported explicitly for audit hygiene

## Scope Notes
- This is a non-core operator-facing patch.
- Detector logic is unchanged.
- Current baseline artifacts remain unchanged.
- Canonical truth template contract is unchanged.

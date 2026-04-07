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

## Why Queue / Watch Remain The Primary Baseline
- Queue and watch-now rows remain the primary operator baseline because they are the existing, deterministic, already-adopted attention surfaces.
- The preview therefore preserves them first and only appends discovery panels that are not already present.
- In other words:
  - baseline rows stay authoritative
  - discovery rows are additive preview only

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

## Scope Notes
- This is a non-core operator-facing patch.
- Detector logic is unchanged.
- Current baseline artifacts remain unchanged.
- Canonical truth template contract is unchanged.

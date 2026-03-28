# OPS_BASELINE_FREEZE_PACK_V1

## Purpose

This pack freezes the current baseline state into one decision artifact.

It consolidates:

- what is currently official,
- what is explicitly deferred,
- and what remains observation-only.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

## Why The Baseline Is Considered Frozen Now

The baseline is considered frozen when the active truth review queue is empty.

That means:

- the current official score boundary is already explicit,
- deferred high-actionability rows are already separated into a hold registry,
- and the remaining precursor line has already been reduced to a conservative decision posture.

At that point, the team no longer needs to keep the baseline "open" just to remember what was decided.

## Why Gangui Deferred Rows Do Not Invalidate The Current Score

The deferred gangui rows are already excluded from official scoring.

That matters because this pack is not hiding unresolved rows inside the benchmark.
It is doing the opposite:

- the current score still reflects only the rows that are officially in scope,
- the deferred rows remain visible,
- and their status is explicitly recorded as hold, not solved.

So the existence of deferred gangui rows does not invalidate the current score.
They are outside the score by design, not silently contaminating it.

## Why The Global Precursor Addon Is Still Not Adopted

The precursor decision line still says observation, not adoption.

That means the baseline keeps:

- the current official score as-is,
- no global precursor addon,
- and only the already-approved decision posture from the precursor pack.

This freeze artifact records that state so it does not need to be reinterpreted later.

## Why Conalog Keeps Only A Site-Specific Precursor Note

`conalog` still has the only defensible site-specific precursor note.

That is a local interpretive note, not a global addon.

This distinction matters:

- the baseline does not promote precursor behavior into official prediction output,
- but it also does not discard the narrow site-specific evidence that remains useful for interpretation.

So the frozen state is:

- no global precursor addon,
- keep the `conalog` site-specific note only.

## Why This Means The Team Can Move To Another Workstream Safely

This artifact gives one place to read the current decision state:

- official F1 values,
- scored and deferred counts,
- deferred hold status by site,
- precursor posture,
- and next-workstream recommendation.

Because those decisions are now captured together, the team can switch topics without reopening the same governance questions from memory.

In other words:

- the score meaning is preserved,
- the deferred rows are preserved,
- the observational precursor posture is preserved,
- and the next workstream does not need to guess what the baseline currently means.

## Outputs

- `_share/baseline_freeze_summary_v1.csv`
- `_share/baseline_freeze_sites_v1.csv`
- `_share/baseline_freeze_decisions_v1.csv`

# OPS_BASELINE_REGRESSION_GUARD_V1

## Purpose

This patch guards the frozen baseline against unintended drift while future workstreams run.

It compares:

- the frozen baseline pack,
- against the current live artifacts that define the same baseline state today.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

It only reports whether the frozen baseline is still preserved.

## Why The Baseline Was Frozen

The baseline was frozen because the current official state had already been made explicit:

- official F1 values were fixed in the baseline freeze pack,
- score scope was made explicit,
- deferred gangui high-actionability rows were moved to hold,
- and the precursor line had already been reduced to an observation-only posture with a `conalog` site note only.

Once the active review queue reached zero, that state was stable enough to freeze.

## Why This Guard Exists Before Switching Topics

Freezing the baseline is only useful if future work does not accidentally move it.

That is the point of this guard.

It lets the team switch to another topic while still checking:

- whether the official metrics changed,
- whether score scope changed,
- whether deferred-hold counts changed,
- whether site status changed,
- and whether the frozen decision posture changed.

Without that comparison, a later workstream could alter the baseline quietly and nobody would know whether the drift was intended.

## What Kinds Of Drift Are Acceptable Versus Unacceptable

The guard marks drift as:

- `error` for metric, count, or status mismatches
- `warn` for recommendation-text mismatches

Interpretation:

- `error` means the frozen baseline state is no longer preserved in a material way
- `warn` means the numeric baseline may still be intact, but the decision wording or recommendation layer changed and should be reviewed deliberately

Examples of unacceptable drift:

- F1 changes
- official scored count changes
- deferred hold count changes
- active review queue becomes nonempty
- site status changes

Examples of reviewable but less severe drift:

- precursor recommendation wording changes
- `conalog` note wording changes
- next-workstream recommendation wording changes

## How To Respond If `drift_detected` Appears

Use `baseline_regression_guard_diffs_v1.csv` first.

That file tells you:

- which scope changed,
- which field changed,
- what the frozen value was,
- what the current value is,
- and whether the difference is `error` or `warn`.

Recommended response:

1. verify whether the drift was intentional
2. if not intentional, restore the live artifact that moved
3. if intentional, rerun the governance line deliberately and create a new frozen baseline pack instead of silently replacing the old one

The key rule is simple:

- do not silently redefine the frozen baseline by accident

## Outputs

- `_share/baseline_regression_guard_summary_v1.csv`
- `_share/baseline_regression_guard_sites_v1.csv`
- `_share/baseline_regression_guard_diffs_v1.csv`

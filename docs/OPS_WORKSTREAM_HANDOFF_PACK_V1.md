# OPS_WORKSTREAM_HANDOFF_PACK_V1

## Purpose

This pack turns the frozen baseline plus regression guard into one concise handoff artifact.

It exists so a different workstream can start without losing:

- the official baseline metrics,
- the scored versus deferred scope boundary,
- the precursor posture,
- the deferred-hold posture,
- and the reactivation conditions for the remaining open threads.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

## Why This Exists After Freeze Plus Guard

The freeze pack captured what the baseline officially means.

The regression guard then confirmed whether the live artifacts still match that frozen state.

Once both exist, the next operational need is simpler:

- give the next workstream one short artifact,
- keep the current baseline meaning intact,
- and avoid reopening old governance decisions from memory.

That is the job of this handoff pack.

## What Is Considered Official Baseline Now

The official baseline remains the frozen score state:

- the current strict and lenient F1 values,
- the current official scored counts,
- the current scored site statuses,
- and the current conservative precursor posture.

If the regression guard says `frozen_baseline_preserved`, this handoff pack treats that frozen state as still valid for downstream work.

## What Remains Deferred Or On Hold

The unresolved high-actionability rows remain on hold.

They are not moved back into active review by this patch, and they are not reintroduced into official scoring.

Their status remains:

- visible,
- deferred,
- and waiting for stronger field or O&M evidence before reactivation.

## What Can Be Safely Ignored In The Next Topic

The next workstream does not need to re-litigate the current baseline itself.

That means it can safely avoid reopening:

- the official baseline metrics,
- the current score-scope boundary,
- the decision not to adopt a global precursor addon,
- and the decision to keep only a `conalog` site-specific precursor note.

Those items are already captured here unless the regression guard later reports drift.

## What Must Be Rechecked Before Future Reporting

Before any future reporting or another topic switch, rerun the regression guard.

That is the main protective rule.

If the guard still says `frozen_baseline_preserved`, the handoff assumptions still hold.

If the guard reports drift, stop and inspect the moved artifact before presenting the baseline as unchanged.

## Outputs

- `_share/workstream_handoff_summary_v1.csv`
- `_share/workstream_handoff_sites_v1.csv`
- `_share/workstream_handoff_open_threads_v1.csv`

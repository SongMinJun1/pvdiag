# OPS_MERGE_READINESS_PACK_V1

## Purpose

This pack decides whether the current frozen workstream branch is ready to merge or archive before switching topics.

It combines:

- the frozen baseline handoff state,
- the current regression guard state,
- and the current git worktree hygiene state.

It does not change:

- official prediction output,
- official scoring logic,
- or canonical truth.

## Why Frozen Baseline Plus Handoff Is Not Enough By Itself

The frozen baseline pack and handoff pack tell us what the branch means.

They do not tell us whether the branch is operationally clean enough to merge or archive.

That missing piece is the live git worktree.

Without worktree hygiene, the branch could still carry:

- accidental uncommitted work,
- unrelated local dirt,
- or generated artifacts that make the branch look noisy even when the baseline itself is stable.

The merge-readiness pack closes that gap.

## What The Four Worktree Classes Mean

`generated_share_artifact`

- files under `_share/`
- usually generated outputs
- useful to inspect, but they should not block topic switch by themselves

`known_unrelated_dirty`

- specific known local dirt outside the current merge decision
- currently limited to the site-event-dataset builder and its smoke test
- they should be tracked separately, not used to block this branch by default

`current_workstream_uncommitted`

- uncommitted files under `docs/` or `research/prognostics/`
- these are the most important blocker class for this patch
- if they are present, the current workstream is still locally open

`other_worktree_change`

- anything else in the repo that does not match the three classes above
- treat this as a hold until someone confirms what changed and why

## When The Branch Is Truly Safe To Merge Or Archive

The branch is truly safe when:

- the regression guard still says `frozen_baseline_preserved`
- the handoff still says `safe_to_switch_topic`
- and the worktree has no remaining local changes

If only generated `_share/` files or the known unrelated dirty files remain, the branch can still be considered practically ready after those are explicitly ignored.

If current workstream dirt or other unexplained dirt remains, stop and clean that up first.

## Why Generated `_share` Artifacts And Known Unrelated Dirty Files Should Not Block By Themselves

Generated `_share` files are expected byproducts of running the packaging scripts.

Known unrelated dirty files are already outside the scope of this branch decision.

Neither class should force the team to keep the current topic open.

The point is not to pretend those files do not exist.

The point is to separate:

- real merge blockers,
- from noisy but understood residue.

That separation is what allows a clean topic switch without losing governance discipline.

## Outputs

- `_share/merge_readiness_summary_v1.csv`
- `_share/merge_readiness_worktree_v1.csv`
- `_share/merge_readiness_actions_v1.csv`

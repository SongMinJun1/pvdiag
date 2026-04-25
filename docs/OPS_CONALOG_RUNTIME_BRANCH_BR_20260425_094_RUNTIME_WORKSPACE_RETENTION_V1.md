<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_094_RUNTIME_WORKSPACE_RETENTION_V1

## Purpose
- Record the runtime workspace retention patch added after BR-093.
- Prevent tri-site validation workspaces from accumulating multi-GB duplicate `data/<site>/out` copies under `/private/tmp`.
- Keep reproducible result artifacts while treating regenerated site/workspace data copies as disposable.
- Keep this branch packaging/operations-only:
  - no `panel_day_engine.py` algorithm change
  - no runtime verdict change
  - no truth label change
  - no threshold tuning approval
  - no operator-facing semantic change

## Problem
- A tri-site reuse run copies existing `data/<site>/out` into `output_root/sites/<site>/output`.
- The raw-only chain stages the same site outputs again under `output_root/raw_only_chain_workspace/data/<site>/out`.
- In the current baseline, the copied site outputs are large:
  - `data/conalog/out`: about `2.7G`
  - `data/gangui/out`: about `482M`
  - `data/ktc_ess/out`: about `383M`
- One tri-site runtime workspace can therefore reach about `7.0G` even though the final `result/` outputs are about `19M`.
- Repeated `/private/tmp` runs can accumulate hundreds of GB if those reproducible workspace copies are retained.

## Implementation
- runner:
  - `release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py`
- docs:
  - `release/conalog_full_runtime_v1/README.md`
- new option:
  - `--workspace-retention full`
  - `--workspace-retention result-only`
- default:
  - `full`
  - preserves previous behavior unless explicitly changed

## `result-only` Retention Contract
- Keep:
  - `result/`
  - `shadow_compare_v1.json`
  - `run_metadata_v1.json`
  - `workspace_cleanup_v1.json`
  - chain `_share` outputs when present
- Remove:
  - `sites/`
  - `live_chain_workspace/data`
  - `raw_only_chain_workspace/data`
- Rationale:
  - removed paths are reproducible copies of existing site outputs
  - kept paths contain the result/report/share artifacts needed for review and handoff

## Real Result
- Fresh result-only validation workspace:
  - output root: `/private/tmp/conalog_workspace_retention_result_only_check`
  - final size: about `20M`
  - cleanup removed estimate: about `7.01GiB`
  - raw-only chain status: `completed`
- Existing recovery workspace cleanup:
  - output root: `/private/tmp/conalog_mlpe_seed_expand_check`
  - before cleanup: about `7.0G`
  - after cleanup: about `19M`
  - cleanup report: `/private/tmp/conalog_mlpe_seed_expand_check/workspace_cleanup_v1.json`

## Safety Boundary
- This patch changes only post-run retention behavior.
- Default behavior remains `full`.
- `result-only` does not alter how result CSV/XLSX/MD artifacts are built.
- `result-only` should not be used when a reviewer explicitly needs full staged `sites/` or workspace `data/` copies for forensic inspection.
- If full staged copies are needed, rerun with `--workspace-retention full`.

## Decision
- Accept `--workspace-retention result-only` as the preferred local validation mode when the goal is result review, not full workspace forensics.
- Keep the default as `full` to avoid surprising existing operators or wrappers.
- Treat `workspace_cleanup_v1.json` as the audit record for what was removed.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py
python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/conalog_workspace_retention_dryrun_check --sites conalog,gangui,ktc_ess --prefer-existing-site-outs on --workspace-retention result-only --dry-run
python3 release/conalog_full_runtime_v1/package/app/run_full_algorithm_pack.py --data-root /Users/b9gc/pvdiag/data --output-root /private/tmp/conalog_workspace_retention_result_only_check --sites conalog,gangui,ktc_ess --prefer-existing-site-outs on --workspace-retention result-only
du -sh /private/tmp/conalog_workspace_retention_result_only_check /private/tmp/conalog_mlpe_seed_expand_check
```

## Commit
- `a73f9f99 Add runtime workspace retention option`

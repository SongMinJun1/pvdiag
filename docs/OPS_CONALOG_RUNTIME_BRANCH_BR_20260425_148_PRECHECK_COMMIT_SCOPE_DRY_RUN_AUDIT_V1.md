<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_148_PRECHECK_COMMIT_SCOPE_DRY_RUN_AUDIT_V1

## Purpose
- Build a dry-run commit-scope audit for the current BR-126..143 runway work.
- Keep this as bookkeeping only:
  - no staging
  - no commit
  - no push
  - no canonical truth write
  - no truth intake write
  - no threshold patch
  - no `pv_ae/panel_day_engine.py` patch
  - no operator-facing behavior change

## Why This Exists
- BR-144 and downstream BR-145..BR-150 are still blocked by absent real replay, selected rule, shadow result, and prepatch-ready candidate.
- The remaining safe work without real data is scope control, dirty-state reduction, and handoff/readiness bookkeeping.
- This precheck answers whether the current dirty tree is a coherent commit candidate or contains dangerous/unrelated files.

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_commit_scope_dry_run_audit_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_commit_scope_dry_run_audit_v1.py`

## Classification Policy
| role family | policy |
| --- | --- |
| `runtime_control_doc` | include if reviewed |
| `runtime_branch_doc_or_matrix` | include if reviewed |
| `field_trial_contract_builder` | include if matching smoke passes |
| `field_trial_contract_smoke` | include if smoke passes |
| `panel_engine_source` | exclude from this scope; BR-144 authorization required |
| `large_site_data` | exclude from commit |
| `generated_release_artifact` | exclude unless a release-sync branch explicitly owns it |
| `unclassified_dirty_path` | hold for manual review |

## Outputs
- `/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check/mlpe_field_trial_commit_scope_dry_run_files_v1.csv`
- `/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check/mlpe_field_trial_commit_scope_dry_run_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check/mlpe_field_trial_commit_scope_dry_run_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check/mlpe_field_trial_commit_scope_dry_run_note_v1.md`
- `/private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check/mlpe_field_trial_commit_scope_dry_run_v1.json`

## Real Result
- dirty files: `43`
- include-candidate files: `43`
- tracked modified files: `1`
- untracked files: `42`
- runtime doc/control files: `25`
- field-trial contract builders: `9`
- field-trial contract smokes: `9`
- risk files: `0`
- issue rows: `0`
- engine source dirty: `0`
- large data dirty: `0`
- release generated dirty: `0`
- unclassified dirty: `0`
- deleted/renamed dirty: `0`
- commit-scope ready flag: `1`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Fixture Result
- Synthetic good fixture:
  - dirty files: `4`
  - risk files: `0`
  - issue rows: `0`
  - commit-scope ready flag: `1`
- Synthetic bad fixture:
  - dirty files: `4`
  - risk files: `4`
  - issue rows: `4`
  - commit-scope ready flag: `0`
  - detects dirty `pv_ae/panel_day_engine.py`, `data/<site>/raw`, generated release JSON, and unclassified paths

## Safety Boundary
- This precheck does not mark BR-148 complete in the BR-128..150 queue.
- Official BR-148 still waits for BR-147 release/handoff sync, which itself waits for BR-144..146.
- This precheck only says the current BR-126..143 dirty set is cleanly classifiable and does not contain panel-engine source, large data, generated release JSON drift, or unclassified files.
- Do not use `git add .`; use the file manifest if staging is later requested.

## Ordered Next Path
1. Keep BR-144 blocked until replay, selected rule, shadow result, and BR-143 prepatch-ready candidate exist.
2. If the user wants repository cleanup next, use this audit to stage only the listed include-candidate files.
3. If the user supplies real KTC ESS capture/labels, resume BR-130 and downstream real-data gates.
4. If no real data is available, the next safe action is a readiness/handoff audit from the current blocked state, not an engine patch.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_commit_scope_dry_run_audit_v1.py research/prognostics/smoke_test_mlpe_field_trial_commit_scope_dry_run_audit_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_commit_scope_dry_run_audit_v1.py
python3 research/prognostics/build_mlpe_field_trial_commit_scope_dry_run_audit_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --output-dir /private/tmp/mlpe_field_trial_commit_scope_dry_run_br148_check
```

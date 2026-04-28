<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260428_153_STALE_WORKTREE_REPRO_PATH_CLEANUP_V1

## Purpose
- Remove stale `postmerge_j` worktree references from BR-095..BR-150 repro docs.
- Keep historical evidence outputs intact; this cleanup changes checkout location guidance only.

## Change
- Replaced stale fixed worktree paths in repro commands with `--repo-root "$(pwd)"`.
- This keeps the commands runnable from the current checkout without binding future users to one deleted/local worktree.
- The BR-126 workspace table now records the current checkout as `"$(pwd)"` instead of the old transient worktree path.

## Observed Effect
- Path portability audit total matches: `1998 -> 1954`.
- `worktree_absolute` high-risk matches: `45 -> 0`.
- Remaining path findings are medium-risk `private_tmp 1330` evidence references and `repo_absolute 624` references; those need separate triage because many are historical provenance pointers.

## Repro Commands
```bash
git status --short --branch
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/pvdiag_repo_path_portability_audit_worktree_docs_check_v1
python3 -m py_compile pv_ae/panel_day_engine.py
git diff --check
```

## Decision
- This patch does not change algorithm behavior or runtime outputs.
- This patch is a handoff/readability cleanup so future repro commands point at the active checkout rather than a stale worktree.

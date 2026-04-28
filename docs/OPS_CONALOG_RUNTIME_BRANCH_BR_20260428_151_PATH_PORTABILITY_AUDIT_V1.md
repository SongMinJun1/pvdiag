<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260428_151_PATH_PORTABILITY_AUDIT_V1

## Purpose
- Add a reproducible guard for local absolute paths and volatile temp-output references after the runtime metadata stability fix.
- Keep this as an audit-only cleanup lane: no `pv_ae/panel_day_engine.py` behavior change, no production rerun, and no bulk rewrite of historical evidence pointers.

## Why This Exists
- The post-merge audit found many repo-local absolute paths, transient worktree paths, and temp-output references.
- Some are valid historical evidence/repro pointers, but transient worktree paths and live-command absolute repo paths can confuse future handoff work.
- The safe move is to make the surface measurable first, then triage only the rows that have a stable replacement.

## Added Guard
- Builder: `research/prognostics/build_repo_path_portability_audit_v1.py`
- Smoke: `research/prognostics/smoke_test_repo_path_portability_audit_v1.py`
- Output files:
  - `repo_path_portability_detail_v1.csv`
  - `repo_path_portability_summary_v1.csv`
  - `repo_path_portability_file_kind_v1.csv`
  - `repo_path_portability_note_v1.md`
  - `repo_path_portability_summary_v1.json`

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir "${TMPDIR:-/tmp}/pvdiag_repo_path_portability_audit_v1"
git diff --check
```

## Interpretation Rule
- `repo_absolute`: prefer repo-relative paths or explicit `--repo-root` arguments when the reference is a live command or stable metadata.
- `worktree_absolute`: treat as the highest cleanup priority because worktree paths are intentionally transient.
- `private_tmp`: keep if it is a historical evidence pointer with a recorded repro command; replace only when the artifact has a stable package/doc output.

## Decision
- This branch does not claim algorithm performance improvement.
- This branch makes future cleanup safer by turning scattered absolute-path concerns into a reproducible audit table.

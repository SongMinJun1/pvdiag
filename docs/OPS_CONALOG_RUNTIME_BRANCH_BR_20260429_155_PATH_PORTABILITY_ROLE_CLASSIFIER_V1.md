<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_155_PATH_PORTABILITY_ROLE_CLASSIFIER_V1

## Purpose
- Refine the BR-151 path portability audit so remaining findings are separated by role, priority, and next action.
- Keep this as an audit/reporting patch only: no `pv_ae/panel_day_engine.py` behavior change, no production semantic change, and no large data committed.

## Change
- `repo_path_portability_detail_v1.csv` now includes:
  - `match_role`
  - `triage_priority`
  - `triage_action`
- `repo_path_portability_summary_v1.csv` and JSON now include counts for those new axes.
- The markdown note now prints `Triage Priorities` and `Triage Roles` so the remaining path debt can be handled without bulk rewriting evidence history.

## Observed Effect
- Path portability audit total matches after this patch: `1934`.
- `worktree_absolute`: `0`.
- `repo_absolute`: `602`.
- `private_tmp`: `1332`.
- Triage split:
  - `p1_live_temp_reference`: `249`
  - `p2_historical_evidence_reference`: `1083`
  - `p2_historical_repro_reference`: `156`
  - `p3_doc_reference`: `446`

## Interpretation
- There is no remaining `p0_stale_worktree` class in the current checkout.
- The only non-doc active cleanup class is `p1_live_temp_reference`, currently `249` research/prognostics rows that should be reviewed before replacing defaults with CLI output dirs or temp-file fixtures.
- The bulk of the remaining rows are historical evidence/repro references in docs; they should not be blindly rewritten unless a stable replacement artifact and repro command are recorded.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/pvdiag_repo_path_portability_role_classifier_check_v3
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- Use BR-155 output as the next cleanup triage map.
- Next patch candidate: review only `p1_live_temp_reference` rows and decide which builder defaults should move to explicit CLI output dirs.
- Do not rewrite `p2_historical_evidence_reference`, `p2_historical_repro_reference`, or `p3_doc_reference` rows unless the touched doc is already being refreshed for a current handoff.

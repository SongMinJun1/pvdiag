<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260428_152_PATH_PORTABILITY_SELF_NOISE_FIX_V1

## Purpose
- Tighten the BR-151 path portability audit so it does not count its own regex literals, note template examples, or smoke-test fixture strings as real repo portability risk.
- Keep the guard audit-only: no engine behavior change, no production result change, and no bulk rewrite of historical evidence references.

## Fix
- Add a short `pp-self` skip marker for intentional scanner/test literals.
- Update the smoke fixture to prove marked self-noise rows are not emitted while unmarked fixture repo/worktree/temp paths are still detected.
- Replace the BR-151 repro command's fixed worktree path with `--repo-root "$(pwd)"` so the doc no longer depends on one local checkout path.

## Expected Effect
- The high-risk `worktree_absolute` count should drop by scanner-owned literals.
- Remaining worktree rows should now be closer to real historical or stale handoff references, not the audit tool looking at itself.
- Observed check: total matches `2011 -> 1998`, `private_tmp 1334 -> 1329`, `repo_absolute 627 -> 624`, `worktree_absolute 50 -> 45`.

## Repro Commands
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_repo_path_portability_audit_v1.py research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/smoke_test_repo_path_portability_audit_v1.py
python3 research/prognostics/build_repo_path_portability_audit_v1.py --repo-root "$(pwd)" --output-dir "${TMPDIR:-/tmp}/pvdiag_repo_path_portability_audit_self_noise_check_v1"
git diff --check
```

## Decision
- This patch improves the measurement instrument only.
- It does not assert that any existing historical `/private/tmp` evidence pointer should be deleted.

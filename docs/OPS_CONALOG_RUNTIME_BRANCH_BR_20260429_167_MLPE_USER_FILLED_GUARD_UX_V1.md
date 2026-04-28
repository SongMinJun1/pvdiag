<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_167_MLPE_USER_FILLED_GUARD_UX_V1

## Purpose
- BR-166 closed generated/chain input dependencies at `0` rows.
- The remaining `7` MLPE input dependency rows are user-filled inputs that must stay fail-closed.
- BR-167 improves operator/developer error guidance without weakening the guard.

## Guarded Inputs
| input kind | scripts | explicit flag |
|---|---:|---|
| returned capture | 2 | `--returned-capture` |
| final label input | 3 | `--label-input` |
| reviewed preflight checklist | 1 | `--reviewed-checklist` |
| truth-seed reviewer decision input | 1 | `--decision-input` |

## Boundary
- Do not remove the `7` audit rows by treating user-filled templates as safe generated artifacts.
- Do not loosen `--allow-user-filled-default`; it remains fixture/regression-only.
- Do not change truth intake, threshold replay, engine patch, or canonical truth write approvals.
- Do not edit `pv_ae/panel_day_engine.py`.

## UX Change
- A blocked default now explains:
  - which user-filled input is blocked,
  - why the default template path is refused as real evidence,
  - which explicit CLI flag should be supplied,
  - that `--allow-user-filled-default` is fixture/regression-only,
  - the exact default path that was refused.

## Validation
```bash
python3 -m py_compile \
  pv_ae/panel_day_engine.py \
  research/prognostics/mlpe_field_trial_user_input_contract_v1.py \
  research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py

python3 research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py

python3 research/prognostics/build_repo_path_portability_audit_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_user_filled_guard_ux_br167_check"

python3 research/prognostics/build_mlpe_field_trial_generated_dependency_review_v1.py \
  --repo-root "$(pwd)" \
  --output-dir "${TMPDIR:-/tmp}/mlpe_user_filled_guard_ux_dependency_review_br167_check"

python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
```

## Expected Counts
- Generated dependency review remains `0`.
- Path portability dependency contracts still show `mlpe_user_filled_input = 7`.
- This is intentional: these rows are guarded human inputs, not generated artifact dependencies.

## Decision
- BR-167 is a guard usability patch, not a portability count-elimination patch.
- The next cleanup branch can review MLPE output defaults separately.

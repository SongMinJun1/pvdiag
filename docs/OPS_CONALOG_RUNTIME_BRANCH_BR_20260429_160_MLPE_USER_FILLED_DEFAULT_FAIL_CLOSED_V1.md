<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260429_160_MLPE_USER_FILLED_DEFAULT_FAIL_CLOSED_V1

## Purpose
- Close BR-159's highest-risk dependency bucket: `mlpe_user_filled_input`.
- Prevent stale temp templates from being silently reused as if they were real field-trial operator/reviewer inputs.
- Keep this scoped to MLPE field-trial support builders; no `pv_ae/panel_day_engine.py` runtime semantic change.

## Change
- Added `research/prognostics/mlpe_field_trial_user_input_contract_v1.py`.
- Added `--allow-user-filled-default` to the 7 MLPE field-trial scripts that still have user-filled temp defaults.
- The 7 scripts now refuse their user-filled default path unless fixture/regression use is explicitly declared.
- Added `smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py` to verify all 7 scripts fail closed on implicit user-filled defaults.

## Guarded Inputs
| input kind | scripts guarded | behavior |
|---|---:|---|
| returned capture | 2 | default capture template cannot be used silently as returned field capture |
| final label input | 3 | default label template cannot be used silently as real labels |
| reviewed preflight checklist | 1 | default unchecked checklist cannot be used silently as reviewed checklist |
| truth-seed reviewer decision | 1 | default decision template cannot be used silently as reviewer decision |

## Expected Effect
- Running the guarded scripts with no explicit user-filled input now stops before reading stale temp artifacts.
- Running with an explicit real/fixture input path still works.
- Running with default fixture material requires `--allow-user-filled-default`, making the intent visible in logs and repro commands.

## Validation
```bash
git status --short --branch
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/mlpe_field_trial_user_input_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py research/prognostics/build_mlpe_field_trial_capture_return_validator_v1.py research/prognostics/build_mlpe_field_trial_capture_return_evidence_resolver_v1.py research/prognostics/build_mlpe_field_trial_final_label_validator_v1.py research/prognostics/build_mlpe_field_trial_label_to_truth_gate_v1.py research/prognostics/build_mlpe_field_trial_real_label_intake_runbook_v1.py research/prognostics/build_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py research/prognostics/build_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_user_filled_default_guard_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_evidence_resolver_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_final_label_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_label_to_truth_gate_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_real_label_intake_runbook_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_intake_preflight_review_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_validator_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_reviewer_decision_schema_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_review_packet_v1.py
python3 research/prognostics/smoke_test_conalog_full_runtime_pack_v1.py
git diff --check
```

## Decision
- User-filled inputs are not portable defaults.
- Template/schema defaults may still be package-contract candidates, but user-filled defaults must either be explicit real paths or explicit fixture/regression paths.
- Next patch candidate: reduce the remaining MLPE `mlpe_template_or_schema_input` defaults by moving shipped templates/schemas behind package-relative contract paths.
- Do not claim truth, threshold, performance, or engine improvement from this branch.

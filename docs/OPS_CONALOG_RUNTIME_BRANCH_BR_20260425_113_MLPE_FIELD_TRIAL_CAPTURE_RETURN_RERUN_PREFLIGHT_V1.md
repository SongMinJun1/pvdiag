<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_113_MLPE_FIELD_TRIAL_CAPTURE_RETURN_RERUN_PREFLIGHT_V1

## Purpose
- Add a preflight gate before rerunning BR-103 readiness and BR-106 handoff on returned capture rows.
- Combine BR-111 validation and BR-112 evidence resolution into one rerun decision.
- Keep this branch rerun-preflight-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_capture_return_rerun_preflight_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_capture_return_rerun_preflight_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv` | BR-111 returned-capture validation |
| `/private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_v1.csv` | BR-112 file-level evidence resolution |

## Outputs
- `/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_note_v1.md`
- `/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_v1.json`

## Real Result
- rows: `14`
- waiting rows: `14`
- rerun-allowed rows: `0`
- validation-failed rows: `0`
- required evidence problem rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke cases: waiting, ready, validation failure, evidence failure.
- Only the complete returned-ready case opens:
  - rows: `4`
  - waiting rows: `1`
  - rerun-allowed rows: `1`
  - validation-failed rows: `1`
  - required evidence problem rows: `1`
  - truth intake allowed sum: `0`

## Interpretation
- Current 실증 state still has no returned real capture, so no row should rerun readiness/handoff yet.
- The gate is not over-blocking: the smoke matrix proves a complete returned-ready row can open.
- The gate is not under-blocking: validation failures and required evidence failures remain blocked.

## Safety Boundary
- `readiness_handoff_rerun_allowed=1` is only permission to rerun BR-103/BR-106.
- It is not final adjudication, truth intake, threshold approval, or engine patch approval.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep current rows waiting until real capture returns.
2. After real capture returns, pass through BR-111 and BR-112 first.
3. Use BR-113 to decide which rows may rerun BR-103 readiness and BR-106 handoff.
4. Only after those gates pass should final adjudication packet generation begin.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_capture_return_rerun_preflight_v1.py research/prognostics/smoke_test_mlpe_field_trial_capture_return_rerun_preflight_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_capture_return_rerun_preflight_v1.py
python3 research/prognostics/build_mlpe_field_trial_capture_return_rerun_preflight_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --validation /private/tmp/mlpe_field_trial_capture_return_validator_br111_check/mlpe_field_trial_capture_return_validation_v1.csv --evidence-resolution /private/tmp/mlpe_field_trial_capture_return_evidence_resolver_br112_check/mlpe_field_trial_capture_return_evidence_resolution_v1.csv --output-dir /private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_110_MLPE_FIELD_TRIAL_REAL_CAPTURE_INTAKE_WATCHLIST_V1

## Purpose
- Convert the operator intake checklist, adjudication handoff guard, and BR-109 dry-run gate into a real-capture intake watchlist.
- Keep the next dependency explicit: collect real field-capture metadata/evidence before final adjudication and truth intake.
- Keep this branch watchlist-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_real_capture_intake_watchlist_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_watchlist_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_checklist_v1.csv` | operator checklist |
| `/private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_v1.csv` | current planned-row handoff guard |
| `/private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv` | pre-adjudication plumbing gate |

## Outputs
- `/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_note_v1.md`
- `/private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check/mlpe_field_trial_real_capture_intake_watchlist_v1.json`

## Real Result
- rows: `14`
- dry-run gate passed flag: `1`
- real capture required rows: `14`
- handoff allowed rows: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Interpretation
- The plumbing is ready, but the real field-capture dependency is still open.
- All 14 planned rows remain collection tasks.
- This is the correct next state before final labels exist.

## Safety Boundary
- Watchlist rows are collection tasks, not labels.
- `dry_run_gate_passed_flag=1` is not truth approval.
- `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Use the watchlist to collect exact real capture metadata/evidence.
2. Rerun BR-103, BR-106, and BR-109 after real capture rows are filled.
3. Open truth intake only after final labels are supplied externally.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_real_capture_intake_watchlist_v1.py research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_watchlist_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_real_capture_intake_watchlist_v1.py
python3 research/prognostics/build_mlpe_field_trial_real_capture_intake_watchlist_v1.py --repo-root "$(pwd)" --operator-checklist /private/tmp/mlpe_field_trial_operator_intake_br104_check/mlpe_field_trial_operator_intake_checklist_v1.csv --handoff-guard /private/tmp/mlpe_field_trial_adjudication_handoff_guard_br106_check/mlpe_field_trial_adjudication_handoff_guard_v1.csv --dry-run-gate-summary /private/tmp/mlpe_field_trial_pre_adjudication_dry_run_gate_br109_check/mlpe_field_trial_pre_adjudication_dry_run_gate_summary_v1.csv --output-dir /private/tmp/mlpe_field_trial_real_capture_intake_watchlist_br110_check
```

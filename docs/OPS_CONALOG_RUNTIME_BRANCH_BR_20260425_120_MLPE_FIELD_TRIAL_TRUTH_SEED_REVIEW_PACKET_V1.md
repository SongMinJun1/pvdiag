<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_120_MLPE_FIELD_TRIAL_TRUTH_SEED_REVIEW_PACKET_V1

## Purpose
- Convert BR-119/BR-117 `truth_gate_ready_flag=1` rows into a sidecar truth-seed review packet.
- Keep BR-117 blocked rows in a separate blocked-reference table.
- Keep this branch packet-only:
  - no canonical truth writes
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_seed_review_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_seed_review_packet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/mlpe_field_trial_real_label_intake_runbook_summary_v1.csv` | BR-119 stage summary / fixture mismatch guard |
| `/private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check/br117_label_to_truth_gate/mlpe_field_trial_label_to_truth_gate_v1.csv` | BR-117 gate output produced by BR-119 |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_blocked_rows_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check/mlpe_field_trial_truth_seed_review_packet_v1.json`

## Real Result
- fixture mismatch rows: `0`
- source gate rows: `0`
- source truth-gate-ready rows: `0`
- source truth-gate-blocked rows: `0`
- truth-seed review packet rows: `0`
- positive truth-seed review rows: `0`
- negative truth-seed review rows: `0`
- blocked before truth-seed review rows: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke chain:
  - BR-119 synthetic label intake with one confirmed positive, one negative control, and one probable row
  - BR-120 packet builder over the resulting BR-119 output
- Result:
  - fixture mismatch rows: `0`
  - source gate rows: `3`
  - source truth-gate-ready rows: `2`
  - source truth-gate-blocked rows: `1`
  - truth-seed review packet rows: `2`
  - positive truth-seed review rows: `1`
  - negative truth-seed review rows: `1`
  - blocked before truth-seed review rows: `1`
  - canonical truth/truth intake/threshold/engine approval sums: `0`

## Interpretation
- Current real state still has no real KTC ESS label rows, so the real packet is empty.
- The smoke confirms the split:
  - confirmed positive and negative-control rows enter sidecar review packet
  - probable rows stay in the blocked-reference table
- A sidecar truth-seed review packet row is still not canonical truth.

## Safety Boundary
- `truth_seed_review_packet_rows` are review candidates only.
- `canonical_truth_write_allowed`, `truth_intake_allowed`, `threshold_patch_allowed`, and `engine_patch_allowed` remain `0`.
- Canonical truth is not overwritten.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-120 as the sidecar packet generator for future BR-119 gate-ready rows.
2. When real KTC ESS labels produce packet rows, review packet rows manually before any truth intake.
3. Build the next branch as a sidecar truth-seed reviewer decision schema, not a canonical truth writer.
4. Keep threshold replay and engine patches blocked until labeled truth and regression pressure gates pass separately.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_seed_review_packet_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_seed_review_packet_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_seed_review_packet_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_seed_review_packet_v1.py --repo-root "$(pwd)" --runbook-dir /private/tmp/mlpe_field_trial_real_label_intake_runbook_br119_check --output-dir /private/tmp/mlpe_field_trial_truth_seed_review_packet_br120_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_114_MLPE_FIELD_TRIAL_RETURNED_CAPTURE_ADJUDICATION_PACKET_V1

## Purpose
- Build final-adjudication packet rows only for BR-113 rows allowed to rerun readiness/handoff.
- Keep current waiting rows blocked instead of creating empty or misleading final-review tasks.
- Keep this branch packet-only:
  - no new truth labels
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_returned_capture_adjudication_packet_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_returned_capture_adjudication_packet_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_v1.csv` | BR-113 rerun preflight |

## Outputs
- `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_v1.csv`
- `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_blocked_v1.csv`
- `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_note_v1.md`
- `/private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check/mlpe_field_trial_returned_capture_adjudication_packet_v1.json`

## Real Result
- packet rows: `0`
- blocked rows: `14`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

## Smoke Matrix Result
- Smoke cases: ready, waiting, evidence-blocked.
- Only the BR-113 allowed case becomes an adjudication packet row:
  - packet rows: `1`
  - blocked rows: `2`
  - truth intake allowed sum: `0`
  - threshold patch allowed sum: `0`
  - engine patch allowed sum: `0`

## Interpretation
- Current 실증 state has no returned-ready rows, so no final-adjudication packet should exist yet.
- The packet builder is not over-blocking: a complete BR-113 allowed row opens in smoke.
- The packet builder is not under-blocking: waiting/evidence-blocked rows remain outside the packet.

## Safety Boundary
- Packet rows contain blank reviewer fields by design.
- External 실증/final review must fill fault family, subtype, confidence, and clearance fields.
- Packet generation is not truth intake, threshold approval, or engine patch approval.
- `panel_day_engine.py` remains untouched.

## Ordered Next Path
1. Keep BR-114 packet rows at `0` until BR-113 allows returned rows.
2. When packet rows exist, collect external reviewer labels into a separate label-intake schema.
3. Do not promote labels to truth or thresholds without a separate truth-intake gate.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_returned_capture_adjudication_packet_v1.py research/prognostics/smoke_test_mlpe_field_trial_returned_capture_adjudication_packet_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_returned_capture_adjudication_packet_v1.py
python3 research/prognostics/build_mlpe_field_trial_returned_capture_adjudication_packet_v1.py --repo-root "$(pwd)" --preflight /private/tmp/mlpe_field_trial_capture_return_rerun_preflight_br113_check/mlpe_field_trial_capture_return_rerun_preflight_v1.csv --output-dir /private/tmp/mlpe_field_trial_returned_capture_adjudication_packet_br114_check
```

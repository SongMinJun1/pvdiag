<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_139_TRUTH_REPLAY_SCORECARD_CONTRACT_V1

## Purpose
- Build the truth replay scorecard contract before BR-140 real replay execution.
- Define how baseline vs candidate replay must be evaluated once sidecar truth package rows exist.
- Keep this branch scorecard-contract-only:
  - no truth intake write
  - no canonical truth write
  - no threshold replay approval
  - no `panel_day_engine.py` patch
  - no operator-facing verdict change
  - no performance improvement claim

## Implementation
- builder:
  - `research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py`
- smoke:
  - `research/prognostics/smoke_test_mlpe_field_trial_truth_replay_scorecard_contract_v1.py`

## Contract Groups
| scorecard group | required | role |
| --- | ---: | --- |
| `sidecar_truth_ready` | 1 | BR-138/BR-137 sidecar truth package event must be ready |
| `baseline_result_attached` | 1 | baseline replay row must join by `trial_event_id` |
| `candidate_result_attached` | 1 | candidate replay row must join by `trial_event_id` |
| `event_identity_join` | 1 | site/root/panel identity must not conflict across truth/baseline/candidate |
| `site_family_support` | 1 | support counts must be stratifiable by site and fault family |
| `precision_recall_f1_axis` | 1 | precision/recall/F1 may be computed only with truth labels and detection flags |
| `lead_time_axis` | 1 | early-warning claims require parseable alert date and fault date |
| `false_alarm_axis` | 1 | operator-load claims require negative-control/normal truth rows |
| `confidence_axis` | 1 | confidence claims require parseable confidence scores on detected rows |
| `unsupported_claim_guard` | 1 | performance improvement claim remains blocked in the contract stage |

## Outputs
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_contract_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_dry_run_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_metrics_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_contract_issues_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_contract_summary_v1.csv`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_contract_note_v1.md`
- `/private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check/mlpe_field_trial_truth_replay_scorecard_contract_v1.json`

## Real Result
- contract rows: `10`
- events: `0`
- truth-replay-scorecard-ready events: `0`
- scorecard rows: `0`
- scorecard passed rows: `0`
- scorecard blocked rows: `0`
- metric rows: `0`
- issue rows: `0`
- performance improvement claim allowed sum: `0`
- canonical truth write allowed sum: `0`
- truth intake allowed sum: `0`
- threshold patch allowed sum: `0`
- engine patch allowed sum: `0`

This is expected. The BR-137 sidecar package dry-run exists but has no ready sidecar truth events, so BR-140 real replay remains blocked.

## Smoke Fixture Result
- Missing input dry-run:
  - contract rows: `10`
  - blocked rows: `1`
  - issue rows: `1`
- Synthetic good fixture:
  - events: `2`
  - scorecard rows: `20`
  - truth-replay-scorecard-ready events: `2`
  - metric rows: `>=6`
  - candidate overall precision/recall: `1.0/1.0`
  - performance improvement claim allowed sum: `0`
- Synthetic bad fixture:
  - truth-replay-scorecard-ready events: `0`
  - detects missing/invalid replay axes including lead-time and write-boundary blockers

## Safety Boundary
- Passing this contract only means replay metrics can be computed.
- It does not prove performance improvement.
- It does not authorize threshold candidate selection.
- It does not create canonical truth labels.
- It does not patch `panel_day_engine.py`.
- Performance/write/approval fields remain locked to `0`.

## Ordered Next Path
1. Keep BR-140 blocked until real sidecar truth package rows exist.
2. Use BR-139 as the replay scorecard contract.
3. When BR-138 emits sidecar truth package rows, run BR-140 with baseline and candidate replay outputs.
4. Only after BR-140 has enough positive/negative support should BR-141 threshold candidate selection be considered.
5. If no real sidecar truth exists, the next safe open branch remains BR-143 prepatch gate refresh.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py research/prognostics/smoke_test_mlpe_field_trial_truth_replay_scorecard_contract_v1.py
python3 research/prognostics/smoke_test_mlpe_field_trial_truth_replay_scorecard_contract_v1.py
python3 research/prognostics/build_mlpe_field_trial_truth_replay_scorecard_contract_v1.py --repo-root "$(pwd)" --output-dir /private/tmp/mlpe_field_trial_truth_replay_scorecard_contract_br139_check
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_061_RESULT_DELTA_SCORECARD_V1

## Purpose
- Add an audit-only result delta scorecard so future engine patches can answer "how much did results change?" with one reproducible artifact.
- Separate result stability and candidate context from accuracy/F1 performance claims.
- This patch does not change runtime verdicts, thresholds, row universe, package outputs, or operator-facing semantics.

## Builder
- script:
  - `research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_v1.py`

## Inputs
- conalog runtime smoke root:
  - `/private/tmp/pvdiag_postmerge_j_conalog_smoke_result_delta_scorecard`
- BR-060 prepatch runbook summary:
  - `/private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv`

## Outputs
- `/private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_summary_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_note_v1.md`

## Real Data Result
- overall status:
  - `pass`
- core compared sites:
  - `1`
- core matched sites:
  - `1`
- core diff count:
  - `0`
- raw-only candidate rows:
  - `72`
- published current rows:
  - `72`
- precursor candidate rows:
  - `0`
- raw-only fault signal rows:
  - `72`
- fault panel rows:
  - `72`
- unresolved panel rows:
  - `277`
- proximal common-cause fault signal rows:
  - `64`
- proximal common-cause fault signal ratio:
  - `0.888889`
- fixed reference rows:
  - `6`
- fixed reference matched row keys:
  - `2`
- fixed reference overlap decision columns match:
  - `0`
- prepatch runbook status:
  - `pass`
- performance improvement claim:
  - `no_truth_label_not_claimed`
- result change claim:
  - `core_result_delta_0`

## Decision
- Accept BR-061 as the baseline result delta scorecard for future algorithm patch review.
- It is valid to claim result stability and candidate-context visibility from this artifact.
- It is not valid to claim percentage performance improvement, accuracy improvement, or F1 improvement from this artifact.
- Future direct engine patches should compare their post-patch scorecard against this baseline before claiming result improvement.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_result_delta_scorecard_v1.py --runtime-root /private/tmp/pvdiag_postmerge_j_conalog_smoke_result_delta_scorecard --prepatch-runbook-summary /private/tmp/panel_engine_algorithm_prepatch_runbook_check/panel_day_engine_algorithm_prepatch_runbook_summary_v1.csv --output-dir /private/tmp/panel_engine_result_delta_scorecard_check
```

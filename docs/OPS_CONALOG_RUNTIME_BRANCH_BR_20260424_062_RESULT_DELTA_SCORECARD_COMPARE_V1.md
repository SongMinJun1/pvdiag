<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_062_RESULT_DELTA_SCORECARD_COMPARE_V1

## Purpose
- Add an audit-only before/after comparator for BR-061 result delta scorecards.
- Future engine patches can now compare a baseline scorecard with a post-patch scorecard before claiming any result or performance change.
- This patch does not change runtime verdicts, thresholds, row universe, package outputs, or operator-facing semantics.

## Comparator
- script:
  - `research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_result_delta_scorecard_compare_v1.py`

## Inputs
- baseline scorecard summary:
  - `/private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_summary_v1.csv`
- post scorecard summary:
  - `/private/tmp/panel_engine_result_delta_scorecard_post_compare_check/panel_day_engine_result_delta_scorecard_summary_v1.csv`
- Current BR-062 check compares the BR-061 baseline to a fresh conalog rerun scorecard and expects a neutral delta.

## Outputs
- `/private/tmp/panel_engine_result_delta_scorecard_compare_check/panel_day_engine_result_delta_scorecard_compare_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_compare_check/panel_day_engine_result_delta_scorecard_compare_summary_v1.csv`
- `/private/tmp/panel_engine_result_delta_scorecard_compare_check/panel_day_engine_result_delta_scorecard_compare_note_v1.md`

## Real Data Result
- overall status:
  - `pass`
- metric count:
  - `19`
- changed metric count:
  - `0`
- core result changed flag:
  - `0`
- raw-only candidate row count delta:
  - `0`
- precursor candidate row count delta:
  - `0`
- fault panel count delta:
  - `0`
- proximal common-cause fault signal count delta:
  - `0`
- performance improvement claim:
  - `not_allowed_without_truth_label_eval`
- result change summary:
  - `no_result_change_detected`

## Decision
- Accept BR-062 as the required before/after scorecard comparator for future algorithm patch review.
- A neutral compare must show changed metric count `0`.
- A post-patch compare may show changes, but those changes are not performance improvement unless backed by truth-label evaluation.
- If core result changes, the next state is review, not automatic acceptance.

## Repro Command
```bash
python3 research/prognostics/compare_panel_day_engine_result_delta_scorecards_v1.py --baseline-scorecard-summary /private/tmp/panel_engine_result_delta_scorecard_check/panel_day_engine_result_delta_scorecard_summary_v1.csv --post-scorecard-summary /private/tmp/panel_engine_result_delta_scorecard_post_compare_check/panel_day_engine_result_delta_scorecard_summary_v1.csv --output-dir /private/tmp/panel_engine_result_delta_scorecard_compare_check
```

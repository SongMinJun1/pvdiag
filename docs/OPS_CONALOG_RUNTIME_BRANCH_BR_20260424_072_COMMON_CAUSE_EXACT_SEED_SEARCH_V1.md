<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_072_COMMON_CAUSE_EXACT_SEED_SEARCH_V1

## Purpose
- Re-search the common-cause exact same-day family after BR-071.
- Answer whether the current conservative path is blocking all progress or preserving a useful next search frontier.
- Classify every external/common-cause candidate by BR-036 judgment role before any semantic algorithm patch.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py`

## Inputs
- BR-064 fault-family judgment candidate packet:
  - `/private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv`
- BR-050 common-cause synchrony axis:
  - `/private/tmp/common_cause_synchrony_axis_sidecar_check/panel_day_engine_common_cause_synchrony_axis_v1.csv`
- tri-site report artifacts:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv`
  - `/private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv`
- raw candidate rows, read-only:
  - `/Users/b9gc/pvdiag/data/<site>/out/ae_simple_fault_candidates.csv`

## Outputs
- `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv`
- `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_summary_v1.csv`
- `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_site_status_summary_v1.csv`
- `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_note_v1.md`

## Real Data Result
- detail rows: `176`
- exact family closure candidates: `0`
- raw same-day direct common-cause reservoir: `49 panels / 101 rows`
- structural blocker panels: `49`
- BR-071 blocker/regression seed panels retained: `50`
- supportive/context hold panels: `127`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Judgment Summary
| primary_judgment_role | usage_tag | common_cause_search_bucket | cases | roots | raw_direct_rows | exact_closure | reservoir | structural_blocker |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `structural_blocker` | `block_panel_local_promotion_regression_seed` | `raw_direct_row_but_report_layer_misaligned` | 49 | 13 | 101 | 0 | 49 | 49 |
| `supportive_hint` | `block_panel_local_promotion_regression_seed` | `common_cause_context_hold` | 1 | 1 | 0 | 0 | 0 | 0 |
| `supportive_hint` | `review_context_only` | `subgroup_or_breadth_context_hold` | 126 | 23 | 0 | 0 | 0 | 0 |

## Site Status
| site | cases | roots | raw direct panels | raw direct rows | official current entries | exact closure | structural blocker | blocker seed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conalog` | 73 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| `gangui` | 27 | 5 | 19 | 71 | 0 | 0 | 19 | 20 |
| `ktc_ess` | 76 | 10 | 30 | 30 | 1 | 0 | 30 | 30 |

## Interpretation
- Conservative gating is not equivalent to no progress.
- The search keeps a positive frontier:
  - `49` panels and `101` raw same-day direct common-cause rows exist as `candidate_reservoir`.
  - Those rows are not exact closure because the official/current report layer still lacks same-day coincidence.
  - The single official/current common-cause entry in `ktc_ess` remains date-misaligned, with nearest current gap `71` days.
- BR-071 rows remain useful, but as regression blockers:
  - future semantic patches must prove they do not accidentally become panel-local positives.

## Decision
- Keep `exact_family_closure = 0`.
- Keep raw same-day direct rows as `candidate_reservoir + structural_blocker`, not production seeds.
- Continue blocker removal work around report-lane entry and date alignment before any common-cause semantic algorithm patch.
- Do not authorize operator-facing promotion, engine patch, or threshold patch from this search.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_exact_seed_search_v1.py
python3 research/prognostics/build_panel_day_engine_common_cause_exact_seed_search_v1.py --judgment-input /private/tmp/fault_family_judgment_candidate_packet_check/panel_day_engine_fault_family_judgment_candidate_packet_v1.csv --synchrony-input /private/tmp/common_cause_synchrony_axis_sidecar_check/panel_day_engine_common_cause_synchrony_axis_v1.csv --current-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_current_v1.csv --precursor-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_precursor_report_v1.csv --rawonly-signal-input /private/tmp/conalog_mlpe_seed_expand_check/result/fault_panel_result_raw_only_fault_signal_report_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/common_cause_exact_seed_search_check
```

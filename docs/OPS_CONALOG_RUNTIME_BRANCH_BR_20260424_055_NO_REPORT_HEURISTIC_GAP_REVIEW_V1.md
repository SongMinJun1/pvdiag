<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_055_NO_REPORT_HEURISTIC_GAP_REVIEW_V1

## Purpose
- BR-052에서 남은 `no_report_heuristic_match = 8`을 report-lane / heuristic attachment gap으로 분해한다.
- 목적은 이 8건이 `panel_day_engine.py` 엔진 버그인지, report 관찰 sidecar 후보인지, 아니면 evidence-only/date-displaced morphology인지 판별하는 것이다.
- 이 패치는 runtime verdict, threshold, row universe, operator-facing semantics를 바꾸지 않는다.

## Builder
- script:
  - `research/prognostics/build_panel_day_engine_no_report_heuristic_gap_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_no_report_heuristic_gap_review_v1.py`

## Inputs
- local morphology exact seed search:
  - `/private/tmp/local_morphology_exact_seed_search_check`
- raw candidates:
  - `/Users/b9gc/pvdiag/data/<site>/out/ae_simple_fault_candidates.csv`
- raw-only share root:
  - `/private/tmp/conalog_mlpe_seed_expand_check/raw_only_chain_workspace/_share`
- runtime result root:
  - `/private/tmp/conalog_mlpe_seed_expand_check/result`

## Outputs
- `/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_v1.csv`
- `/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_summary_v1.csv`
- `/private/tmp/no_report_heuristic_gap_review_check/panel_day_engine_no_report_heuristic_gap_review_note_v1.md`

## Real Data Result
- reviewed panels:
  - `8`
- heuristic gap classification:
  - `expected_absent_non_fault_status_gate = 8`
- engine patch candidates:
  - `0`
- report observation sidecar candidates:
  - `3`
- date alignment split:
  - `near_anchor_1_3d = 3`
  - `date_displaced_gt14d = 5`
- hard fault signal rows:
  - `0`

## Site Split
| site | gap type | panels | engine patch candidates | report observation candidates |
|---|---|---:|---:|---:|
| `conalog` | `date_displaced_gt14d` | 4 | 0 | 0 |
| `conalog` | `near_anchor_1_3d` | 2 | 0 | 2 |
| `gangui` | `near_anchor_1_3d` | 1 | 0 | 1 |
| `ktc_ess` | `date_displaced_gt14d` | 1 | 0 | 0 |

## Interpretation
- The missing heuristic rows are explained by the deterministic fault-status gate:
  - runtime cause heuristic is built only for rows where `패널고장여부_ko == 고장`.
  - all 8 reviewed rows are `미확정`.
- Therefore this is not currently evidence for a `panel_day_engine.py` algorithm bug.
- The 3 near-anchor rows may justify a future non-fault morphology observation sidecar, but not automatic operator-facing promotion.
- The 5 date-displaced rows should remain evidence-only/date-displaced morphology context.

## Decision
- Do not open an engine patch from BR-055.
- Keep exact-family closure open.
- If the next patch continues from this branch, the safest target is a small report-observation sidecar for the 3 near-anchor non-fault morphology rows, not a runtime rule/threshold change.

## Repro Command
```bash
python3 research/prognostics/build_panel_day_engine_no_report_heuristic_gap_review_v1.py --local-search-root /private/tmp/local_morphology_exact_seed_search_check --data-root /Users/b9gc/pvdiag/data --result-root /private/tmp/conalog_mlpe_seed_expand_check/result --raw-only-share-root /private/tmp/conalog_mlpe_seed_expand_check/raw_only_chain_workspace/_share --output-dir /private/tmp/no_report_heuristic_gap_review_check --sites conalog gangui ktc_ess
```

<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_073_COMMON_CAUSE_STRUCTURAL_BLOCKER_REVIEW_V1

## Purpose
- Split BR-072 common-cause structural blockers into concrete report-lane/date-alignment subtypes.
- Identify whether any blocker is close enough for manual trace review.
- Keep this as evidence-only review; no production semantics are changed.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_common_cause_structural_blocker_review_v1.py`

## Inputs
- BR-072 common-cause exact seed search:
  - `/private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv`

## Outputs
- `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_v1.csv`
- `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_summary_v1.csv`
- `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_site_summary_v1.csv`
- `/private/tmp/common_cause_structural_blocker_review_check/panel_day_engine_common_cause_structural_blocker_review_note_v1.md`

## Real Data Result
- detail rows: `49`
- manual trace review targets: `2`
- structural patch-target review rows: `2`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`
- threshold patch allowed sum: `0`

## Structural Blocker Split
| subtype | cases | roots | raw rows | readiness |
| --- | ---: | ---: | ---: | --- |
| `no_report_lane_entry` | 13 | 6 | 13 | hold until report entry exists |
| `precursor_carryover_without_current_closure` | 19 | 6 | 20 | precursor-only context hold |
| `rawonly_date_displaced_without_current_closure` | 15 | 5 | 66 | raw-only context hold |
| `rawonly_near_signal_anchor` | 1 | 1 | 1 | manual trace review only |
| `official_current_date_displaced` | 1 | 1 | 1 | manual trace review only |

## Site Read
- `gangui`:
  - `rawonly_date_displaced_without_current_closure`: `15` cases / `66` raw rows
  - `rawonly_near_signal_anchor`: `1` manual trace target
  - `precursor_carryover_without_current_closure`: `2` cases
  - `no_report_lane_entry`: `1` case
- `ktc_ess`:
  - `precursor_carryover_without_current_closure`: `17` cases
  - `no_report_lane_entry`: `12` cases
  - `official_current_date_displaced`: `1` manual trace target with nearest current gap `71` days

## Interpretation
- BR-073 narrows BR-072's large structural blocker pool into two practical layers.
- Large hold layer:
  - `47` rows remain lane/date context only.
  - These rows are not patch-ready semantics.
- Small manual-trace layer:
  - `2` rows deserve deeper trace review.
  - They still do not authorize production promotion, engine patching, or threshold patching.
- This means the conservative path is still producing forward motion:
  - the search frontier is no longer all `49` rows
  - the next manual workload is `2` rows

## Decision
- Keep all BR-073 rows out of operator-facing promotion.
- Keep engine patch and threshold patch authorization at `0`.
- Use the two manual trace targets as the next inspection queue, not as positive examples.
- Before any semantic rule change, prove whether either target is a data/reporting alignment issue rather than a real common-cause hold.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py research/prognostics/smoke_test_panel_day_engine_common_cause_structural_blocker_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_common_cause_structural_blocker_review_v1.py
python3 research/prognostics/build_panel_day_engine_common_cause_structural_blocker_review_v1.py --exact-seed-input /private/tmp/common_cause_exact_seed_search_check/panel_day_engine_common_cause_exact_seed_search_v1.csv --output-dir /private/tmp/common_cause_structural_blocker_review_check
```

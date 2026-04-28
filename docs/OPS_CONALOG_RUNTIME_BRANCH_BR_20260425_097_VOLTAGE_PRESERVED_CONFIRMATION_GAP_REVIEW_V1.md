<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_097_VOLTAGE_PRESERVED_CONFIRMATION_GAP_REVIEW_V1

## Purpose
- Implement the next safe step after BR-096: review which confirmation axes are still open after raw/source traceability is attached.
- Separate four evidence layers that were easy to blur:
  - raw/source trace attached
  - exact vendor/manual support
  - independent physical or maintenance confirmation
  - blocker clearance for common-cause, measurement-artifact, and counterexample risk
- Keep this branch gap-review-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_attachment_index_v1.csv` | BR-096 request-level raw/source attachment index |
| `/private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check/panel_day_engine_voltage_preserved_raw_source_daily_trace_v1.csv` | BR-096 daily trace safety input |
| `/Users/b9gc/pvdiag/data/manual/vendor_reply_cases.csv` | exact-panel vendor/manual reply cases |
| `docs/internal/manual_field_evidence_latest.csv` | site-level manual context, not exact-panel validation |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_checklist_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_review_v1.json`

## Real Result
- review rows: `14`
- checklist rows: `84`
- summary rows: `8`
- review bucket counts:
  - `vendor_supported_needs_physical_confirmation`: `5`
  - `raw_supported_needs_independent_confirmation`: `4`
  - `counterexample_guarded_hold`: `3`
  - `blocker_clearance_hold`: `2`
- raw source attached rows: `14`
- vendor exact support rows: `9`
- vendor positive/likely rows: `7`
- vendor rejected/none-visible rows: `2`
- vendor field-confirmed rows: `0`
- independent confirmation met rows: `0`
- all-clearance candidate rows: `9`
- evidence ready for truth use sum: `0`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Site Split
| site | review_rows | vendor_exact_support_rows | vendor_positive_or_likely_rows | vendor_rejected_rows | counterexample_clearance_required_rows | independent_confirmation_met_rows | evidence_ready_for_truth_use_sum |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conalog` | 3 | 3 | 2 | 1 | 0 | 0 | 0 |
| `gangui` | 9 | 4 | 3 | 1 | 3 | 0 | 0 |
| `ktc_ess` | 2 | 2 | 2 | 0 | 0 | 0 | 0 |

## Review Buckets
| review_bucket | rows | meaning | next action |
| --- | ---: | --- | --- |
| `vendor_supported_needs_physical_confirmation` | 5 | exact vendor pattern/likely support exists, but `field_confirmed_flag=0` | attach exact-panel physical, electrical, inspection, maintenance, or repair record |
| `raw_supported_needs_independent_confirmation` | 4 | raw/source trace is present, but exact vendor/field support is still missing | collect independent exact-panel evidence |
| `counterexample_guarded_hold` | 3 | same-root negative-overlap/counterexample risk remains active | resolve counterexample clearance before truth rebuild |
| `blocker_clearance_hold` | 2 | common-cause or measurement-artifact blocker remains active | review blocker-held days before confirmation |

## Interpretation
- BR-097 is real progress because it narrows the remaining problem from “raw evidence is scattered” to “which exact confirmation axes are still missing”.
- The strongest current external support is vendor pattern/likely support for `7` rows, but none of those rows are field-confirmed.
- Raw/source attachment is now closed for all `14` rows, but raw waveform support remains support-only and cannot become a truth label by itself.
- The `3` `gangui` counterexample-guarded rows stay behind explicit clearance even when exact vendor support exists.
- Site-level manual context is kept as context only; `manual_site_exact_usable_rows` remains `0`, so it does not close exact-panel validation.

## Safety Boundary
- BR-097 does not rebuild truth rows.
- BR-097 does not rerun or tune thresholds.
- BR-097 does not change runtime verdicts or operator-facing labels.
- Vendor pattern support is not physical confirmation unless `field_confirmed_flag > 0` or exact-panel physical/maintenance evidence is attached.
- Data-derived common-cause/artifact/counterexample clearance candidates are not approvals; they only identify rows that can be reviewed next.

## Ordered Next Path
1. Attach exact-panel independent physical/electrical/inspection/maintenance/repair evidence for the `7` vendor positive/likely rows first.
2. Resolve the `3` `gangui` counterexample-guarded rows separately before any truth rebuild.
3. Review the `2` blocker-held rows for common-cause and measurement-artifact clearance.
4. Only after independent confirmation and clearance axes are explicitly populated, build confirmed-positive truth intake.
5. Re-run subtype threshold replay only after enough evidence-backed positive and negative truth rows exist.

## Decision
- Accept BR-097 as the current confirmation-gap review.
- Do not treat vendor/manual support as final truth.
- Do not rebuild confirmed-positive truth or rerun threshold replay yet.
- The next branch should be an independent confirmation attachment plus blocker-clearance attachment, not a `panel_day_engine.py` patch.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_confirmation_gap_review_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --attachment-dir /private/tmp/panel_day_engine_voltage_preserved_raw_source_attachment_br096_check --vendor-input /Users/b9gc/pvdiag/data/manual/vendor_reply_cases.csv --manual-site-input docs/internal/manual_field_evidence_latest.csv --output-dir /private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check
```

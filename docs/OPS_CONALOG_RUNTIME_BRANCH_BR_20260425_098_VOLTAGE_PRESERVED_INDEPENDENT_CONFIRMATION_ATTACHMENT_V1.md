<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_098_VOLTAGE_PRESERVED_INDEPENDENT_CONFIRMATION_ATTACHMENT_V1

## Purpose
- Implement the next safe step after BR-097: attach exact-panel independent confirmation and explicit blocker-clearance evidence if it exists.
- Convert the BR-097 gap review into fillable evidence templates so future field/maintenance records can be attached without changing runtime code.
- Keep three evidence roles separate:
  - exact vendor pattern support
  - same-site field-confirmed references that do not match the target panel
  - exact-panel independent physical/maintenance/inspection/repair confirmation
- Keep this branch attachment-gate-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check/panel_day_engine_voltage_preserved_confirmation_gap_review_v1.csv` | BR-097 confirmation gap review |
| `/Users/b9gc/pvdiag/data/manual/vendor_reply_cases.csv` | exact-panel vendor/manual reply cases and same-site reference cases |
| `docs/internal/manual_field_evidence_latest.csv` | site-level manual context, not exact-panel validation |
| optional `--independent-evidence-input` | future exact-panel physical/electrical/maintenance/inspection/repair evidence |
| optional `--blocker-clearance-input` | future explicit common-cause/artifact/counterexample clearance evidence |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_source_scan_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_blocker_clearance_attachment_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_action_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_input_template_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_blocker_clearance_input_template_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.json`

## Real Result
- attachment rows: `14`
- source scan rows: `56`
- blocker clearance rows: `14`
- summary rows: `8`
- exact vendor positive/likely target rows: `7`
- exact vendor field-confirmed target rows: `0`
- target rows with same-site field-confirmed reference examples: `3`
- exact independent evidence rows attached: `0`
- independent confirmation attached rows: `0`
- data-clearance candidate rows: `9`
- explicit all-clearance rows: `0`
- counterexample-clearance required rows: `3`
- truth intake ready rows: `0`
- positive truth candidate approved sum: `0`
- threshold tuning approved sum: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Site Split
| site | review_rows | exact_vendor_positive_or_likely_rows | exact_vendor_field_confirmed_rows | target_rows_with_same_site_reference | independent_confirmation_attached_rows | data_clearance_candidate_rows | explicit_all_clearance_rows | counterexample_clearance_required_rows | truth_intake_ready_rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conalog` | 3 | 2 | 0 | 3 | 0 | 2 | 0 | 0 | 0 |
| `gangui` | 9 | 3 | 0 | 0 | 0 | 5 | 0 | 3 | 0 |
| `ktc_ess` | 2 | 2 | 0 | 0 | 0 | 2 | 0 | 0 | 0 |

## Interpretation
- BR-098 confirms that no current voltage-preserved target row has exact-panel field confirmation.
- `conalog` has same-site field-confirmed reference examples, but they are different panel IDs and therefore reference-only.
- The `7` exact vendor positive/likely rows remain useful acquisition targets, not positive truth rows.
- The `9` data-clearance candidate rows are not explicit blocker clearances.
- The `3` `gangui` counterexample-guarded rows still require explicit same-root counterexample clearance.
- Because independent confirmation and explicit clearances are both `0`, confirmed-positive truth intake remains blocked.

## Templates
- `panel_day_engine_voltage_preserved_independent_confirmation_input_template_v1.csv` is the fillable template for exact-panel evidence.
- Accepted independent evidence types are:
  - `field_confirmation`
  - `inspection_record`
  - `inverter_trace`
  - `iv_curve`
  - `maintenance_record`
  - `physical_measurement`
  - `repair_record`
  - `string_trace`
- Accepted confirmed statuses are:
  - `attached_confirmed`
  - `confirmed`
  - `field_confirmed`
  - `reviewed_positive`
- `panel_day_engine_voltage_preserved_blocker_clearance_input_template_v1.csv` is the fillable template for explicit blocker clearance.
- Accepted clearance statuses are:
  - `attached_clear`
  - `cleared`
  - `reviewed_clear`

## Safety Boundary
- Same-site confirmed references are not target-panel confirmation.
- Vendor pattern support is not exact physical confirmation unless field confirmation or independent evidence is attached.
- Data-derived common-cause/artifact/counterexample candidate flags are not explicit reviewer clearance.
- No truth rebuild, threshold replay, operator-facing promotion, or direct `panel_day_engine.py` edit is approved.

## Ordered Next Path
1. Fill the independent-confirmation template only with exact-panel physical/electrical/inspection/maintenance/repair evidence.
2. Fill the blocker-clearance template only with explicit common-cause, measurement-artifact, and counterexample clearance evidence.
3. Re-run BR-098 with those filled templates and verify `truth_intake_ready_rows`.
4. Only after BR-098 produces nonzero exact evidence and explicit clearance, build a separate confirmed-positive truth-intake gate.
5. Keep threshold replay and `panel_day_engine.py` changes blocked until confirmed truth intake exists.

## Decision
- Accept BR-098 as the current attachment gate.
- Do not use same-site references, vendor pattern support, or data-clearance candidates as truth labels.
- The next step is evidence acquisition/template fill, not threshold replay or engine patching.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.py --repo-root /Users/b9gc/pvdiag_worktrees/postmerge_j --gap-review-dir /private/tmp/panel_day_engine_voltage_preserved_confirmation_gap_review_br097_check --vendor-input /Users/b9gc/pvdiag/data/manual/vendor_reply_cases.csv --manual-site-input docs/internal/manual_field_evidence_latest.csv --output-dir /private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check
```

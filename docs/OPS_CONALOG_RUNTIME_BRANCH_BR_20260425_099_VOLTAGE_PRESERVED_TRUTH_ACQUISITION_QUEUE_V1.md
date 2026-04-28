<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260425_099_VOLTAGE_PRESERVED_TRUTH_ACQUISITION_QUEUE_V1

## Purpose
- Implement the next safe step after BR-098: convert missing evidence axes into a collector-facing acquisition queue.
- Make the remaining voltage-preserved work actionable without pretending that truth labels already exist.
- Keep this branch acquisition-planning-only:
  - no positive truth label approval
  - no threshold tuning approval
  - no `panel_day_engine.py` patch
  - no runtime verdict change
  - no operator-facing promotion

## Implementation
- builder:
  - `research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py`

## Inputs
| input | role |
| --- | --- |
| `/private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check/panel_day_engine_voltage_preserved_independent_confirmation_attachment_v1.csv` | BR-098 attachment gate output |

## Outputs
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_panel_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_site_summary_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_collector_template_v1.csv`
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_note_v1.md`
- `/private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check/panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.json`

## Real Result
- panel rows: `14`
- queue rows: `45`
- collector template rows: `45`
- open required axes: `45`
- independent confirmation queue rows: `14`
- common-cause clearance queue rows: `14`
- measurement-artifact clearance queue rows: `14`
- counterexample clearance queue rows: `3`
- same-site reference-only target rows: `3`
- vendor support context target rows: `7`
- truth intake ready rows: `0`
- operator-facing change allowed sum: `0`
- engine patch allowed sum: `0`
- threshold patch allowed sum: `0`

## Site Split
| site | panel_rows | queue_rows | open_required_axes | independent_confirmation_open_rows | explicit_clearance_open_rows | counterexample_clearance_open_rows | same_site_reference_only_rows | vendor_support_context_rows | truth_intake_ready_rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `conalog` | 3 | 9 | 9 | 3 | 6 | 0 | 3 | 2 | 0 |
| `gangui` | 9 | 30 | 30 | 9 | 18 | 3 | 0 | 3 | 0 |
| `ktc_ess` | 2 | 6 | 6 | 2 | 4 | 0 | 0 | 2 | 0 |

## Queue Axes
| acquisition_axis | rows | role |
| --- | ---: | --- |
| `independent_panel_confirmation` | 14 | exact-panel physical/electrical/inspection/maintenance/repair evidence |
| `common_cause_clearance` | 14 | explicit reviewer/evidence clearance that panel-local truth is not site/root/group common-cause |
| `measurement_artifact_clearance` | 14 | explicit clearance that sensor/reference/logger/data artifact is not driving the shape |
| `counterexample_clearance` | 3 | explicit same-root negative-overlap/counterexample clearance for guarded rows |

## Interpretation
- BR-099 is the actionable shopping list for the current voltage-preserved frontier.
- The `7` vendor-supported target rows get higher-priority exact-panel confirmation requests, but they remain support context only.
- The `3` same-site reference-only target rows are useful for analogy and collection routing, not exact confirmation.
- The `3` `gangui` counterexample-guarded rows require one extra axis each, so they have 4 queue rows per panel instead of 3.
- Every queue row is still open, so confirmed-positive truth intake remains blocked.

## Safety Boundary
- BR-099 does not attach evidence; it tells us what evidence to collect.
- BR-099 does not create truth labels.
- BR-099 does not approve threshold replay.
- BR-099 does not approve direct `panel_day_engine.py` edits.
- Any collected evidence must be fed back through BR-098 first; only then can a separate truth-intake branch be considered.

## Ordered Next Path
1. Use `panel_day_engine_voltage_preserved_truth_acquisition_collector_template_v1.csv` as the collection sheet.
2. Fill only exact-panel evidence or explicit clearance records; do not use same-site references as target-panel confirmation.
3. Convert filled collector rows into BR-098 independent evidence and blocker-clearance inputs.
4. Re-run BR-098 and verify whether `truth_intake_ready_rows` becomes nonzero.
5. If and only if BR-098 produces ready rows, build a separate confirmed-positive truth-intake gate.

## Decision
- Accept BR-099 as the current evidence acquisition queue.
- Do not proceed to truth intake, threshold replay, or engine patching until this queue has actual collected evidence and BR-098 re-attachment succeeds.

## Repro Commands
Before patch:

```bash
git status --short --branch
```

After patch:

```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py research/prognostics/smoke_test_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py
python3 research/prognostics/build_panel_day_engine_voltage_preserved_truth_acquisition_queue_v1.py --repo-root "$(pwd)" --attachment-dir /private/tmp/panel_day_engine_voltage_preserved_independent_confirmation_br098_check --output-dir /private/tmp/panel_day_engine_voltage_preserved_truth_acquisition_queue_br099_check
```

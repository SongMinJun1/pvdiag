<!-- markdownlint-disable MD013 -->

# OPS_CONALOG_RUNTIME_BRANCH_BR_20260424_068_RAW_WAVEFORM_PHYSICAL_SUPPORT_REVIEW_V1

## Purpose
- Follow BR-067's next evidence requirement by checking raw long-format daily CSVs for the 2 physical-leaning voltage-axis rows.
- Use timestamp-level peer comparison as waveform proxy evidence:
  - target `v_in` vs same-timestamp peer median `v_in`
  - target `i_out` vs same-timestamp peer median `i_out`
  - target `p` vs same-timestamp peer median `p`
- Keep this as physical-support review only, not a confirmed fault-family threshold.

## Builder
- builder:
  - `research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py`
- smoke:
  - `research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py`

## Inputs
- BR-067 physical-vs-artifact review:
  - `/private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv`
- read-only panel-day core:
  - `/Users/b9gc/pvdiag/data/<site>/out/panel_day_core.csv`
- read-only raw daily files:
  - `/Users/b9gc/pvdiag/data/<site>/raw/<source_csv>`

## Outputs
- `/private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_v1.csv`
- `/private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_summary_v1.csv`
- `/private/tmp/raw_waveform_physical_support_review_check/panel_day_engine_raw_waveform_physical_support_review_note_v1.md`

## Real Data Result
- detail rows: `2`
- raw waveform physical-support rows: `2`
- operator promotion allowed sum: `0`
- engine patch candidate sum: `0`

## Detail Snapshot
| site | panel_id | target_vdom_signal_days | raw_file_found_days | raw_active_timestamp_rows | raw_median_v_ratio | raw_median_i_ratio | raw_median_p_ratio | raw_vlow_iok_timestamp_frac | raw_daily_support_days | raw_daily_support_frac | physical_support_score | limitation_score |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `gangui` | `bf1a912f-6cf0-4f12-8e97-9d9d86576511.0.7` | 146 | 146 | 14196 | 0.632757 | 1.040984 | 0.666620 | 0.884686 | 144 | 0.986301 | 12 | 0 |
| `ktc_ess` | `70ad2d87-cdb6-4842-81b7-71c7599bbf05.1.4` | 111 | 111 | 15506 | 0.564797 | 1.044655 | 0.614780 | 0.785180 | 98 | 0.882883 | 12 | 0 |

## Interpretation
- Both rows now have raw waveform proxy support:
  - median voltage ratio is low (`0.632757`, `0.564797`)
  - median current ratio is preserved or slightly high (`1.040984`, `1.044655`)
  - median power ratio is low (`0.666620`, `0.614780`)
  - timestamp-level low-voltage/current-ok fraction is high (`0.884686`, `0.785180`)
- Raw source coverage is complete for the target signal days:
  - `gangui`: `146/146`
  - `ktc_ess`: `111/111`
- This supports the physical voltage-axis hypothesis more strongly than BR-067 did.
- It still does not authorize a semantic threshold patch by itself.
  - The remaining missing layer is independent confirmation: IV/waveform artifact, maintenance/inspection evidence, or reproducible field confirmation.

## Decision
- BR-068 keeps both rows as `raw_waveform_physical_support_review`.
- BR-068 promotes 0 rows to operator-facing result.
- BR-068 authorizes 0 direct engine patches.
- The next safe step is to define a physical-confirmation packet or checklist before any family-specific threshold proposal.

## Repro Commands
```bash
python3 -m py_compile pv_ae/panel_day_engine.py research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py
python3 research/prognostics/smoke_test_panel_day_engine_raw_waveform_physical_support_review_v1.py
python3 research/prognostics/build_panel_day_engine_raw_waveform_physical_support_review_v1.py --review-input /private/tmp/voltage_dominant_physical_vs_artifact_review_check/panel_day_engine_voltage_dominant_physical_vs_artifact_review_v1.csv --data-root /Users/b9gc/pvdiag/data --output-dir /private/tmp/raw_waveform_physical_support_review_check
```

# OPS PANEL DAY ENGINE INTERNAL SHARE CLEAN PACK V1

## Purpose

This is a non-core packaging/documentation step.

It does not change detector logic.
It does not touch the seed 4-panel internal-share flow.

It builds one clean Korean internal-share pack from already-approved summary artifacts only.

## Important Boundary

This clean pack must stay independent from the seed-panel flow.

So it:

- does not read seed 4-panel outputs
- does not discuss AE/DTW seed cases
- does not depend on the old case-review flow

It only reuses summary artifacts that were already approved.

## Inputs

- `_share/panel_day_engine_latest_perf_internal_share_v1.csv`
- `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- `_share/panel_day_engine_kernellog_project_mapping_v1.csv`
- `_share/panel_day_engine_gpv7_perf_summary_v1.csv`
- `_share/panel_day_engine_project_progress_snapshot_v1.csv`
- `_share/panel_day_engine_project_final_decision_pack_v1.csv`
- `_share/panel_day_engine_project_handoff_summary_v1.csv`

## Outputs

- `_share/panel_day_engine_internal_share_clean_pack_v1.md`
- `_share/panel_day_engine_internal_share_clean_summary_v1.csv`

## What This Pack Consolidates

1. latest performance summary
2. abrupt 6-case symptom-name map
3. kernel-log symptom axis to project event axis mapping
4. GPV 7-type summary
5. current progress snapshot
6. simple do/don't language for internal sharing

## Summary CSV

`panel_day_engine_internal_share_clean_summary_v1.csv` is a compact share table.

It emits rows under these sections:

- `최신 성능`
- `급작 고장 6건`
- `커널로그-프로젝트 매핑`
- `GPV 7종`
- `진행률`
- `말해도 되는 것 / 말하면 안 되는 것`

Columns are:

- `섹션`
- `항목`
- `값_ko`
- `비고_ko`

## Markdown Pack

`panel_day_engine_internal_share_clean_pack_v1.md` is the directly shareable Korean artifact.

It contains exactly these sections:

1. `최신 성능 요약`
2. `급작 고장 6건 증상 분류`
3. `커널로그 분류와 프로젝트 분류 관계`
4. `GPV 7종 정리`
5. `현재 진행률`
6. `지금 말해도 되는 것 / 말하면 안 되는 것`

Style rules:

- Korean only
- short sentences
- no seed-panel discussion
- no AE/DTW case discussion
- no long theory

## Interpretation Rules

### Latest Performance

The clean pack uses only:

- `전조형 고장`
- `급작 고장`
- `common-cause routing`

from `panel_day_engine_latest_perf_internal_share_v1.csv`.

In the clean pack, `common-cause routing` is presented as `같이 흔들리는 이상` for internal readability.

### Abrupt 6 Cases

The abrupt 6-case section uses `_share/panel_day_engine_abrupt6_symptom_map_v1.csv` exactly as stored.

It does not add new inference beyond those rows.

### Kernel Mapping

The kernel-log section uses `_share/panel_day_engine_kernellog_project_mapping_v1.csv` exactly as stored.

Its main message is simple:

- kernel-log is the symptom axis
- the project is the event-type axis

### GPV 7 Types

The GPV section uses `_share/panel_day_engine_gpv7_perf_summary_v1.csv` exactly as stored.

If the source rows say the exact 7-class metrics were not found, that wording must be preserved.
No missing numbers should be invented.

### Progress

The progress section uses `_share/panel_day_engine_project_progress_snapshot_v1.csv` exactly as stored:

- `연구/알고리즘 큰 줄기`
- `운영 스택`
- `내부 공유/정리 문서`

### Claims

The final section is summarized from:

- `_share/panel_day_engine_project_final_decision_pack_v1.csv`
- `_share/panel_day_engine_project_handoff_summary_v1.csv`

It should clearly keep the current boundaries:

- abrupt can be discussed only at bounded current-data level
- precursor remains exploratory because support is small
- common-cause remains exploratory
- operator workflow can be used operationally
- detector general performance must not be overclaimed

## Smoke Coverage

The smoke test verifies:

- scripts compile
- outputs generate
- markdown sections are emitted
- summary rows are emitted
- no seed-panel outputs are read
- official outputs are not modified by the smoke

## Reproduction

```bash
python -m py_compile research/prognostics/build_panel_day_engine_internal_share_clean_pack_v1.py research/prognostics/smoke_test_panel_day_engine_internal_share_clean_pack_v1.py
python research/prognostics/build_panel_day_engine_internal_share_clean_pack_v1.py
python research/prognostics/smoke_test_panel_day_engine_internal_share_clean_pack_v1.py
```

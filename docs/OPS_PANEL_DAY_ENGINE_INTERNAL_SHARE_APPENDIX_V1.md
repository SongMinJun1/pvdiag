# OPS PANEL DAY ENGINE INTERNAL SHARE APPENDIX V1

## Purpose

This appendix is a non-core internal-share packaging step.

It does not change detector logic.
It does not touch the older seed-panel AE/DTW case-review flow.

Instead, it builds four lightweight appendix artifacts that can be attached after the main internal-share pack:

1. abrupt/no-precursor 6-case symptom-name matching
2. kernel-log symptom name to project-category interpretation mapping
3. GPV 7-type performance summary or explicit not-found fallback
4. whole-project progress snapshot

## Important Boundary

This appendix step must exclude the seed 4 panels entirely.

So this step:

- does not read the seed-panel case-review outputs
- does not print the seed-panel case-review outputs
- does not summarize the seed-panel AE/DTW examples

The appendix is intentionally separate from the seed-panel narrative.

## Inputs

- `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
- `_share/panel_date_reaudit_working.csv`
- `_share/panel_day_engine_project_eval_matrix_v1.csv`
- `_share/panel_day_engine_project_current_data_freeze_pack_v1.csv`
- `_share/panel_day_engine_operator_attention_policy_recommendation_v1.csv`
- `_share/panel_day_engine_operator_pipeline_manifest_v1.csv`
- repo-local GPV files/docs/outputs only

## Outputs

- `_share/panel_day_engine_abrupt6_symptom_map_v1.csv`
- `_share/panel_day_engine_kernellog_project_mapping_v1.csv`
- `_share/panel_day_engine_gpv7_perf_summary_v1.csv`
- `_share/panel_day_engine_project_progress_snapshot_v1.csv`

## Abrupt6 Symptom Map

Base universe starts from `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`.

Then the builder narrows to rows that belong to `abrupt_or_no_precursor_now`.

The expected current real row count is 6.

Selection policy is strict first, then only minimally broadened when stored truth says the strict view is incomplete:

1. start from `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
2. keep only `abrupt_or_no_precursor_now`
3. exclude rows with `candidate_validity == false_positive`
4. exclude rows with `vendor_reply_class == vendor_rejected`
5. keep strict abrupt-evidence rows with at least one stored hard flag:
   - `final_fault_hit_by_anchor_flag == 1`
   - `final_fault_hit_within_3d_after_flag == 1`
   - `final_fault_hit_within_7d_after_flag == 1`
   - `critical_fault_hit_by_anchor_flag == 1`
   - `critical_fault_hit_within_3d_after_flag == 1`
   - `critical_fault_hit_within_7d_after_flag == 1`
6. if the strict set is smaller than the known abrupt positive support, backfill only from `_share/panel_date_reaudit_working.csv` rows that are:
   - still not `false_positive`
   - still not `vendor_rejected`
   - explicitly mapped to accepted abrupt-positive families:
     - `diode_like`
     - `open_or_device_issue_like`
     - `module_damage_like`
7. use `_share/panel_day_engine_local_precursor_eligibility_cases_v1.csv` only as tie-breaker or date enrichment when available
8. remove the banned seed-panel ids entirely
9. after strict rows plus accepted-truth backfill, the final abrupt6 row count must be exactly `6`
10. if the count is not exactly `6`, the builder fails clearly and does not overwrite a stale abrupt6 output

This keeps the abrupt6 map aligned with the requested "true abrupt positive only" interpretation while still recovering the already-agreed 6-case universe from stored accepted truth.

Each row reports:

- site
- panel_id
- fault anchor date
- symptom-level Korean name
- short evidence text
- which source field drove that mapping
- note

Allowed `증상명_ko`:

- `다이오드형`
- `개방/장치이상형`
- `모듈손상형`
- `출력저하형`
- `전압변화형`
- `복합형`
- `불충분`

Mapping priority is intentionally conservative:

1. explicit truth/vendor family first
2. then current stored reason strings
3. then closest symptom-level wording only when evidence is still visible
4. otherwise `불충분`

This avoids inventing unsupported physical root-cause names.

## Kernel-Log To Project Mapping

`panel_day_engine_kernellog_project_mapping_v1.csv` is a fixed interpretation table.

It is not a confusion matrix.

It answers:

"When an internal kernel-log symptom label is used, which project bucket is the main interpretation, and which bucket is only secondary?"

Fixed kernel-log symptom rows:

- `출력 저하형`
- `전압 변화형`
- `패턴 이상형`
- `불안정형`
- `복합형`

Allowed project-category values:

- `전조형 고장`
- `급작 고장`
- `같이 흔들리는 이상`
- `반복 이상`
- `오경보`

## GPV 7-Type Summary

This appendix searches the current repo only.
No web lookup is used.

Search scope is limited to repo files/docs/outputs containing names such as:

- `gpv`
- `gpvs`
- `faults`
- `classification`
- `benchmark`

Decision rule:

- first try to parse `data/gpvs/out/EXTERNAL_GPVS_BYTYPE_METRICS.csv`
- if per-type metrics are present there, emit one row per GPV type `1..7` with actual stored values
- representative row per type is chosen from the stored by-type table using a simple score priority such as AP/AUC/F1
- otherwise emit rows `1..7` with:
  - `성능요약_ko = 현재 저장 산출물에서 7종별 정식 수치 미확인`
  - blank numeric field
  - source text that explicitly says repo search only / not found

If exact Korean type descriptions are not stored, the appendix uses coarse labels like `GPVS Fault1` ... `GPVS Fault7` and still reports the actual parsed metrics.

## Progress Snapshot

The progress snapshot intentionally emits exactly three rows:

- `연구/알고리즘 큰 줄기`
- `운영 스택`
- `내부 공유/정리 문서`

Current fixed completion estimates:

- research/algorithm: `85`
- operator stack: `95`
- internal-share/docs: `70`

Interpretation:

- research/algorithm: main lines are done, but step3/common-cause remain underpowered under current data
- operator stack: baseline, QA, pipeline, release gate, and idempotence have been built
- internal-share/docs: appendix completion improved the share state, but the document pack is still not fully closed

## Smoke Coverage

The smoke test checks:

- scripts compile
- abrupt6 output row count is exactly `6`
- strict abrupt evidence plus accepted-truth backfill produces the expected 6-row family mix
- `false_positive` / `vendor_rejected` rows are excluded
- banned seed-panel ids are excluded
- stale-output protection works when the builder cannot recover 6 abrupt-positive rows
- fixed mapping rows are emitted
- GPV by-type parser uses actual stored metrics when present
- progress snapshot rows are emitted
- seed-panel outputs are not read or required
- official outputs are not modified by the smoke test

## Reproduction

```bash
python -m py_compile research/prognostics/build_panel_day_engine_internal_share_appendix_v1.py research/prognostics/smoke_test_panel_day_engine_internal_share_appendix_v1.py
python research/prognostics/build_panel_day_engine_internal_share_appendix_v1.py
python research/prognostics/smoke_test_panel_day_engine_internal_share_appendix_v1.py
```

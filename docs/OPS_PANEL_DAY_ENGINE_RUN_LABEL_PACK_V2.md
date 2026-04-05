# OPS_PANEL_DAY_ENGINE_RUN_LABEL_PACK_V2

## 목적
- `run_label_pack_v1` 는 scorer v1 재료로는 유용했지만, 실제 학습 가능한 positive/negative 수가 너무 적었다.
- 이번 `v2` 는 이미 끝낸 taxonomy/onset/performance/common-cause audit 결과를 scorer-ready run label로 다시 압축하는 보강 단계다.
- detector 로직은 바꾸지 않고, 다음 `run_ranker_v2` holdout 전에 학습용 run label만 더 강하게 만든다.

## 입력
- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_label_pack_v1.csv`
- `_share/panel_day_engine_fault_taxonomy_eval_buckets_v2.csv`
- `_share/panel_day_engine_precursor_onset_truth_v1.csv`
- `_share/panel_day_engine_precursor_performance_cases_v1.csv`
- `_share/panel_day_engine_non_precursor_performance_cases_v1.csv`
- `_share/panel_day_engine_common_cause_descriptive_retrofit_cases_v1.csv`
- `_share/panel_day_engine_local_seed_carry_fate_cases_v1.csv`

## 출력
- `_share/panel_day_engine_run_label_pack_v2.csv`
- `_share/panel_day_engine_run_label_pack_summary_v2.csv`

## 핵심 변경
- `v1` 의 positive-like 는 유지한다.
  - `eligible_local`
  - `future_fault_linked`
  - `future_truth_linked`
- 여기에 step 4 비전조 bucket에서 "적시에 잡힌 abrupt fault" 를 positive-like 로 승격한다.
  - `final_fault_hit_by_anchor_flag == 1`
  - 또는 `final_fault_hit_within_3d_after_flag == 1`
- common-cause descriptive retrofit 에서 설명된 run 은 `common_cause_like` 로 따로 모은다.
  - 하지만 학습 label은 `exclude` 로 둔다.
  - 이유: panel-local positive/negative truth 가 아니라 routing/descriptive context 이기 때문이다.

## overlap 규칙
- case anchor 와 run segmentation 사이에 며칠 정도의 비동기 차이가 있어, abrupt/common-cause case 는 같은 `site/panel_id` 에 대해 `anchor_date ±5일` envelope 로 run overlap 을 잡는다.
- precursor onset/performance support 는 `preferred_precursor_onset_date ~ fault_start_date` 구간과 run 이 겹치는지로 본다.
- 이 support flag 는 provenance 용도이고, v2 label assignment 자체를 직접 바꾸지는 않는다.

## v2 label 규칙
- `positive_like`
  - `eligible_local`
  - `future_fault_linked`
  - `future_truth_linked`
  - `abrupt_hit_by_anchor`
  - `abrupt_hit_within_3d`
- `negative_like`
  - `nuisance_alert`
  - `isolated_unexplained`
- `monitor_like`
  - `recurring_monitor_like`
  - `recurring_chronic_monitor_like`
- `common_cause_like`
  - `non_panel_or_common_cause` 이고 descriptive retrofit `combined_marker_flag == 1`
- `unlabeled_other`
  - 위 조건 어디에도 안 걸리는 run

우선순위는 다음 순서다.
1. `positive_like`
2. `negative_like`
3. `monitor_like`
4. `common_cause_like`
5. `unlabeled_other`

## training label 매핑
- `positive_like -> positive`
- `negative_like -> negative`
- `monitor_like -> exclude`
- `common_cause_like -> exclude`
- `unlabeled_other -> exclude`

## confidence 해석
- `strong`
  - `eligible_local`
  - `future_fault_linked`
  - `future_truth_linked`
  - `abrupt_hit_by_anchor`
- `medium`
  - `abrupt_hit_within_3d`
  - `nuisance_alert`
  - `isolated_unexplained`
  - `recurring_monitor_like`
  - `common_cause_like`
- `weak`
  - `unlabeled_other`

## 왜 common-cause descriptive run 을 positive/negative 로 쓰지 않는가
- 이 run 들은 panel-local precursor/fault truth 라기보다 routing 설명력에 가까운 정보다.
- 그래서 scorer 학습에 바로 positive/negative 로 넣으면, local fault scorer 와 common-cause routing context 가 섞인다.
- 현재 단계에서는 `exclude` 로 보관하고 provenance 로만 남기는 것이 더 안전하다.

## 왜 지금이 run_ranker_v2 holdout 직전 단계인가
- taxonomy v2 로 precursor-bearing / abrupt / non-panel bucket 이 분리됐다.
- precursor onset truth 와 precursor marker 성능이 정리됐다.
- abrupt bucket 은 timing hit 여부로 positive-like 확장이 가능해졌다.
- common-cause bucket 은 descriptive retrofit 으로 scorer contamination 없이 제외 집합으로 보강할 수 있게 됐다.

즉, `run_label_pack_v2` 는 다음 `run_ranker_v2` holdout 에 들어갈 학습 집합을 넓히되, 아직 불안정한 bucket 은 `exclude` 로 남기는 가장 보수적인 중간판이다.

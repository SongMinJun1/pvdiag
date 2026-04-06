# OPS_PANEL_DAY_ENGINE_RUN_RANKER_REFERENCE_GAP_AUDIT_V1

## 목적

hybrid audit까지 해 봤는데도 current deterministic baseline을 안정적으로 넘지 못했다. 그래서 다음 method search를 더 늘리기 전에, 현재 best deterministic run score인 `electrical_core_minus_broadshape_050` 자체가 어디서 강하고 어디서 한계인지 먼저 해부한다.

## 왜 지금 이 audit이 필요한가

- hybrid가 실패하면 learned scorer만의 문제가 아니라 reference baseline 구조가 이미 얼마나 좋은지, 또 어떤 종류의 miss/false promotion을 남기는지부터 다시 봐야 한다.
- baseline의 miss가 본질적으로 약한 positive-like인지, broadshape penalty로 과하게 눌린 positive-like인지, 아니면 negative-like와 구조적으로 섞여 있는지에 따라 다음 액션이 달라진다.
- 그래서 current best score를 `top20 / top50 / below50` gap class로 쪼개서 strengths와 limits를 직접 본다.

## gap_class 해석

- `positive_top20_global`
  - strong positive-like run을 reference가 상위 retrieval에서 잘 잡는 구간
- `positive_top50_global_not_top20`
  - positive-like near-miss 구간
  - rerank나 penalty tuning 여지가 있는지 보기 좋은 구간
- `positive_below_top50_global`
  - current reference가 본격적으로 놓치는 positive-like 구간
- `negative_top20_global`
  - false promotion risk가 가장 큰 negative-like 구간
- `negative_top50_global_not_top20`
  - 경계성 false promotion 구간
- `negative_below_top50_global`
  - reference가 negative-like run을 비교적 안전하게 누르는 구간

## recommended_next_direction 의미

- `keep_reference_as_best_current`
  - missed positive가 전반적으로 약하고 distinct pattern도 적어 current reference를 best current로 유지
- `tune_broadshape_penalty_only`
  - missed positive가 fault-like signal은 있는데 broadshape-heavy 패턴 때문에 눌린 것으로 보여 penalty만 미세조정할 가치가 있음
- `expand_positive_labels_before_more_modeling`
  - missed positive가 sparse하거나 heterogeneous해서 method search보다 positive label expansion이 더 우선
- `stop_scorer_search_for_now`
  - negative top20과 positive top20이 너무 비슷해서 clean separator가 거의 없고, scorer search 이득이 제한적

## 입력

- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_label_pack_v2.csv`
- `_share/panel_day_engine_run_ranker_v0_scores.csv`

## 출력

- `_share/panel_day_engine_run_ranker_reference_gap_cases_v1.csv`
- `_share/panel_day_engine_run_ranker_reference_gap_summary_v1.csv`

## 방법

1. full run universe에서 `electrical_core_minus_broadshape_050` global/site rank를 계산한다.
2. 그중 `label_bucket_v2 in {positive_like, negative_like}` 인 labeled rows만 case universe로 잡는다.
3. labeled run을 global rank 기준으로:
   - top20
   - top21-50
   - below50
   로 나누고 positive/negative를 각각 따로 본다.
4. gap class별 median feature profile을 요약해 baseline strength/miss/false-promotion 구조를 읽는다.

## 재현

```bash
python -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_run_ranker_reference_gap_audit_v1.py \
  research/prognostics/smoke_test_panel_day_engine_run_ranker_reference_gap_audit_v1.py

python research/prognostics/build_panel_day_engine_run_ranker_reference_gap_audit_v1.py
python research/prognostics/smoke_test_panel_day_engine_run_ranker_reference_gap_audit_v1.py
```

# OPS_PANEL_DAY_ENGINE_RUN_RANKER_HYBRID_AUDIT_V1

## 목적

`site_conditioned_scaling` 단독 실험만으로는 deterministic reference를 안정적으로 넘지 못했다. 그래서 이번 patch는 detector logic을 바꾸지 않고, `electrical_core_minus_broadshape_050` 의 강한 retrieval을 바깥 shortlist gate로 유지한 채 shortlist 내부 순서만 learned score로 조정하는 hybrid ranking을 점검한다.

## 왜 hybrid가 다음 단계인가

- deterministic reference는 electrical severity가 강한 positive-like run을 안정적으로 끌어오는 장점이 있다.
- learned scorer는 top-level retrieval 자체보다는 shortlist 내부 순서 조정에서 더 도움이 될 수 있다.
- 그래서 learned score를 전체 순위에 바로 맡기기보다, deterministic outer shortlist를 고정하고 안쪽 ordering에만 쓰는 것이 더 보수적이고 운영적으로 해석 가능하다.

## 비교 방법

- `reference_only`
  - `electrical_core_minus_broadshape_050` 단독 순위
- `hybrid_ref50_global`
  - reference 상위 50개 shortlist 유지
  - shortlist 내부만 global logistic learned score로 재정렬
- `hybrid_ref100_global`
  - reference 상위 100개 shortlist 유지
  - shortlist 내부만 global logistic learned score로 재정렬
- `hybrid_ref50_site`
  - reference 상위 50개 shortlist 유지
  - shortlist 내부만 exploratory site-conditioned logistic learned score로 재정렬
- `hybrid_ref100_site`
  - reference 상위 100개 shortlist 유지
  - shortlist 내부만 exploratory site-conditioned logistic learned score로 재정렬

## shortlist 50 vs 100 해석

- `50` 은 더 보수적인 rerank다.
  - deterministic retrieval을 더 강하게 유지한다.
  - learned score contamination이 작아야 할 때 적합하다.
- `100` 은 더 넓은 rerank다.
  - learned score가 positive-like를 더 많이 구조할 여지는 있다.
  - 대신 negative-like over-promotion 위험도 같이 본다.

## 중요한 해석 주의점

- deterministic reference는 shortlist 바깥 retrieval gate로 유지된다.
- `site` variant는 prior audit와 마찬가지로 site distribution을 이용한 exploratory method search 성격이다.
- 따라서 본 audit은 final unbiased claim이 아니라 "hybrid 구조가 learned scorer를 더 안전하게 쓸 수 있는가"를 보는 중간 판단용이다.

## 입력

- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_label_pack_v2.csv`
- `_share/panel_day_engine_run_label_promotion_scenarios_v1.csv`
- `_share/panel_day_engine_run_ranker_v0_scores.csv`
- `_share/panel_day_engine_run_ranker_site_conditioned_scaling_summary_v1.csv`

## 출력

- `_share/panel_day_engine_run_ranker_hybrid_summary_v1.csv`
- `_share/panel_day_engine_run_ranker_hybrid_topk_yield_v1.csv`
- `_share/panel_day_engine_run_ranker_hybrid_cases_v1.csv`

## 무엇을 보면 되는가

- summary:
  - reference 대비 hybrid가 `top10/top20 positive-minus-negative` 를 개선했는지
  - global logistic baseline 대비 hybrid가 더 안정적인지
- topk_yield:
  - fold별로 positive-like / negative-like 가 top10, top20 안에 얼마나 들어오는지
- cases:
  - `positive_captured_by_hybrid_not_reference`
  - `positive_captured_by_reference_not_hybrid`
  - `negative_promoted_by_hybrid_not_reference`
  를 통해 hybrid가 어떤 종류의 reorder를 만들었는지 확인한다.

## 언제 `run_ranker_v3_hybrid` 로 갈 수 있나

- reference-only 대비 top20 positive-minus-negative 가 일관되게 같거나 좋아진다.
- 동시에 negative promotion이 제한적이다.
- case audit에서 hybrid가 deterministic이 놓치지 않던 strong positives를 크게 해치지 않으면서 추가 positive-like를 구조한다.

## 언제 learned scorer를 더 밀지 말아야 하나

- hybrid도 reference-only 를 못 넘는다.
- shortlist를 넓힐수록 negative-like promotion만 늘어난다.
- positive gain이 거의 없고 disagreement가 노이즈성 reorder에 가깝다.

## 재현

```bash
python -m py_compile pv_ae/panel_day_engine.py \
  research/prognostics/build_panel_day_engine_run_ranker_hybrid_audit_v1.py \
  research/prognostics/smoke_test_panel_day_engine_run_ranker_hybrid_audit_v1.py

python research/prognostics/build_panel_day_engine_run_ranker_hybrid_audit_v1.py
python research/prognostics/smoke_test_panel_day_engine_run_ranker_hybrid_audit_v1.py
```

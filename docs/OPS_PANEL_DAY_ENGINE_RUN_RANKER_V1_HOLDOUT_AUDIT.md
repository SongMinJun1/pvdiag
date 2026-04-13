# OPS_PANEL_DAY_ENGINE_RUN_RANKER_V1_HOLDOUT_AUDIT

## 목적
- `run_ranker_v1` prototype의 optimistic full-fit 결과만으로는 scorer path가 실제로 유효한지 판단하기 어렵다.
- 그래서 같은 online-safe run feature만 사용해 `logistic_v1` 을 fold별로 다시 학습하고, holdout에서 `electrical_core_score` 와 `electrical_core_minus_broadshape_050` 를 직접 비교한다.

## 왜 optimistic full-fit만으로는 부족한가
- full-fit prototype은 train과 eval이 같은 run universe를 공유하므로 optimistic bias가 있다.
- 특히 local precursor run 수가 작고 label도 weak label이기 때문에, full-fit에서 보인 top-k 개선이 실제 일반화 신호인지 확인하는 별도 단계가 필요하다.

## 왜 site / time holdout인가
- `leave-one-site-out` 은 site-specific pattern에 과적합했는지 보는 가장 직접적인 점검이다.
- `time_holdout_70_30` 은 later runs로 넘어갈 때 ranking signal이 유지되는지 보는 최소 temporal sanity check다.
- 둘 다 통과하지 못하면 production-minded scorer로 갈 근거가 약하다.

## feature 제약
- holdout logistic은 v1 prototype과 같은 online-safe feature만 사용한다.
- `future_fault_linked_flag`, `future_truth_linked_flag`, `recurring_run_within_60d`, `fate_class`, `cohort_hint` 같은 post-run / label-adjacent 정보는 입력에서 제외한다.
- 따라서 holdout 결과는 detector online path에 옮길 수 있는 정보만으로 계산된 비교다.

## 비교 대상
- learned:
  - `logistic_v1_holdout`
- v0 reference:
  - `electrical_core_score`
  - `electrical_core_minus_broadshape_050`

`hgb_v1` 는 이번 holdout audit에서 제외한다. 목적이 "prototype logistic path가 v0를 실제로 넘는가"를 확인하는 것이기 때문이다.

## 출력물
- `_share/panel_day_engine_run_ranker_v1_holdout_fold_scores.csv`
  - fold x score 단위 상세 지표
- `_share/panel_day_engine_run_ranker_v1_holdout_summary.csv`
  - fold family별 평균 비교 요약
- `_share/panel_day_engine_run_ranker_v1_holdout_topk_yield.csv`
  - fold x score x K (`10`, `20`) top-k yield 행

## 해석 포인트
- `labeled_test_auc`, `labeled_test_average_precision`
  - labeled holdout subset에서 positive/negative 분리도가 유지되는지 본다.
- `top10_positive_minus_negative`, `top20_positive_minus_negative`
  - 실제 shortlist에서 positive-like를 negative-like보다 더 많이 끌어올리는지가 핵심이다.
- skip fold
  - train labeled set에 positive/negative 둘 다 없으면 fold를 skip한다.
  - 이런 skip 자체도 현재 weak-label coverage 한계의 일부다.

## 어떤 결과가 다음 단계로 이어지는가
- A) production-minded `run_ranker_v1` 로 갈 근거
  - `logistic_v1_holdout` 이 site/time holdout 모두에서 best v0 reference보다 `mean_top20_positive_minus_negative` 와 top-k positive counts가 일관되게 높을 때
  - 그리고 labeled holdout AUC/AP도 reference ranking보다 열세가 아닐 때
- B) scorer method search 중단 + operator-facing consolidation 전환
  - holdout에서 logistic이 v0 reference를 안정적으로 못 넘고
  - fold별 top-k가 여전히 `negative_like` 혹은 `unlabeled_other` 위주로 채워질 때
  - 이 경우 detector-side scorer 개선보다 run consolidation / operator triage가 더 현실적인 경로다

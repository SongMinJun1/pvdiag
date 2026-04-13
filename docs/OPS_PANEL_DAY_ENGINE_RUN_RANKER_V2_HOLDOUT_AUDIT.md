# OPS_PANEL_DAY_ENGINE_RUN_RANKER_V2_HOLDOUT_AUDIT

## 목적
- `run_label_pack_v2` 가 단순히 positive 수를 조금 늘린 것이 아니라, holdout ranking 품질도 실제로 개선하는지 확인한다.
- detector 로직은 바꾸지 않고, 기존 online-safe run feature만 사용해 `logistic_v2_holdout` 을 다시 학습한다.
- 비교 대상은 다음 3개로 제한한다.
  - `logistic_v2_holdout`
  - `electrical_core_score`
  - `electrical_core_minus_broadshape_050`

## 왜 지금 holdout을 다시 봐야 하는가
- `v1` label pack은 scarcity가 심해서 scorer가 holdout에서 v0 reference를 안정적으로 넘지 못했다.
- `v2` 는 label 수보다도 label quality를 바꿨다.
  - precursor-bearing positive는 유지
  - timely abrupt hit를 positive-like로 추가
  - common-cause descriptive는 positive/negative 대신 exclude로 분리
- 따라서 다음 체크는 “같은 safe feature로 다시 학습했을 때 ranking이 실제로 나아지는가”이다.

## 학습 / 평가 규칙
- 학습 label:
  - `training_label_v2 == positive` -> positive class
  - `training_label_v2 == negative` -> negative class
  - 나머지 -> train exclude
- 평가 grouping:
  - `positive_like`
  - `negative_like`
  - `monitor_like`
  - `common_cause_like`
  - `unlabeled_other`
- labeled AUC / AP는 `positive_like` vs `negative_like` subset 에서만 계산한다.

## feature 제약
- `run_ranker_v1` holdout 과 같은 online-safe feature만 사용한다.
- 다음은 사용하지 않는다.
  - future / post-run outcome
  - `fate_class`
  - `cohort_hint`
  - `label_bucket_v2`
  - `training_label_v2`
  - `recurring_run_within_60d`

즉, 이번 audit은 label truth만 바뀌고 feature channel은 그대로인 상태를 본다.

## fold
- `leave_one_site_out`
- `time_holdout_70_30`

각 fold에서:
- train은 labeled rows only
- test는 해당 fold의 전체 run universe
- train label에 positive/negative 둘 다 없으면 fold skip

## 핵심 산출물
- `panel_day_engine_run_ranker_v2_holdout_fold_scores.csv`
  - fold별 AUC/AP와 top-10 / top-20 yield
- `panel_day_engine_run_ranker_v2_holdout_summary.csv`
  - score별 fold-type 평균 성능
  - `v1` holdout summary 대비 top-k delta
- `panel_day_engine_run_ranker_v2_holdout_topk_yield.csv`
  - fold x score x K 상세 yield

## 해석 기준
### 앞으로 v2 scorer를 진행할 근거
- `logistic_v2_holdout` 이 `logistic_v1_holdout` 대비 top-k delta가 양수이고
- 동시에 comparable v0 reference 대비 top-k positive-minus-negative가 일관되게 밀리지 않을 때
- labeled AUC/AP도 fold별로 붕괴하지 않을 때

### scorer를 잠시 접고 label expansion audit으로 돌아갈 근거
- `v2` 라벨을 넣어도 `logistic_v2_holdout` 이 `v1` 보다 나아지지 않거나
- v0 reference보다 top-k yield가 계속 불안정하게 밀리고
- fold skip가 여전히 많아 labeled train universe가 너무 작을 때

그 경우 다음 단계는 model tweak보다 label expansion 쪽이 더 맞다.

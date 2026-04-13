# OPS_PANEL_DAY_ENGINE_RUN_RANKER_V1_PROTOTYPE_AUDIT

## 목적
- detector gate tweaking은 일단 멈추고, existing run feature만으로 learned scorer가 hand-built v0보다 나아질 여지가 있는지 본다.
- 이 단계는 production claim이 아니라 optimistic prototype audit이다.

## 왜 learned run-level scoring인가
- day-level gate 조정은 이미 여러 번 시도됐고, gain보다 burden tradeoff가 더 뚜렷해졌다.
- run 단위에서는 단일 hand-built score 하나보다 feature 조합 자체를 학습시키는 편이 더 나은 ordering을 만들 가능성이 있다.
- 그래서 다음 method search path는 gate 변경이 아니라 run-level scorer prototype이다.

## 입력
- `_share/panel_day_engine_run_feature_table_v1.csv`
- `_share/panel_day_engine_run_ranker_v0_scores.csv`
- `_share/panel_day_engine_run_ranker_v0_topk_yield_summary.csv`

## 학습 라벨
- `positive_like`: `eligible_local`, `future_fault_linked`
- `negative_like`: `nuisance_alert`, `isolated_unexplained`
- `monitor_like`: `recurring_monitor_like`
- `unlabeled_other`: `unmatched_other`

학습에는 `positive_like` 와 `negative_like` 만 사용한다. `monitor_like` 와 `unlabeled_other` 는 score evaluation 대상이지만 supervised label로 쓰지 않는다.

## online-safe feature만 사용
future outcome, recurrence, fate, cohort 같은 post-run 정보는 feature에 넣지 않는다.

금지:
- `future_fault_linked_flag`
- `future_truth_linked_flag`
- `recurring_run_within_60d`
- `fate_class`
- `cohort_hint`
- 그 외 post-run future info

## prototype model
### logistic_v1
- median/IQR robust scaling
- logistic regression
- full-fit prototype scoring

### hgb_v1
- `HistGradientBoostingClassifier`
- same online-safe feature set
- full-fit prototype scoring

## 왜 optimistic audit인가
- 같은 데이터에서 label을 만들고 같은 데이터에 fit한 뒤 다시 그 전체 run universe를 scoring한다.
- cross-validation도 없고 future split도 없다.
- 따라서 이 결과는 “가능성 스크리닝” 이지 일반화 성능 주장으로 쓰면 안 된다.

## v0 reference 포함 이유
- learned score가 정말 의미가 있으려면 최소한 `electrical_core_score` 와 `electrical_core_minus_broadshape_050` 보다 top-k yield가 나아져야 한다.
- 그래서 v1 output에는 v0 reference score도 같이 실어서 같은 run universe 위에서 직접 비교한다.

## production-minded run_ranker_v1로 넘어갈 조건
- `logistic_v1_score` 또는 `hgb_v1_score` 가 top-20 / top-50 에서 v0 reference보다 높은 `positive_minus_negative` 를 반복적으로 보인다.
- top-k에서 `positive_like` 농축이 좋아지면서 `negative_like` 는 같이 늘지 않는다.
- learned model이 단순히 `unlabeled_other` 만 위로 끌어올리는 게 아니라 labeled positive 쪽을 실제로 더 잘 retrieval한다.

이 조건이 안 나오면 detector-side method search를 더 키우기보다 operator-facing consolidation 쪽으로 무게를 옮기는 게 낫다.
